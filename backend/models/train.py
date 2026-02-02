"""
HorizonOps Model Training Pipeline
XGBoost classifier for predictive maintenance with SHAP explainability
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import xgboost as xgb
import shap
import joblib
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("horizonops.training")

# Feature configuration
FEATURE_COLUMNS = [
    'vibration_rms',
    'vibration_peak',
    'vibration_kurtosis',
    'temperature',
    'temp_rate_of_change',
    'power_consumption',
    'power_deviation',
    'time_since_maintenance',
    'cumulative_cycles',
    'hour_of_day',
    'day_of_week'
]

TARGET_COLUMN = 'failure_within_72h'


class PredictiveMaintenanceModel:
    """
    XGBoost-based predictive maintenance classifier.

    Predicts equipment failure within 72-hour window with
    SHAP-based explainability for operations trust.
    """

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.scaler = StandardScaler()
        self.explainer = None
        self.feature_columns = FEATURE_COLUMNS
        self.training_metadata = {}

    def train(self, data: pd.DataFrame, optimize_hyperparams: bool = False):
        """
        Train the predictive maintenance model.

        Args:
            data: Training DataFrame with features and target
            optimize_hyperparams: Whether to run Optuna optimization
        """
        logger.info("Starting model training pipeline...")

        # Prepare features and target
        X = data[self.feature_columns].copy()
        y = data[TARGET_COLUMN].copy()

        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")

        # Handle class imbalance
        scale_pos_weight = len(y[y == 0]) / len(y[y == 1])
        logger.info(f"Class imbalance ratio: {scale_pos_weight:.2f}")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)

        # XGBoost parameters (tuned for predictive maintenance)
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'min_child_weight': 3,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': scale_pos_weight,
            'random_state': 42,
            'n_jobs': -1
        }

        if optimize_hyperparams:
            params = self._optimize_hyperparameters(X_scaled, y, tscv)

        # Train final model
        self.model = xgb.XGBClassifier(**params)

        # Cross-validation scores
        cv_scores = []
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )

            y_pred = self.model.predict(X_val)
            y_prob = self.model.predict_proba(X_val)[:, 1]

            fold_metrics = {
                'precision': precision_score(y_val, y_pred),
                'recall': recall_score(y_val, y_pred),
                'f1': f1_score(y_val, y_pred),
                'auc': roc_auc_score(y_val, y_prob)
            }
            cv_scores.append(fold_metrics)
            logger.info(f"Fold {fold + 1}: Precision={fold_metrics['precision']:.3f}, Recall={fold_metrics['recall']:.3f}, AUC={fold_metrics['auc']:.3f}")

        # Final training on full data
        self.model.fit(X_scaled, y, verbose=False)

        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)

        # Store training metadata
        self.training_metadata = {
            'training_date': datetime.utcnow().isoformat(),
            'n_samples': len(X),
            'n_features': len(self.feature_columns),
            'feature_columns': self.feature_columns,
            'cv_metrics': {
                'precision_mean': np.mean([s['precision'] for s in cv_scores]),
                'precision_std': np.std([s['precision'] for s in cv_scores]),
                'recall_mean': np.mean([s['recall'] for s in cv_scores]),
                'recall_std': np.std([s['recall'] for s in cv_scores]),
                'f1_mean': np.mean([s['f1'] for s in cv_scores]),
                'auc_mean': np.mean([s['auc'] for s in cv_scores])
            },
            'model_params': params
        }

        logger.info("Training complete!")
        logger.info(f"CV Precision: {self.training_metadata['cv_metrics']['precision_mean']:.3f} (+/- {self.training_metadata['cv_metrics']['precision_std']:.3f})")
        logger.info(f"CV Recall: {self.training_metadata['cv_metrics']['recall_mean']:.3f}")

        return self.training_metadata

    def _optimize_hyperparameters(self, X, y, cv):
        """Run Optuna hyperparameter optimization."""
        import optuna

        def objective(trial):
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'random_state': 42
            }

            model = xgb.XGBClassifier(**params)
            scores = []

            for train_idx, val_idx in cv.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                model.fit(X_train, y_train, verbose=False)
                y_prob = model.predict_proba(X_val)[:, 1]
                scores.append(roc_auc_score(y_val, y_prob))

            return np.mean(scores)

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=50, show_progress_bar=True)

        logger.info(f"Best hyperparameters: {study.best_params}")
        return {**study.best_params, 'objective': 'binary:logistic', 'random_state': 42}

    def predict(self, features: pd.DataFrame) -> dict:
        """
        Make prediction with probability and explanation.

        Args:
            features: DataFrame with feature columns

        Returns:
            Dictionary with prediction, probability, and SHAP values
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X = features[self.feature_columns].copy()
        X_scaled = self.scaler.transform(X)

        probability = self.model.predict_proba(X_scaled)[0, 1]
        prediction = int(probability > 0.5)

        # Get SHAP values for explanation
        shap_values = self.explainer.shap_values(X_scaled)

        # Feature contributions
        contributions = dict(zip(
            self.feature_columns,
            shap_values[0].tolist() if isinstance(shap_values, np.ndarray) else shap_values[0]
        ))

        return {
            'prediction': prediction,
            'failure_probability': float(probability),
            'risk_score': float(probability * 100),
            'feature_contributions': contributions,
            'top_risk_factors': self._get_top_factors(contributions)
        }

    def _get_top_factors(self, contributions: dict, n: int = 3) -> list:
        """Get top contributing factors to prediction."""
        sorted_factors = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return [
            {'feature': f, 'contribution': round(c, 4)}
            for f, c in sorted_factors[:n]
        ]

    def save(self, version: str = "v1"):
        """Save model, scaler, and metadata."""
        model_path = self.model_dir / f"xgboost_{version}.pkl"
        scaler_path = self.model_dir / f"scaler_{version}.pkl"
        metadata_path = self.model_dir / f"metadata_{version}.json"

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        with open(metadata_path, 'w') as f:
            json.dump(self.training_metadata, f, indent=2)

        logger.info(f"Model saved to {model_path}")

    def load(self, version: str = "v1"):
        """Load model, scaler, and metadata."""
        model_path = self.model_dir / f"xgboost_{version}.pkl"
        scaler_path = self.model_dir / f"scaler_{version}.pkl"
        metadata_path = self.model_dir / f"metadata_{version}.json"

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)

        with open(metadata_path, 'r') as f:
            self.training_metadata = json.load(f)

        self.explainer = shap.TreeExplainer(self.model)
        logger.info(f"Model loaded from {model_path}")


