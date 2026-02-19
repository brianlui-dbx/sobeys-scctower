"""
Demand Forecasting Model Training Script
=========================================
Trains a demand forecasting model using historical shipping schedule data,
registers it as a custom MLflow pyfunc model in Unity Catalog.

Input signature: customer_name (str), product_name (str), date (str), weather_forecast (str)
Output: predicted_demand (int) - number of units
"""

import mlflow
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
UC_MODEL_NAME = "retail_consumer_goods.supply_chain_control_tower.demand_forecast_model"
EXPERIMENT_NAME = "/Users/brian.lui@databricks.com/demand_forecast_experiment"

# ---------------------------------------------------------------------------
# 1. Load training data from Snowflake federated tables
# ---------------------------------------------------------------------------
print("Loading training data...")
training_df = spark.sql("""
    SELECT *
    FROM retail_consumer_goods.supply_chain_control_tower.demand_training_data
""").toPandas()

print(f"Loaded {len(training_df)} training records")
print(f"Products: {training_df['PRODUCT_NAME'].nunique()}")
print(f"Customers: {training_df['CUSTOMER_NAME'].nunique()}")

# ---------------------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------------------
print("Engineering features...")

customer_encoder = LabelEncoder()
product_encoder = LabelEncoder()
dc_encoder = LabelEncoder()

training_df["customer_enc"] = customer_encoder.fit_transform(training_df["CUSTOMER_NAME"])
training_df["product_enc"] = product_encoder.fit_transform(training_df["PRODUCT_NAME"])
training_df["dc_enc"] = dc_encoder.fit_transform(training_df["DC_ID"])

feature_cols = ["customer_enc", "product_enc", "dc_enc",
                "DAY_OF_WEEK", "MONTH", "DAY_OF_MONTH", "COST_PER_UNIT"]

X = training_df[feature_cols].values
y = training_df["DEMAND"].values

# ---------------------------------------------------------------------------
# 3. Train model
# ---------------------------------------------------------------------------
print("Training GradientBoosting model...")

model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    random_state=42,
)
model.fit(X, y)

train_preds = model.predict(X)
mae = np.mean(np.abs(y - train_preds))
rmse = np.sqrt(np.mean((y - train_preds) ** 2))
print(f"Training MAE: {mae:.1f}  |  RMSE: {rmse:.1f}")

# ---------------------------------------------------------------------------
# 4. Build lookup tables needed at inference time
# ---------------------------------------------------------------------------
customer_names_list = list(customer_encoder.classes_)
product_names_list  = list(product_encoder.classes_)
dc_ids_list         = list(dc_encoder.classes_)

# Map customer -> typical DC (mode)
customer_dc_map = (
    training_df.groupby("CUSTOMER_NAME")["DC_ID"]
    .agg(lambda x: x.mode().iloc[0])
    .to_dict()
)

# Map product -> cost_per_unit
product_cost_map = (
    training_df.groupby("PRODUCT_NAME")["COST_PER_UNIT"]
    .first()
    .to_dict()
)

# ---------------------------------------------------------------------------
# 5. Define custom pyfunc model
# ---------------------------------------------------------------------------

