"""
LSTM-based per-qubit eavesdropping detector for BB84.

Unlike the Random Forest classifier in eavesdrop_detector.py — which sees only
six summary features per run (QBER, sifting efficiency, noise levels, etc.) —
this module consumes the full per-qubit exchange as a temporal sequence and
learns sequence-level signatures that the summary statistics flatten away.

Why a recurrent model? An intercept-resend attack produces a specific
*pattern* of bob_result randomisation: errors cluster on basis-matched
positions where Eve guessed the wrong basis, while basis-mismatched
positions stay uniformly random whether Eve is there or not. The joint
distribution of consecutive (alice_basis, bob_basis, bob_result) tuples
therefore differs subtly between the two regimes, and an LSTM can pick
this up where a feature-engineered RF cannot.

Architecture (intentionally small — CPU-only, no GPU expected):
    Input  : [seq_len, 6]  per-qubit features
    LSTM   : hidden=32, 1 layer
    Pool   : mean over time
    FC     : 32 -> 2 (logits)
    Output : softmax probabilities

Training data is synthesised on demand: we draw random QKD-run statistics
(Eve rate, noise rate) and roll the corresponding qubit-level outcomes.
A frozen training corpus of ~600 sequences is enough for the model to
converge on this binary task in <30 seconds on CPU.

Weights are persisted to backend/ml/lstm_weights.pt so the first request
after a server restart is cheap.
"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

log = logging.getLogger(__name__)

# --- Architecture hyperparameters ---
N_FEATURES = 6
HIDDEN_SIZE = 64
N_LAYERS = 1
N_CLASSES = 2

# --- Training hyperparameters ---
N_TRAIN_SAMPLES = 1200
N_VAL_SAMPLES = 200
MIN_SEQ_LEN = 80
MAX_SEQ_LEN = 250
N_EPOCHS = 60
BATCH_SIZE = 32
LEARNING_RATE = 2e-3

_WEIGHTS_PATH = Path(__file__).parent / "lstm_weights.pt"


class LstmEavesdropDetector(nn.Module):
    """Compact LSTM classifier for per-qubit BB84 exchange sequences."""

    def __init__(self, n_features=N_FEATURES, hidden=HIDDEN_SIZE,
                 n_layers=N_LAYERS, n_classes=N_CLASSES):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            num_layers=n_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x, lengths=None):
        # x: [batch, seq_len, n_features]
        out, (h_n, _) = self.lstm(x)
        if lengths is None:
            # Concatenate mean-pool and last hidden state for a richer signature.
            pooled_mean = out.mean(dim=1)
        else:
            mask = torch.arange(out.size(1), device=out.device)[None, :] < lengths[:, None]
            mask = mask.unsqueeze(-1).float()
            pooled_mean = (out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        # h_n: [n_layers, batch, hidden] -> take final layer
        h_last = h_n[-1]
        combined = pooled_mean + h_last
        return self.fc(combined)


# ======================================================================
# Synthetic training-data generator
# ======================================================================

def _build_sequence(rng: np.random.Generator, eve_rate: float,
                    noise_rate: float, n: int) -> np.ndarray:
    """
    Roll one synthetic BB84 qubit-exchange sequence.

    For each position i we produce a 6-dim feature vector matching what
    the websocket emits during a real run.
    """
    alice_bits = rng.integers(0, 2, n)
    alice_bases = rng.integers(0, 2, n)
    bob_bases = rng.integers(0, 2, n)
    basis_match = (alice_bases == bob_bases).astype(np.int8)

    bob_results = np.empty(n, dtype=np.int8)
    for i in range(n):
        if basis_match[i]:
            # Honest channel: bit flips with probability noise_rate.
            flip = rng.random() < noise_rate
            bob_results[i] = alice_bits[i] ^ int(flip)
            # If Eve intercepted and picked the wrong basis, the resent
            # qubit collapses → 50/50 random for Bob.
            if rng.random() < eve_rate:
                if rng.integers(0, 2) == 0:  # Eve's basis wrong half the time
                    bob_results[i] = int(rng.integers(0, 2))
        else:
            # Basis mismatch: 50/50 random regardless.
            bob_results[i] = int(rng.integers(0, 2))

    error = ((bob_results != alice_bits) & basis_match.astype(bool)).astype(np.int8)

    feats = np.stack([
        alice_bases.astype(np.float32),
        bob_bases.astype(np.float32),
        alice_bits.astype(np.float32),
        bob_results.astype(np.float32),
        basis_match.astype(np.float32),
        error.astype(np.float32),
    ], axis=1)  # [n, 6]
    return feats


def _build_dataset(n_samples: int, rng: np.random.Generator,
                   max_len: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build a padded dataset of synthetic sequences. Label = 1 ⇔ Eve present."""
    X = np.zeros((n_samples, max_len, N_FEATURES), dtype=np.float32)
    y = np.zeros(n_samples, dtype=np.int64)
    lens = np.zeros(n_samples, dtype=np.int64)

    for k in range(n_samples):
        eve_present = bool(rng.integers(0, 2))
        if eve_present:
            # Bias toward the boundary regime: 60 % of Eve samples have
            # rate ∈ [0.25, 0.45] (hard to distinguish from honest noise),
            # 40 % have rate ∈ [0.45, 1.0] (easy). Without this skew the
            # model under-detects intercept-resend at the operational
            # 0.30 setting used by the front-end.
            if rng.random() < 0.6:
                eve_rate = float(rng.uniform(0.25, 0.45))
            else:
                eve_rate = float(rng.uniform(0.45, 1.0))
        else:
            eve_rate = 0.0
        noise_rate = float(rng.uniform(0.005, 0.05))
        n = int(rng.integers(MIN_SEQ_LEN, max_len + 1))
        seq = _build_sequence(rng, eve_rate, noise_rate, n)
        X[k, :n, :] = seq
        y[k] = 1 if eve_present else 0
        lens[k] = n

    return (
        torch.from_numpy(X),
        torch.from_numpy(y),
        torch.from_numpy(lens),
    )


