"""Tests for backtest metrics (RPS / log-loss / Brier) on known cases."""

import numpy as np
import pytest

from footpred.backtest import brier_one, log_loss_one, outcome, rps


def test_outcome_encoding():
    assert outcome(2, 1) == 0   # home win
    assert outcome(1, 1) == 1   # draw
    assert outcome(0, 3) == 2   # away win


def test_rps_perfect_prediction_is_zero():
    assert rps(np.array([1.0, 0.0, 0.0]), 0) == pytest.approx(0.0)


def test_rps_ordered_penalty():
    # Predicting away when home happened should cost more than predicting draw.
    probs = np.array([0.0, 0.0, 1.0])  # all on away
    far = rps(probs, 0)                # actual home — maximally wrong (ordered)
    near = rps(np.array([0.0, 1.0, 0.0]), 0)  # predicted draw, actual home
    assert far > near
    assert far == pytest.approx(1.0)   # max RPS for 3 ordered classes


def test_log_loss_and_brier_perfect():
    p = np.array([1.0, 0.0, 0.0])
    assert log_loss_one(p, 0) == pytest.approx(0.0, abs=1e-9)
    assert brier_one(p, 0) == pytest.approx(0.0)


def test_brier_uniform():
    p = np.array([1 / 3, 1 / 3, 1 / 3])
    # sum of squared error vs one-hot = (2/3)^2 + (1/3)^2 + (1/3)^2
    assert brier_one(p, 0) == pytest.approx((2 / 3) ** 2 + 2 * (1 / 3) ** 2)