class DemandForecastModel(mlflow.pyfunc.PythonModel):
    """
    Custom MLflow pyfunc that accepts human-readable inputs
    (customer_name, product_name, date, weather_forecast)
    and returns predicted demand in units.
    """

    def __init__(self, sklearn_model, customer_encoder, product_encoder,
                 dc_encoder, customer_names, product_names, dc_ids,
                 customer_dc_map, product_cost_map):
        self.sklearn_model = sklearn_model
        self.customer_encoder = customer_encoder
        self.product_encoder = product_encoder
        self.dc_encoder = dc_encoder
        self.customer_names = customer_names
        self.product_names = product_names
        self.dc_ids = dc_ids
        self.customer_dc_map = customer_dc_map
        self.product_cost_map = product_cost_map

    def _weather_multiplier(self, weather_text: str) -> float:
        """Apply a demand multiplier based on weather forecast text."""
        w = weather_text.lower()
        if any(k in w for k in ("blizzard", "hurricane", "tornado")):
            return 0.55
        if any(k in w for k in ("snow", "ice", "sleet")):
            return 0.70
        if any(k in w for k in ("storm", "thunderstorm", "heavy rain")):
            return 0.80
        if any(k in w for k in ("rain", "drizzle", "shower")):
            return 0.90
        if any(k in w for k in ("cold", "freeze", "frost", "freezing")):
            return 0.85
        if any(k in w for k in ("hot", "heat", "heatwave", "heat wave")):
            return 1.15
        if any(k in w for k in ("sunny", "clear", "fair", "warm")):
            return 1.10
        if any(k in w for k in ("cloudy", "overcast", "fog")):
            return 0.97
        return 1.0   # neutral / unknown

    def predict(self, context, model_input, params=None):
        results = []
        for _, row in model_input.iterrows():
            customer_name = str(row.get("customer_name", ""))
            product_name  = str(row.get("product_name", ""))
            date_str      = str(row.get("date", ""))
            weather       = str(row.get("weather_forecast", "clear"))

            # Parse date
            try:
                dt = pd.to_datetime(date_str)
            except Exception:
                dt = pd.Timestamp.now()

            day_of_week  = dt.dayofweek + 1   # Spark DAYOFWEEK is 1-7
            month        = dt.month
            day_of_month = dt.day

            # Encode customer
            if customer_name in self.customer_names:
                cust_enc = int(self.customer_encoder.transform([customer_name])[0])
            else:
                cust_enc = 0

            # Encode product
            if product_name in self.product_names:
                prod_enc = int(self.product_encoder.transform([product_name])[0])
            else:
                prod_enc = 0

            # Determine DC for customer
            dc_id = self.customer_dc_map.get(customer_name, self.dc_ids[0])
            if dc_id in self.dc_ids:
                dc_enc = int(self.dc_encoder.transform([dc_id])[0])
            else:
                dc_enc = 0

            cost_per_unit = self.product_cost_map.get(product_name, 3.0)

            features = np.array([[cust_enc, prod_enc, dc_enc,
                                  day_of_week, month, day_of_month,
                                  cost_per_unit]])

            base_demand = float(self.sklearn_model.predict(features)[0])

            # Weather adjustment
            multiplier = self._weather_multiplier(weather)
            predicted = max(0, int(round(base_demand * multiplier)))
            results.append(predicted)

        return pd.DataFrame({"predicted_demand": results})


# ---------------------------------------------------------------------------
# 6. Log & register model in Unity Catalog
# ---------------------------------------------------------------------------
print("Logging model to MLflow & registering in Unity Catalog...")

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(EXPERIMENT_NAME)

input_schema = Schema([
    ColSpec("string", "customer_name"),
    ColSpec("string", "product_name"),
    ColSpec("string", "date"),
    ColSpec("string", "weather_forecast"),
])
output_schema = Schema([
    ColSpec("long", "predicted_demand"),
])
signature = ModelSignature(inputs=input_schema, outputs=output_schema)

# Sample input for testing
sample_input = pd.DataFrame({
    "customer_name": ["FreshWay Supermarket"],
    "product_name": ["Organic Tomatoes"],
    "date": ["2026-02-19"],
    "weather_forecast": ["sunny and warm"],
})

pyfunc_model = DemandForecastModel(
    sklearn_model=model,
    customer_encoder=customer_encoder,
    product_encoder=product_encoder,
    dc_encoder=dc_encoder,
    customer_names=customer_names_list,
    product_names=product_names_list,
    dc_ids=dc_ids_list,
    customer_dc_map=customer_dc_map,
    product_cost_map=product_cost_map,
)

with mlflow.start_run(run_name="demand_forecast_v1") as run:
    mlflow.log_param("n_estimators", 200)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_param("training_rows", len(training_df))
    mlflow.log_param("n_products", len(product_names_list))
    mlflow.log_param("n_customers", len(customer_names_list))
    mlflow.log_metric("train_mae", mae)
    mlflow.log_metric("train_rmse", rmse)

    mlflow.pyfunc.log_model(
        artifact_path="demand_forecast",
        python_model=pyfunc_model,
        signature=signature,
        input_example=sample_input,
        pip_requirements=["scikit-learn", "pandas", "numpy"],
        registered_model_name=UC_MODEL_NAME,
    )

    print(f"Run ID: {run.info.run_id}")

# ---------------------------------------------------------------------------
# 7. Quick validation
# ---------------------------------------------------------------------------
print("\nValidation - sample predictions:")
test_input = pd.DataFrame({
    "customer_name": [
        "FreshWay Supermarket",
        "GreenGrocer Plus",
        "Market Fresh Foods",
    ],
    "product_name": [
        "Organic Tomatoes",
        "Organic Bananas",
        "Organic Strawberries",
    ],
    "date": ["2026-02-19", "2026-02-20", "2026-02-21"],
    "weather_forecast": ["sunny and warm", "heavy rain expected", "snow storm"],
})

preds = pyfunc_model.predict(context=None, model_input=test_input)
for i, row in test_input.iterrows():
    print(f"  {row['customer_name']} | {row['product_name']} | {row['date']} | "
          f"Weather: {row['weather_forecast']} => {preds.iloc[i]['predicted_demand']:,} units")

print(f"\nModel registered as: {UC_MODEL_NAME}")
print("Training complete!")