# ======================================================================
# Train + persist
# ======================================================================

def train(force: bool = False) -> dict:
    """
    Train the LSTM on freshly synthesised data and persist weights.

    Returns a metrics dict (final train/val loss and accuracy).
    """
    rng = np.random.default_rng(42)
    log.info("Training LSTM eavesdrop detector — synthesising training data…")

    X_train, y_train, len_train = _build_dataset(N_TRAIN_SAMPLES, rng, MAX_SEQ_LEN)
    X_val, y_val, len_val = _build_dataset(N_VAL_SAMPLES, rng, MAX_SEQ_LEN)

    train_ds = TensorDataset(X_train, y_train, len_train)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    model = LstmEavesdropDetector()
    optimiser = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    last_train_loss = math.nan
    last_train_acc = 0.0
    for epoch in range(N_EPOCHS):
        model.train()
        losses, n_correct, n_total = [], 0, 0
        for X_b, y_b, len_b in train_loader:
            optimiser.zero_grad()
            logits = model(X_b, len_b)
            loss = criterion(logits, y_b)
            loss.backward()
            optimiser.step()
            losses.append(loss.item())
            preds = logits.argmax(dim=-1)
            n_correct += int((preds == y_b).sum().item())
            n_total += int(y_b.numel())
        last_train_loss = float(np.mean(losses))
        last_train_acc = n_correct / max(n_total, 1)

    model.eval()
    with torch.no_grad():
        val_logits = model(X_val, len_val)
        val_loss = float(criterion(val_logits, y_val).item())
        val_preds = val_logits.argmax(dim=-1)
        val_acc = float((val_preds == y_val).sum().item() / y_val.numel())

    torch.save({
        "state_dict": model.state_dict(),
        "metrics": {
            "train_loss": round(last_train_loss, 4),
            "train_acc": round(last_train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "n_train": N_TRAIN_SAMPLES,
            "n_val": N_VAL_SAMPLES,
            "n_epochs": N_EPOCHS,
        },
    }, _WEIGHTS_PATH)

    log.info(
        "LSTM trained: train_acc=%.4f val_acc=%.4f val_loss=%.4f",
        last_train_acc, val_acc, val_loss,
    )
    return {
        "trained": True,
        "train_acc": round(last_train_acc, 4),
        "val_acc": round(val_acc, 4),
        "val_loss": round(val_loss, 4),
        "n_train": N_TRAIN_SAMPLES,
        "n_val": N_VAL_SAMPLES,
        "n_epochs": N_EPOCHS,
    }


# ======================================================================
# Inference
# ======================================================================

_model: LstmEavesdropDetector | None = None
_metrics: dict | None = None


def _ensure_loaded() -> bool:
    global _model, _metrics
    if _model is not None:
        return True
    if not _WEIGHTS_PATH.exists():
        return False
    try:
        ckpt = torch.load(_WEIGHTS_PATH, map_location="cpu", weights_only=False)
        m = LstmEavesdropDetector()
        m.load_state_dict(ckpt["state_dict"])
        m.eval()
        _model = m
        _metrics = ckpt.get("metrics", {})
        return True
    except Exception as exc:
        log.error("Failed to load LSTM weights: %s", exc)
        return False


def ensure_trained() -> dict:
    """Load existing weights, training fresh ones if none present."""
    if _ensure_loaded():
        return {"trained": True, **(_metrics or {})}
    train()
    _ensure_loaded()
    return {"trained": True, **(_metrics or {})}


def predict(alice_bits, alice_bases, bob_bases, bob_results) -> dict | None:
    """
    Predict P(Eve | full per-qubit exchange) for a single QKD run.

    All four inputs are equal-length lists of integers (0/1). Returns None
    if the model is unavailable.
    """
    if not _ensure_loaded():
        return None

    n = min(len(alice_bits), len(alice_bases), len(bob_bases), len(bob_results))
    if n == 0:
        return None

    a_bits = np.asarray(alice_bits[:n], dtype=np.float32)
    a_bases = np.asarray(alice_bases[:n], dtype=np.float32)
    b_bases = np.asarray(bob_bases[:n], dtype=np.float32)
    b_results = np.asarray(bob_results[:n], dtype=np.float32)
    basis_match = (a_bases == b_bases).astype(np.float32)
    error = ((b_results != a_bits).astype(np.float32) * basis_match)

    feats = np.stack([
        a_bases, b_bases, a_bits, b_results, basis_match, error,
    ], axis=1)[None, ...]  # [1, n, 6]

    x = torch.from_numpy(feats)
    lens = torch.tensor([n], dtype=torch.int64)
    with torch.no_grad():
        logits = _model(x, lens)
        proba = torch.softmax(logits, dim=-1)[0].cpu().numpy()
    p_eve = float(proba[1])
    return {
        "eve_probability": round(p_eve, 4),
        "lstm_verdict": "compromised" if p_eve >= 0.5 else "secure",
        "threshold": 0.5,
        "model_type": "lstm",
        "metrics": _metrics or {},
        "sequence_length": n,
    }


def get_metrics() -> dict | None:
    if not _ensure_loaded():
        return None
    return _metrics
