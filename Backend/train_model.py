import pandas as pd
import lightgbm as lgb
import joblib
import matplotlib.pyplot as plt

from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np

client = MongoClient("") # MISSING LINK
df = pd.DataFrame(list(client["BusDelayPredict"]["journeysBN"].find({})))
client.close()

# Add cyclic time-of-day features
df["scheduled_mins"] = df["scheduled_mins"].astype(int)
df["time_sin"] = np.sin(2 * np.pi * df["scheduled_mins"] / 1440)
df["time_cos"] = np.cos(2 * np.pi * df["scheduled_mins"] / 1440)

# Target encoding
for col in ["origin", "destination", "stop_name"]:
    mean_map = df.groupby(col)["delay_mins"].mean().to_dict()
    df[f"{col}_te"] = df[col].map(mean_map)

# Define features and target
features = [
    "time_sin", "time_cos", "day_of_week", "is_holiday",
    "service_id", "stop_index",
    "origin_te", "destination_te", "stop_name_te"
]
X = df[features]
y = df["delay_mins"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = lgb.LGBMRegressor(random_state=42, learning_rate=0.15, max_depth=30, min_child_samples=15, n_estimators=200, num_leaves=75)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"Test RMSE with target-encoded features: {rmse:.2f}")

# Save model
joblib.dump(model, "lgbm_model.pkl")

# Save target encodings as dictionaries
target_maps = {
    "origin": df.groupby("origin")["delay_mins"].mean().to_dict(),
    "destination": df.groupby("destination")["delay_mins"].mean().to_dict(),
    "stop_name": df.groupby("stop_name")["delay_mins"].mean().to_dict()
}
joblib.dump(target_maps, "target_encodings.pkl")