from pydantic import BaseModel
from typing import Optional
from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- KPI / Dashboard ---

class KpiCardOut(BaseModel):
    id: str
    label: str
    value: float
    unit: str = ""
    prefix: str = ""
    change: float = 0
    change_unit: str = "%"


class ChartDataPointOut(BaseModel):
    month: str
    value: float


class SupplierRiskOut(BaseModel):
    label: str
    value: str
    change: float
    change_unit: str


class DemandForecastingSectionOut(BaseModel):
    title: str
    accuracy_label: str
    accuracy_value: float
    unit: str
    period: str
    chart_data: list[ChartDataPointOut]


class InventoryLocationOut(BaseModel):
    name: str
    value: float


class InventoryLevelsOut(BaseModel):
    title: str
    subtitle: str
    total_value: float
    unit: str
    prefix: str
    period: str
    locations: list[InventoryLocationOut]


class SupplierPerformanceOut(BaseModel):
    name: str
    on_time_delivery: float
    quality_score: float
    lead_time: str
    risk_score: str


class SupplierPerformanceSectionOut(BaseModel):
    title: str
    columns: list[str]
    suppliers: list[SupplierPerformanceOut]


class RiskFactorOut(BaseModel):
    factor: str
    severity: str


class RiskAssessmentOut(BaseModel):
    title: str
    factors: list[RiskFactorOut]


class ContributingFactorOut(BaseModel):
    name: str
    value: float


class DisruptionTypeOut(BaseModel):
    type: str
    probability: float


class PredictiveRiskOut(BaseModel):
    title: str
    disruption_label: str
    disruption_level: str
    period: str
    contributing_factors: list[ContributingFactorOut]
    disruption_types: list[DisruptionTypeOut]


class LogisticsMetricOut(BaseModel):
    label: str
    value: float
    unit: str
    period: str
    chart_data: list[ChartDataPointOut]


class LogisticsTransportationOut(BaseModel):
    title: str
    expedited_delayed: LogisticsMetricOut
    otif_over_time: LogisticsMetricOut


class ExecutiveDashboardOut(BaseModel):
    title: str
    subtitle: str
    kpi_cards: list[KpiCardOut]
    supplier_risk: SupplierRiskOut
    demand_forecasting: DemandForecastingSectionOut
    inventory_levels: InventoryLevelsOut
    supplier_performance: SupplierPerformanceSectionOut
    risk_assessment: RiskAssessmentOut
    predictive_risk_analysis: PredictiveRiskOut
    logistics_transportation: LogisticsTransportationOut


# --- DC Inventory ---

class DcInventoryOut(BaseModel):
    product_id: str
    product_name: str
    dc_id: str
    dc_name: str
    allocated_qty: int
    safety_stock: int
    excess_qty: int
    total_qty: int
    snapshot_date: str


# --- Incoming Supply ---

class IncomingSupplyOut(BaseModel):
    shipment_id: str
    source_location: str
    product_name: str
    destination_dc: str
    qty: int
    expected_arrival_days: int
    expected_arrival_date: str


# --- Shipping Schedule ---

class ShippingScheduleOut(BaseModel):
    schedule_id: str
    product_name: str
    dc_name: str
    customer_name: str
    schedule_date: str
    qty: int


# --- Supplier Orders ---

class SupplierOrderOut(BaseModel):
    order_id: str
    supplier_name: str
    product_name: str
    qty: int
    expected_arrival_days: int
    expected_arrival_date: str


# --- Stockout Risk ---

class StockoutRiskOut(BaseModel):
    product_name: str
    dc_name: str
    current_qty: int
    safety_stock: int
    days_of_supply: float
    risk_level: str


# --- Storage Location ---

class StorageLocationOut(BaseModel):
    location_id: str
    location_name: str
    type: str
    location: str
    latitude: float
    longitude: float


# --- Customer Location ---

class CustomerLocationOut(BaseModel):
    customer_id: str
    name: str
    location: str
    latitude: float
    longitude: float


# --- Chat ---

class ChatMessageIn(BaseModel):
    role: str
    content: str


class ChatRequestIn(BaseModel):
    messages: list[ChatMessageIn]


class ChatResponseOut(BaseModel):
    response: str
    model: str


class ChatTaskOut(BaseModel):
    task_id: str
    status: str  # "pending", "running", "done", "error"
    response: str = ""
