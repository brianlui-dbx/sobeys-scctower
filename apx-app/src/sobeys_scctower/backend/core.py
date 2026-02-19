"""
Core application infrastructure: config, logging, utilities, dependencies, and bootstrap.
Adapted for SQL warehouse queries (no Lakebase database).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib import resources
from pathlib import Path
from typing import Annotated, Any, ClassVar, TypeAlias

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.staticfiles import NotModifiedResponse, StaticFiles
from starlette.types import Scope

from .._metadata import api_prefix, app_name, app_slug, dist_dir

# --- Config ---

project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)
    catalog: str = Field(default="snowflake_retail_consumer_goods")
    schema_name: str = Field(default="supply_chain_control_tower", validation_alias="SOBEYS_SCCTOWER_SCHEMA")
    warehouse_id: str = Field(default="b9771bcf4a3a5399")
    chat_endpoint: str = Field(default="https://adb-7405613286317055.15.azuredatabricks.net/serving-endpoints")
    chat_model: str = Field(default="mas-5fba20e2-endpoint")
    general_model: str = Field(default="databricks-gpt-5-1")

    @property
    def full_schema(self) -> str:
        return f"{self.catalog}.{self.schema_name}"

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")

    def __hash__(self) -> int:
        return hash(self.app_name)


# --- Logger ---

logger = logging.getLogger(app_name)


# --- Static Files ---


class CachedStaticFiles(StaticFiles):
    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        request_headers = Headers(scope=scope)
        response = FileResponse(
            full_path, status_code=status_code, stat_result=stat_result
        )
        if "/assets/" in str(full_path):
            response.headers["cache-control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["cache-control"] = "no-cache"
        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response


# --- Utils ---


def _add_not_found_handler(app: FastAPI) -> None:
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            path = request.url.path
            accept = request.headers.get("accept", "")
            is_api = path.startswith(api_prefix)
            is_get_page_nav = request.method == "GET" and "text/html" in accept
            looks_like_asset = "." in path.split("/")[-1]
            if (not is_api) and is_get_page_nav and (not looks_like_asset):
                return FileResponse(dist_dir / "index.html")
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    app.exception_handler(StarletteHTTPException)(http_exception_handler)


# --- SQL Helper with TTL Cache ---

import time

_sql_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
SQL_CACHE_TTL = 300  # 5 minutes — data is snapshot-based


def execute_sql(ws: WorkspaceClient, config: AppConfig, query: str, ttl: int = SQL_CACHE_TTL) -> list[dict[str, Any]]:
    """Execute a SQL query with in-memory TTL caching."""
    from databricks.sdk.service.sql import StatementState

    cache_key = query.strip()
    now = time.time()

    # Return cached result if fresh
    if cache_key in _sql_cache:
        cached_at, cached_rows = _sql_cache[cache_key]
        if now - cached_at < ttl:
            logger.info(f"SQL cache hit ({len(cached_rows)} rows, {int(now - cached_at)}s old)")
            return cached_rows

    short_query = query.strip().replace("\n", " ")[:80]
    logger.info(f"SQL: {short_query}...")

    response = ws.statement_execution.execute_statement(
        warehouse_id=config.warehouse_id,
        statement=query,
        wait_timeout="30s",
    )

    state = response.status.state if response.status else "UNKNOWN"
    if state != StatementState.SUCCEEDED:
        error_msg = response.status.error.message if response.status and response.status.error else "unknown"
        logger.error(f"SQL failed ({state}): {error_msg}")
        return []

    if response.manifest and response.result and response.result.data_array:
        columns = [col.name for col in response.manifest.schema.columns]  # type: ignore
        rows = [dict(zip(columns, row)) for row in response.result.data_array]
        logger.info(f"SQL returned {len(rows)} rows")
        _sql_cache[cache_key] = (now, rows)
        return rows

    logger.info("SQL returned 0 rows")
    _sql_cache[cache_key] = (now, [])
    return []


# --- Lifespan ---


@asynccontextmanager
async def _default_lifespan(app: FastAPI):
    config = AppConfig()
    logger.info(f"Starting app: {config.app_name}")
    logger.info(f"  Catalog: {config.catalog}")
    logger.info(f"  Schema: {config.schema_name}")
    logger.info(f"  Warehouse: {config.warehouse_id}")
    logger.info(f"  Chat model: {config.chat_model}")

    ws = WorkspaceClient()
    app.state.config = config
    app.state.workspace_client = ws
    yield


# --- Factory ---


def create_app(
    *,
    routers: list[APIRouter] | None = None,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def _composed_lifespan(app: FastAPI):
        async with _default_lifespan(app):
            if lifespan:
                async with lifespan(app):
                    yield
            else:
                yield

    app = FastAPI(title=app_name, lifespan=_composed_lifespan)

    for router in routers or []:
        app.include_router(router)

    app.mount("/", CachedStaticFiles(directory=dist_dir, html=True))
    _add_not_found_handler(app)

    return app


def create_router() -> APIRouter:
    return APIRouter(prefix=api_prefix)


# --- Dependencies ---


def get_config(request: Request) -> AppConfig:
    if not hasattr(request.app.state, "config"):
        raise RuntimeError("AppConfig not initialized.")
    return request.app.state.config


def get_ws(request: Request) -> WorkspaceClient:
    if not hasattr(request.app.state, "workspace_client"):
        raise RuntimeError("WorkspaceClient not initialized.")
    return request.app.state.workspace_client


def get_user_ws(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> WorkspaceClient:
    if not token:
        raise ValueError("OBO token not provided")
    return WorkspaceClient(token=token, auth_type="pat")


def get_user_token(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> str:
    """Return the raw OBO token string for use with external SDKs (e.g. OpenAI)."""
    if not token:
        raise ValueError("OBO token not provided in X-Forwarded-Access-Token header")
    return token


class Dependency:
    Client: TypeAlias = Annotated[WorkspaceClient, Depends(get_ws)]
    UserClient: TypeAlias = Annotated[WorkspaceClient, Depends(get_user_ws)]
    UserToken: TypeAlias = Annotated[str, Depends(get_user_token)]
    Config: TypeAlias = Annotated[AppConfig, Depends(get_config)]
