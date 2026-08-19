#!/usr/bin/env python3
"""
AML Prediction Pipeline
=======================

This script is the AML-oriented counterpart of the previously supplied
GraphSAGE test.py.

Important:
- aml_prediction_dataset.csv is a CUSTOMER-LEVEL feature table.
- It does not contain the account->account/device/IP graph required by the
  original GraphSAGE test.py.
- Therefore this script performs the AML prediction from the engineered
  customer/transaction features directly.
- It supports both binary AML suspicion prediction and 3-class AML risk
  prediction.
- The target columns are:
      aml_suspicious_label : 0/1
      aml_risk_label       : 0/1/2
- AML_Risk_Level itself is intentionally NOT used as an input feature.

Outputs:
    aml_artifacts/
        aml_model.joblib
        aml_preprocessor.joblib
        aml_feature_columns.json
        aml_test_predictions.csv
        aml_metrics.json
"""

import argparse
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression


# ============================================================
# Configuration
# ============================================================

DEFAULT_DATA = "aml_prediction_dataset.csv"
DEFAULT_OUTPUT = "aml_artifacts"
RANDOM_STATE = 42

# Columns that should never be model inputs.
# Some are identifiers; others are downstream risk/target variables.
EXCLUDE_FROM_FEATURES = {
    "Customer_ID",
    "aml_risk_label",
    "aml_suspicious_label",
    "AML_Risk_Level",

    # Potential target leakage / downstream model outputs
    "Customer_Risk_Category",
    "Customer_Segment",
    "Churn_Probability",
    "Cross_Sell_Probability",
    "Upsell_Probability",
    "Loan_Default_Risk",
}

# These are useful for audit/output but should not be used as predictors.
ID_COLUMNS = {"Customer_ID"}


# ============================================================
# Utility functions
# ============================================================

def safe_div(a, b):
    return a / np.where(np.abs(b) < 1e-12, 1.0, b)


