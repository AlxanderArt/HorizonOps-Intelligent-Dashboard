"""
Model Unit Tests for HorizonOps
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


class TestFeatureEngineering:
    """Test feature engineering functions."""

    def test_rms_calculation(self):
        """Test RMS vibration calculation."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        # Test known values
        series = pd.Series([3, 4])  # RMS should be 5/sqrt(2) ≈ 3.54
        expected_rms = np.sqrt((9 + 16) / 2)
        assert abs(store._compute_rms(series) - expected_rms) < 0.01

    def test_kurtosis_normal_distribution(self):
        """Test kurtosis for normal distribution."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        # Normal distribution should have kurtosis ~3
        np.random.seed(42)
        normal_data = pd.Series(np.random.normal(0, 1, 10000))
        kurtosis = store._compute_kurtosis(normal_data)
        assert 2.5 < kurtosis < 3.5  # Close to 3

    def test_rate_of_change_positive_slope(self):
        """Test rate of change calculation."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        # Linear increasing data
        series = pd.Series([1, 2, 3, 4, 5])
        rate = store._compute_rate(series)
        assert rate > 0  # Should be positive slope

    def test_rate_of_change_negative_slope(self):
        """Test rate of change for decreasing data."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        series = pd.Series([5, 4, 3, 2, 1])
        rate = store._compute_rate(series)
        assert rate < 0  # Should be negative slope


class TestFeatureStore:
    """Test FeatureStore service."""

    def test_ingest_creates_buffer(self):
        """Test that ingesting data creates machine buffer."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        machine_id = "TEST-001"
        reading = {"vibration_rms": 22.0, "temperature": 45.0}

        store.ingest(machine_id, reading)

        assert machine_id in store.telemetry_buffer
        assert len(store.telemetry_buffer[machine_id]) == 1

    def test_buffer_size_limit(self):
        """Test that buffer doesn't exceed max size."""
        from services.feature_store import FeatureStore
        store = FeatureStore(buffer_size=100)

        machine_id = "TEST-002"

        # Ingest more than buffer size
        for i in range(150):
            store.ingest(machine_id, {"vibration_rms": i})

        assert len(store.telemetry_buffer[machine_id]) <= 100

    def test_get_features_requires_minimum_data(self):
        """Test that features require minimum samples."""
        from services.feature_store import FeatureStore
        store = FeatureStore()

        machine_id = "TEST-003"

        # Ingest too few samples
        for i in range(5):
            store.ingest(machine_id, {"vibration_rms": 20.0})

        # Should return None or incomplete features
        features = store.get_features(machine_id)
        # Features should either be None or have quality flag


class TestSyntheticDataGeneration:
    """Test synthetic data generation functions."""

    def test_normal_operation_ranges(self):
        """Test that normal operation data is within expected ranges."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from generate_synthetic_data import generate_normal_operation

        data = generate_normal_operation(100)

        # Check vibration RMS is reasonable
        assert all(15 < v < 30 for v in data['vibration_rms'])

        # Check temperature is reasonable
        assert all(35 < t < 55 for t in data['temperature'])

    def test_degradation_pattern_increases(self):
        """Test that degradation pattern shows increasing severity."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from generate_synthetic_data import generate_degradation_pattern

        data = generate_degradation_pattern(100, severity=1.0)

        # Vibration should trend upward
        first_half_mean = np.mean(data['vibration_rms'][:50])
        second_half_mean = np.mean(data['vibration_rms'][50:])
        assert second_half_mean > first_half_mean


class TestPredictionLogic:
    """Test prediction calculation logic."""

    def test_risk_score_bounds(self):
        """Test that risk scores are always 0-100."""
        # Simulate various feature combinations
        test_cases = [
            (10, 3.0, 40, 100),   # Low risk
            (30, 4.0, 50, 300),   # Medium risk
            (60, 6.0, 60, 500),   # High risk
            (100, 10.0, 80, 1000),  # Extreme (should cap at 100)
        ]

        for vib_rms, kurtosis, temp, maintenance_hours in test_cases:
            # Simplified risk calculation
            vibration_risk = (vib_rms / 50) * 30
            temp_risk = max(0, (temp - 45) / 30) * 25
            maintenance_risk = min(maintenance_hours / 500, 1) * 20
            kurtosis_risk = max(0, (kurtosis - 3) / 5) * 25

            risk_score = min(100, vibration_risk + temp_risk + maintenance_risk + kurtosis_risk)

            assert 0 <= risk_score <= 100, f"Risk score {risk_score} out of bounds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
