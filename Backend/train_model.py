import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
from sklearn.utils import resample
from lightgbm import LGBMRegressor
from pymongo import MongoClient

# Configuration
MONGO_URI  = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
DB_NAME    = "BusDelayPredict"
COLLECTION = "journeysBN"

def main():
    # 1. Load data
    client = MongoClient(MONGO_URI)
    df = pd.DataFrame(list(client[DB_NAME][COLLECTION].find({})))
    client.close()

    # 2. Drop incomplete rows
    df = df.dropna(subset=["delay_mins", "scheduled_mins"])

    # 3. Features & target
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

    # 4. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 5. Upsample minority class in the training set
    train_df = pd.concat([X_train, y_train.reset_index(drop=True)], axis=1)
    df_zero    = train_df[train_df["delay_mins"] == 0]
    df_nonzero = train_df[train_df["delay_mins"] >  0]

    df_nonzero_upsampled = resample(
        df_nonzero,
        replace=True,
        n_samples=len(df_zero),
        random_state=42
    )

    df_balanced = pd.concat([df_zero, df_nonzero_upsampled])
    X_train_bal = df_balanced[feature_cols]
    y_train_bal = df_balanced["delay_mins"]

    # 6. Preprocessing pipeline
    numeric_features     = ["scheduled_mins", "day_of_week", "stop_index"]
    categorical_features = ["is_peak", "service_id", "stop_name", "origin", "destination"]

    preprocessor = ColumnTransformer([
        ("num", "passthrough", numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ])

    # 7. sklearn pipeline (no oversampler)
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", LGBMRegressor(objective="regression", random_state=42))
    ])

    # 8. Hyperparameter grid
    param_grid = {
        "regressor__n_estimators":  [100, 200, 300],
        "regressor__learning_rate": [0.01, 0.05, 0.1],
        "regressor__num_leaves":    [31, 63],
        "regressor__max_depth":     [-1, 10, 20],
    }

    # 9. Grid search
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=5,
        scoring="neg_mean_squared_error",
        verbose=2,
        n_jobs=-1
    )
    grid_search.fit(X_train_bal, y_train_bal)

    # 10. Report
    best_params = grid_search.best_params_
    best_rmse   = np.sqrt(-grid_search.best_score_)
    print("Best parameters:", best_params)
    print(f"Cross-validated RMSE: {best_rmse:.2f} minutes")

    # 11. Test-set evaluation
    best_model = grid_search.best_estimator_
    y_pred     = best_model.predict(X_test)
    test_rmse  = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"Test RMSE: {test_rmse:.2f} minutes")

    # 12. Persist
    joblib.dump(best_model, "best_delay_predictor_lgbm.pkl")
    print("Tuned model saved as best_delay_predictor_lgbm.pkl")

if __name__ == "__main__":
    main()