def add_aml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a small number of robust AML-derived ratios if their source columns
    exist. The CSV already contains most engineered transaction features.
    """
    df = df.copy()

    # Transaction intensity relative to monthly income.
    if {"total_transaction_amount", "Monthly_Income"}.issubset(df.columns):
        df["txn_to_monthly_income_ratio"] = safe_div(
            df["total_transaction_amount"],
            df["Monthly_Income"],
        )

    # Outstanding debt relative to income.
    if {"Outstanding_Loan_Amount", "Annual_Income"}.issubset(df.columns):
        df["loan_to_annual_income_ratio"] = safe_div(
            df["Outstanding_Loan_Amount"],
            df["Annual_Income"],
        )

    # High-value transactions relative to account balance.
    if {"max_transaction_amount", "Avg_Monthly_Balance"}.issubset(df.columns):
        df["max_txn_to_balance_ratio"] = safe_div(
            df["max_transaction_amount"],
            df["Avg_Monthly_Balance"],
        )

    # Suspicious activity density.
    if {"Suspicious_Transaction_Count", "txn_count"}.issubset(df.columns):
        df["suspicious_txn_ratio"] = safe_div(
            df["Suspicious_Transaction_Count"],
            df["txn_count"],
        )

    # Beneficiary changes relative to transaction activity.
    if {"Beneficiary_Change_Frequency", "txn_count"}.issubset(df.columns):
        df["beneficiary_change_ratio"] = safe_div(
            df["Beneficiary_Change_Frequency"],
            df["txn_count"],
        )

    # Security / transaction-risk composite.
    risk_cols = [
        c for c in [
            "transaction_risk_mean",
            "Fraud_Risk_Score",
            "Velocity_Score",
            "Geo_Anomaly_Flag",
            "Account_Takeover_Risk",
        ]
        if c in df.columns
    ]
    if risk_cols:
        df["aml_signal_mean"] = df[risk_cols].apply(
            pd.to_numeric, errors="coerce"
        ).mean(axis=1)

    df = df.replace([np.inf, -np.inf], np.nan)
    return df


def build_preprocessor(X: pd.DataFrame):
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [
        c for c in X.columns
        if c not in numeric_cols
    ]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                min_frequency=5,
            ),
        ),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )

    return preprocessor, numeric_cols, categorical_cols


def create_model():
    """
    Logistic regression is deliberately used as a strong, reproducible
    baseline. It handles the class imbalance through balanced weights and
    produces calibrated-ish probabilities that are easy to consume in the
    voice agent/API layer.

    You can replace this estimator with XGBoost/LightGBM/CatBoost later
    without changing the feature pipeline.
    """
    return LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="saga",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


# ============================================================
# Training
# ============================================================

def train(data_path: str, output_dir: str, target: str):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    print(f"Loading: {data_path}")
    df = pd.read_csv(data_path)

    if target not in df.columns:
        raise ValueError(
            f"Target '{target}' not found. "
            f"Available targets: "
            f"{[c for c in ['aml_suspicious_label', 'aml_risk_label'] if c in df.columns]}"
        )

    df = add_aml_features(df)

    # Preserve ID for final predictions.
    ids = df["Customer_ID"].copy() if "Customer_ID" in df.columns else pd.Series(
        np.arange(len(df)), name="Customer_ID"
    )

    # Target
    y = pd.to_numeric(df[target], errors="raise")

    # Features
    feature_cols = [
        c for c in df.columns
        if c not in EXCLUDE_FROM_FEATURES
    ]
    X = df[feature_cols].copy()

    # Drop all-null columns.
    all_null = [c for c in X.columns if X[c].isna().all()]
    if all_null:
        X = X.drop(columns=all_null)
        feature_cols = [c for c in feature_cols if c not in all_null]

    print(f"Rows: {len(df):,}")
    print(f"Features before encoding: {len(feature_cols):,}")
    print("\nTarget distribution:")
    print(y.value_counts().sort_index())

    # Stratified split
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X,
        y,
        ids,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    preprocessor, numeric_cols, categorical_cols = build_preprocessor(X_train)
    model = create_model()

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])

    print("\nTraining AML model...")
    pipeline.fit(X_train, y_train)

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------
    pred = pipeline.predict(X_test)
    prob = pipeline.predict_proba(X_test)

    metrics = {
        "target": target,
        "rows": int(len(df)),
        "num_input_features": int(len(feature_cols)),
        "test_rows": int(len(X_test)),
        "random_state": RANDOM_STATE,
        "class_distribution": {
            str(k): int(v)
            for k, v in y.value_counts().sort_index().items()
        },
    }

    if len(np.unique(y_test)) == 2:
        positive_prob = prob[:, 1]

        metrics.update({
            "roc_auc": float(roc_auc_score(y_test, positive_prob)),
            "pr_auc": float(average_precision_score(y_test, positive_prob)),
            "precision": float(precision_score(
                y_test, pred, zero_division=0
            )),
            "recall": float(recall_score(
                y_test, pred, zero_division=0
            )),
            "f1": float(f1_score(
                y_test, pred, zero_division=0
            )),
        })

        print(f"\nROC-AUC : {metrics['roc_auc']:.4f}")
        print(f"PR-AUC  : {metrics['pr_auc']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall   : {metrics['recall']:.4f}")
        print(f"F1       : {metrics['f1']:.4f}")

    else:
        metrics["macro_f1"] = float(
            f1_score(y_test, pred, average="macro", zero_division=0)
        )
        metrics["weighted_f1"] = float(
            f1_score(y_test, pred, average="weighted", zero_division=0)
        )

        # One-vs-rest ROC-AUC/PR-AUC for multiclass.
        try:
            metrics["roc_auc_ovr"] = float(
                roc_auc_score(
                    y_test,
                    prob,
                    multi_class="ovr",
                    average="macro",
                )
            )
        except ValueError:
            pass

        print(f"\nMacro F1    : {metrics['macro_f1']:.4f}")
        print(f"Weighted F1 : {metrics['weighted_f1']:.4f}")
        if "roc_auc_ovr" in metrics:
            print(f"ROC-AUC OVR : {metrics['roc_auc_ovr']:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, pred, zero_division=0))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, pred))

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------
    predictions = pd.DataFrame({
        "Customer_ID": id_test.values,
        "actual_label": y_test.values,
        "predicted_label": pred,
    })

    if prob.shape[1] == 2:
        predictions["aml_probability"] = prob[:, 1]
        predictions["risk_level"] = np.where(
            prob[:, 1] >= 0.75,
            "HIGH",
            np.where(prob[:, 1] >= 0.40, "MEDIUM", "LOW"),
        )
    else:
        for i, cls in enumerate(pipeline.classes_):
            predictions[f"probability_class_{cls}"] = prob[:, i]

        # Probability of any non-low AML class.
        if 0 in list(pipeline.classes_):
            low_idx = list(pipeline.classes_).index(0)
            predictions["aml_probability"] = 1.0 - prob[:, low_idx]
        else:
            predictions["aml_probability"] = prob.max(axis=1)

        predictions["risk_level"] = np.select(
            [
                predictions["aml_probability"] >= 0.75,
                predictions["aml_probability"] >= 0.40,
            ],
            ["HIGH", "MEDIUM"],
            default="LOW",
        )

    pred_path = output / "aml_test_predictions.csv"
    predictions.sort_values(
        "aml_probability",
        ascending=False,
    ).to_csv(pred_path, index=False)

    # Save pipeline.
    model_path = output / "aml_model.joblib"
    joblib.dump(pipeline, model_path)

    with open(output / "aml_feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    with open(output / "aml_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved:")
    print(f"  Model       : {model_path}")
    print(f"  Predictions : {pred_path}")
    print(f"  Metrics     : {output / 'aml_metrics.json'}")

    return pipeline


# ============================================================
# Prediction on new customer CSV
# ============================================================

def predict(data_path: str, model_path: str, output_path: str):
    print(f"Loading data: {data_path}")
    df = pd.read_csv(data_path)

    original_ids = (
        df["Customer_ID"].copy()
        if "Customer_ID" in df.columns
        else pd.Series(np.arange(len(df)), name="Customer_ID")
    )

    df = add_aml_features(df)

    feature_cols = [
        c for c in df.columns
        if c not in EXCLUDE_FROM_FEATURES
    ]

    X = df[feature_cols].copy()

    pipeline = joblib.load(model_path)

    # Ensure prediction columns match training.
    # Missing columns are filled with NaN; unknown extra columns are ignored.
    saved_feature_file = Path(model_path).with_name("aml_feature_columns.json")
    if saved_feature_file.exists():
        with open(saved_feature_file) as f:
            trained_features = json.load(f)

        for col in trained_features:
            if col not in X.columns:
                X[col] = np.nan

        X = X[trained_features]

    pred = pipeline.predict(X)
    prob = pipeline.predict_proba(X)

    result = pd.DataFrame({
        "Customer_ID": original_ids.values,
        "aml_predicted_label": pred,
    })

    if prob.shape[1] == 2:
        result["aml_probability"] = prob[:, 1]
    else:
        classes = list(pipeline.classes_)

        if 0 in classes:
            low_idx = classes.index(0)
            result["aml_probability"] = 1.0 - prob[:, low_idx]
        else:
            result["aml_probability"] = prob.max(axis=1)

        for i, cls in enumerate(classes):
            result[f"probability_class_{cls}"] = prob[:, i]

    result["risk_level"] = np.select(
        [
            result["aml_probability"] >= 0.75,
            result["aml_probability"] >= 0.40,
        ],
        ["HIGH", "MEDIUM"],
        default="LOW",
    )

    result = result.sort_values(
        "aml_probability",
        ascending=False,
    )

    result.to_csv(output_path, index=False)

    print("\nPrediction complete.")
    print(result.head(20).to_string(index=False))
    print(f"\nSaved: {output_path}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="AML prediction from engineered customer/transaction data"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    train_parser = sub.add_parser("train")
    train_parser.add_argument(
        "--data",
        default=DEFAULT_DATA,
        help="AML feature CSV",
    )
    train_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output artifact directory",
    )
    train_parser.add_argument(
        "--target",
        choices=["aml_suspicious_label", "aml_risk_label"],
        default="aml_suspicious_label",
        help="Prediction target",
    )

    pred_parser = sub.add_parser("predict")
    pred_parser.add_argument(
        "--data",
        required=True,
        help="New customer feature CSV",
    )
    pred_parser.add_argument(
        "--model",
        default="aml_artifacts/aml_model.joblib",
        help="Saved AML model",
    )
    pred_parser.add_argument(
        "--output",
        default="aml_predictions.csv",
        help="Prediction output CSV",
    )

    args = parser.parse_args()

    if args.command == "train":
        train(
            data_path=args.data,
            output_dir=args.output,
            target=args.target,
        )

    elif args.command == "predict":
        predict(
            data_path=args.data,
            model_path=args.model,
            output_path=args.output,
        )


if __name__ == "__main__":
    main()
