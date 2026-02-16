# Supply Chain Control Tower - Databricks Deployment Package

## File Size Verification

All files are under the 10MB Databricks file size limit:
- Largest file: `frontend/canvaskit/canvaskit.wasm` (6.7MB) ✅
- Backend: `backend/main.py` (<1MB) ✅

## Deployment Structure

```
deployment/
├── backend/              # FastAPI backend
│   ├── main.py          # Main FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── .env            # Environment variables (configure before deployment)
└── frontend/            # Flutter web build
    ├── index.html       # Main HTML file
    ├── main.dart.js     # Compiled Dart/Flutter code (2.7MB)
    ├── flutter.js       # Flutter framework
    ├── assets/          # App assets and fonts
    ├── canvaskit/       # Flutter rendering engine
    └── icons/           # App icons
```

## Databricks Deployment Steps

### 1. Upload Backend to Databricks

```python
# In Databricks notebook
import os

# Create directory for backend
dbutils.fs.mkdirs("/FileStore/supply_chain_tracker/backend")

# Upload main.py and requirements.txt
# (Use Databricks UI or dbutils.fs.cp to upload files)
```

### 2. Install Dependencies

```python
# In Databricks notebook
%pip install -r /dbfs/FileStore/supply_chain_tracker/backend/requirements.txt
```

### 3. Configure Environment Variables

Update the `.env` file or set environment variables in Databricks:
```
DATABRICKS_SERVER_HOSTNAME=<your-workspace>.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>
DATABRICKS_ACCESS_TOKEN=<your-token>
DATABRICKS_CATALOG=<catalog-name>
DATABRICKS_SCHEMA=<schema-name>
OSRM_BASE_URL=http://router.project-osrm.org
```

### 4. Upload Frontend to Databricks

```python
# Upload entire frontend directory
dbutils.fs.mkdirs("/FileStore/supply_chain_tracker/frontend")

# Upload all files from frontend/ directory
# (Use Databricks UI to upload the entire folder)
```

### 5. Start the Application

```python
# In Databricks notebook
import sys
sys.path.append('/dbfs/FileStore/supply_chain_tracker/backend')

import subprocess
import os

os.chdir('/dbfs/FileStore/supply_chain_tracker/backend')
subprocess.Popen(['uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'])
```

### 6. Access the Application

The application will be available at:
- API: `https://<databricks-workspace>/driver-proxy/o/0/<cluster-id>/8000/api/`
- Frontend: `https://<databricks-workspace>/driver-proxy/o/0/<cluster-id>/8000/`

## Features

### Real-time Inventory Screen
- **Interactive map** with tooltips showing shipment quantities
- **Filter by product** - Individual chips for all products
- **Filter by status** - Filter by In Transit, At DC, At Dock, Delivered
- **Dynamic summary cards** - Update based on selected filters
- **Maximize map** - Full-screen map view

### Batch Tracking Screen
- **Batch selection** - Select by product and batch ID
- **Route visualization** - OSRM-powered routing with detailed status colors
- **Animation** - Track shipment journey with "Track History" button
- **Event timeline** - View all batch events chronologically
- **Maximize map** - Full-screen tracking view

## API Endpoints

- `GET /api/inventory` - Get inventory data with optional filters
- `GET /api/inventory/summary` - Get status summary counts
- `GET /api/products` - Get list of unique products (cached)
- `GET /api/statuses` - Get list of status categories
- `GET /api/batches` - Get list of batches
- `GET /api/batch/{batch_id}` - Get events for specific batch
- `GET /api/route` - Get OSRM route between two coordinates

## Technology Stack

### Frontend
- **Flutter Web** (compiled to JavaScript)
- **shadcn_ui** for consistent UI components
- **flutter_map** for interactive maps
- **OpenStreetMap** tiles

### Backend
- **FastAPI** for REST API
- **Databricks SQL Connector** for data access
- **Pandas** for data processing
- **OSRM** for route calculations
- **In-memory caching** for performance

## Notes

- All assets are optimized and under the 10MB file size limit
- The backend serves both API endpoints and static frontend files
- CORS is configured for development (update for production)
- Cache TTL is set to 60 seconds for inventory data
- Products and statuses are cached for 5 minutes
