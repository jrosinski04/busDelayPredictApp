import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.metrics import mean_squared_error
from lightgbm import LGBMRegressor
import joblib
import numpy as np
import os

# Configuration
MONGO_URI = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
DB_NAME = "BusDelayPredict"
COLLECTION = "journeysTEST"
os.environ["LOKY_MAX_CPU_COUNT"] = "8"

# Loading data from MongoDB into pandas data frame
client = MongoClient(MONGO_URI)
df = pd.DataFrame(list(client[DB_NAME][COLLECTION].find({})))
client.close()

# Dropping records with missing target
df = df.dropna(subset=["delay_mins", "scheduled_mins"])

# Defining features and target
feature_cols = [
    "scheduled_mins",
    "day_of_week",
    "is_peak",
    "stop_index",
    "service_id",
    "stop_name",
    "origin",
    "destination"
]
X = df[feature_cols]
y = df["delay_mins"]

# Splitting into train/test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Preprocessing pipelines
numeric_features = ["scheduled_mins", "day_of_week", "stop_index"]
numeric_transformer = "passthrough"

categorical_features = ["is_peak", "service_id", "stop_name", "origin", "destination"]
categorical_transformer = OneHotEncoder(handle_unknown="ignore")

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
    ],
    remainder="drop"
)

# Creating pipeline with LightGBM regressor
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", LGBMRegressor(
        objective="regression",
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbose=-1
    ))
])

# Training the model
model.fit(X_train, y_train)

# Evaluating on test set
y_pred = model.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
print(f"Test RMSE: {rmse:.2f} minutes")

# Saving the trained pipeline for later use
joblib.dump(model, "delay_predictor_lgbm.pkl")