def evaluate_model(model: PredictiveMaintenanceModel, test_data: pd.DataFrame):
    """Comprehensive model evaluation."""
    X_test = test_data[FEATURE_COLUMNS]
    y_test = test_data[TARGET_COLUMN]

    X_scaled = model.scaler.transform(X_test)
    y_pred = model.model.predict(X_scaled)
    y_prob = model.model.predict_proba(X_scaled)[:, 1]

    print("\n" + "=" * 50)
    print("MODEL EVALUATION REPORT")
    print("=" * 50)
    print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")
    print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")

    # Feature importance
    importance = pd.DataFrame({
        'feature': FEATURE_COLUMNS,
        'importance': model.model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\nFeature Importance:\n{importance.to_string(index=False)}")


if __name__ == "__main__":
    # Training script entry point
    logger.info("Loading training data...")

    # Load synthetic data
    data_path = Path("../data/synthetic/training_data.csv")
    if data_path.exists():
        data = pd.read_csv(data_path)
    else:
        logger.error("Training data not found. Run generate_synthetic_data.py first.")
        exit(1)

    # Train model
    model = PredictiveMaintenanceModel()
    model.train(data, optimize_hyperparams=False)

    # Save model
    model.save("v1")

    # Evaluate on held-out data
    test_data = data.tail(1000)
    evaluate_model(model, test_data)
