import pandas as pd
import lightgbm as lgb
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import GridSearchCV
from lightgbm import LGBMRegressor
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np

client = MongoClient("mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict")
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

param_grid = {
    "num_leaves": [50, 63, 75],
    "max_depth": [10, 15, 20],
    "learning_rate": [0.2, 0.15, 0.1],
    "n_estimators": [100, 200],
    "min_child_samples": [15, 25]
}

model = LGBMRegressor(random_state=42)

grid = GridSearchCV(
    model,
    param_grid,
    scoring="neg_root_mean_squared_error",
    cv=2,
    verbose=1,
    n_jobs=-1
)

grid.fit(X_train, y_train)

print("Best Parameters:", grid.best_params_)
print("Best RMSE:", -grid.best_score_)

# Optionally test it on the test set
best_model = grid.best_estimator_
y_pred = best_model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"Test RMSE of best model: {rmse:.2f}")

# Save model
joblib.dump(model, "best_lgbm_model.pkl")