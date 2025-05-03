import pandas as pd
import numpy as np
import joblib
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
from lightgbm import LGBMRegressor, early_stopping, log_evaluation
from sklearn.metrics import mean_squared_error
import os

# Configuration
MONGO_URI  = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
DB_NAME    = "BusDelayPredict"
COLLECTION = "journeysBN"

# Feature definitions
NUMERIC_FEATURES     = ["scheduled_mins", "day_of_week", "stop_index"]
CATEGORICAL_FEATURES = ["is_holiday", "is_peak", "service_id", "stop_name", "origin", "destination"]
ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET               = "delay_mins"

def is_peak(mins: int, weekday: int) -> bool:
    if weekday >= 5:
        return False
    return (420 <= mins < 540) or (900 <= mins < 1080)

def main():
    # 1) Load raw data from MongoDB
    client = MongoClient(MONGO_URI)
    df = pd.DataFrame(list(client[DB_NAME][COLLECTION].find({})))
    client.close()

    # 2) Drop rows with missing target or numeric features
    df = df.dropna(subset=[TARGET] + NUMERIC_FEATURES + ["day_of_week"])

    # Filter out unrealistic delays (e.g., more than 3 hours or less than -1 hour)
    df = df[df["delay_mins"].between(-60, 180)]

    # 3) Compute day_of_week and is_peak if missing
    if "day_of_week" not in df:
        df["day_of_week"] = pd.to_datetime(df["date"]).dt.weekday
    if "is_peak" not in df:
        df["is_peak"] = df.apply(lambda r: is_peak(r["scheduled_mins"], r["day_of_week"]), axis=1)

    # 4) Split into train/test
    X = df[ALL_FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 5) Tapered up-sampling (30% of zero delays)
    train_df   = pd.concat([X_train, y_train.reset_index(drop=True)], axis=1)
    df_zero    = train_df[train_df[TARGET] == 0]
    df_nonzero = train_df[train_df[TARGET] >  0]
    n_zero     = len(df_zero)
    n_up       = int(1.0)
    df_nonzero_up = resample(
        df_nonzero,
        replace=True,
        n_samples=n_up,
        random_state=42
    )
    df_balanced = pd.concat([df_zero, df_nonzero_up]).reset_index(drop=True)
    Xb = df_balanced[ALL_FEATURES]
    yb = df_balanced[TARGET]

    # 6) Scale numeric features
    scaler = StandardScaler()
    Xb_num      = scaler.fit_transform(Xb[NUMERIC_FEATURES])
    Xtest_num   = scaler.transform(X_test[NUMERIC_FEATURES])
    Xb_prepared = pd.concat([
        pd.DataFrame(Xb_num, columns=NUMERIC_FEATURES),
        Xb[CATEGORICAL_FEATURES].reset_index(drop=True)
    ], axis=1)
    Xtest_prepared = pd.concat([
        pd.DataFrame(Xtest_num, columns=NUMERIC_FEATURES),
        X_test[CATEGORICAL_FEATURES].reset_index(drop=True)
    ], axis=1)

    # 6.1) Cast all categorical columns to pd.Categorical
    for col in CATEGORICAL_FEATURES:
        Xb_prepared[col] = pd.Categorical(Xb_prepared[col])
        Xtest_prepared[col] = pd.Categorical(Xtest_prepared[col])


    # 7) Configure LightGBM with Huber objective and regularization
    model = LGBMRegressor(
        objective="huber",
        alpha=0.9,
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=64,
        min_child_samples=5,
        reg_alpha=0,
        reg_lambda=0,
        random_state=42,
        categorical_feature=CATEGORICAL_FEATURES,
        verbosity=-1
    )

    # 8) Fit with early stopping and logging callback
    model.fit(
        Xb_prepared, yb,
        eval_set=[(Xtest_prepared, y_test)],
        callbacks=[
            early_stopping(stopping_rounds=20),
            log_evaluation(period=20)
        ]
    )

    # 9) Evaluate performance
    preds = model.predict(Xtest_prepared)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    print(f"Test RMSE: {rmse:.2f} minutes")

    # 10) Save scaler and model
    os.makedirs("models", exist_ok=True)
    joblib.dump(scaler, "models/scaler.pkl")
    joblib.dump(model,   "models/best_lgbm_delay.pkl")
    print("Saved scaler and model to models/")

if __name__ == "__main__":
    main()
