"""
Machine-learning-based eavesdropper detection for BB84.

The standard BB84 security check is a hard threshold: abort if QBER ≥ 11%.
This is robust but ignores additional context: noise level, channel distance,
sifting efficiency, and historical patterns. A QBER of 9% might be benign
(high noise + long fiber) or malicious (low noise + short fiber → Eve).

This module trains a binary classifier on the user's accumulated simulation
history to predict P(Eve | observed features). Features used:
  - qber                      — raw error rate
  - sifting_efficiency        — sifted_key_length / n_qubits
  - depolarizing_prob         — known gate noise
  - measurement_error_prob    — known measurement noise
  - channel_distance_km       — known channel loss contribution
  - n_qubits                  — sample size

A Random Forest is used because it handles the small-N regime gracefully
and produces calibrated probability estimates via voting.

Reference for the broader argument:
  arXiv:2603.27278 — "Quantum Bit Error Rate Analysis in BB84 Quantum Key
  Distribution: Measurement, Statistical Estimation, and Eavesdropping
  Detection", 2026 — discusses ML-augmented eavesdropping detection.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

FEATURE_NAMES = [
    "qber",
    "sifting_efficiency",
    "depolarizing_prob",
    "measurement_error_prob",
    "channel_distance_km",
    "n_qubits",
]

MIN_TRAINING_RUNS = 20  # need at least this many history entries to train
MIN_CLASS_SAMPLES = 5   # need at least this many of each class (Eve / no-Eve)


@dataclass
class ModelState:
    trained: bool = False
    n_samples: int = 0
    n_positive: int = 0   # runs with eve_intercept = True
    n_negative: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    feature_importance: dict | None = None
    model_type: str = ""
    error: str | None = None


# Module-level model cache (one per server process).
_model: Any = None
_state: ModelState = ModelState()


def extract_features(run) -> list[float]:
    """
    Build a feature vector from a SimulationRun row.

    Sifting efficiency = sifted_key_length / n_qubits.
    """
    n_qubits = max(int(run.n_qubits or 1), 1)
    sifted = int(run.sifted_key_length or 0)
    return [
        float(run.qber or 0.0),
        sifted / n_qubits,
        float(run.depolarizing_prob or 0.0),
        float(run.measurement_error_prob or 0.0),
        float(run.channel_distance_km or 0.0),
        float(n_qubits),
    ]


def extract_features_from_dict(d: dict) -> list[float]:
    """Same as extract_features but for a plain config dict (used at predict time)."""
    n_qubits = max(int(d.get("n_qubits", 1) or 1), 1)
    sifted = int(d.get("sifted_key_length", 0) or 0)
    return [
        float(d.get("qber", 0.0) or 0.0),
        sifted / n_qubits,
        float(d.get("depolarizing_prob", 0.0) or 0.0),
        float(d.get("measurement_error_prob", 0.0) or 0.0),
        float(d.get("channel_distance_km", 0.0) or 0.0),
        float(n_qubits),
    ]


def train_on_runs(runs: list, model_type: str = "random_forest") -> ModelState:
    """
    Train the eavesdropper classifier on the supplied simulation history.

    Args:
        runs:       Iterable of SimulationRun ORM objects.
        model_type: 'random_forest' or 'logistic_regression'.

    Returns:
        ModelState reflecting training outcome.
    """
    global _model, _state

    X, y = [], []
    for r in runs:
        X.append(extract_features(r))
        y.append(1 if bool(r.eve_intercept) else 0)

    X = np.asarray(X)
    y = np.asarray(y)

    n_positive = int(y.sum())
    n_negative = int(len(y) - n_positive)

    if len(y) < MIN_TRAINING_RUNS:
        _state = ModelState(
            trained=False, n_samples=len(y),
            n_positive=n_positive, n_negative=n_negative,
            error=f"Need at least {MIN_TRAINING_RUNS} runs (have {len(y)})."
        )
        _model = None
        return _state

    if n_positive < MIN_CLASS_SAMPLES or n_negative < MIN_CLASS_SAMPLES:
        _state = ModelState(
            trained=False, n_samples=len(y),
            n_positive=n_positive, n_negative=n_negative,
            error=(
                f"Need at least {MIN_CLASS_SAMPLES} runs of each class "
                f"(Eve-present and Eve-absent). Currently {n_positive} / {n_negative}."
            ),
        )
        _model = None
        return _state

    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=1000, class_weight="balanced")
    else:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )

    # Stratified holdout for honest accuracy reporting
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    feat_imp = None
    if hasattr(model, "feature_importances_"):
        feat_imp = {
            name: round(float(imp), 4)
            for name, imp in zip(FEATURE_NAMES, model.feature_importances_)
        }
    elif hasattr(model, "coef_"):
        coefs = model.coef_[0]
        feat_imp = {
            name: round(float(c), 4)
            for name, c in zip(FEATURE_NAMES, coefs)
        }

    # Refit on full data for production predictions
    model.fit(X, y)
    _model = model
    _state = ModelState(
        trained=True,
        n_samples=len(y),
        n_positive=n_positive,
        n_negative=n_negative,
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1=round(f1, 4),
        feature_importance=feat_imp,
        model_type=model_type,
    )
    return _state


def predict(features: list[float]) -> dict | None:
    """
    Predict eavesdropping probability for a single observation.

    Returns None if no trained model is available.
    """
    if _model is None or not _state.trained:
        return None
    X = np.asarray([features])
    proba = float(_model.predict_proba(X)[0, 1])  # P(class=1) = P(Eve present)
    return {
        "eve_probability": round(proba, 4),
        "ml_verdict": "compromised" if proba >= 0.5 else "secure",
        "threshold": 0.5,
    }


def get_state() -> ModelState:
    return _state
