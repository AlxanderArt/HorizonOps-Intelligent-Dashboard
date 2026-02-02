"""
Feature Store Service
Real-time feature engineering for predictive maintenance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger("aegisops.features")


@dataclass
class FeatureWindow:
    """Configuration for rolling window features."""
    name: str
    window_minutes: int
    aggregation: str  # 'mean', 'std', 'max', 'min', 'rms', 'kurtosis'


class FeatureStore:
    """
    Real-time feature engineering service.

    Computes rolling window features from raw telemetry for ML inference.
    Designed for low-latency production serving.
    """

    # Feature window configurations
    WINDOW_CONFIGS = [
        FeatureWindow('vibration_rms_5m', 5, 'rms'),
        FeatureWindow('vibration_rms_1h', 60, 'rms'),
        FeatureWindow('vibration_peak_5m', 5, 'max'),
        FeatureWindow('vibration_kurtosis_1h', 60, 'kurtosis'),
        FeatureWindow('temp_mean_15m', 15, 'mean'),
        FeatureWindow('temp_rate_15m', 15, 'rate'),
        FeatureWindow('power_mean_1h', 60, 'mean'),
        FeatureWindow('power_std_1h', 60, 'std'),
    ]

    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.telemetry_buffer: Dict[str, List[dict]] = {}
        self.feature_cache: Dict[str, dict] = {}
        self.last_update: Dict[str, datetime] = {}

    def ingest(self, machine_id: str, reading: dict):
        """
        Ingest a telemetry reading and update feature cache.

        Args:
            machine_id: Machine identifier
            reading: Raw sensor reading dict
        """
        if machine_id not in self.telemetry_buffer:
            self.telemetry_buffer[machine_id] = []

        # Add timestamp if not present
        if 'timestamp' not in reading:
            reading['timestamp'] = datetime.utcnow()

        self.telemetry_buffer[machine_id].append(reading)

        # Maintain buffer size
        if len(self.telemetry_buffer[machine_id]) > self.buffer_size:
            self.telemetry_buffer[machine_id] = self.telemetry_buffer[machine_id][-self.buffer_size:]

        # Update feature cache
        self._update_features(machine_id)
        self.last_update[machine_id] = datetime.utcnow()

    def get_features(self, machine_id: str) -> Optional[dict]:
        """
        Get current feature vector for a machine.

        Returns:
            Feature dictionary ready for model inference, or None if insufficient data
        """
        if machine_id not in self.feature_cache:
            return None

        features = self.feature_cache[machine_id].copy()
        features['feature_timestamp'] = datetime.utcnow().isoformat()
        features['data_quality'] = self._assess_data_quality(machine_id)

        return features

    def _update_features(self, machine_id: str):
        """Compute features from buffer and update cache."""
        buffer = self.telemetry_buffer.get(machine_id, [])

        if len(buffer) < 10:  # Minimum samples needed
            return

        df = pd.DataFrame(buffer)

        # Ensure timestamp column
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

        features = {}

        # Compute vibration features
        if 'vibration' in df.columns or 'vibration_rms' in df.columns:
            vib_col = 'vibration' if 'vibration' in df.columns else 'vibration_rms'
            features['vibration_rms'] = self._compute_rms(df[vib_col].tail(60))
            features['vibration_peak'] = df[vib_col].tail(60).max()
            features['vibration_kurtosis'] = self._compute_kurtosis(df[vib_col].tail(720))

        # Temperature features
        if 'temperature' in df.columns or 'temp' in df.columns:
            temp_col = 'temperature' if 'temperature' in df.columns else 'temp'
            features['temperature'] = df[temp_col].tail(180).mean()
            features['temp_rate_of_change'] = self._compute_rate(df[temp_col].tail(180))

        # Power features
        if 'power' in df.columns or 'power_consumption' in df.columns:
            power_col = 'power' if 'power' in df.columns else 'power_consumption'
            features['power_consumption'] = df[power_col].tail(720).mean()
            baseline_power = 12.0  # Assumed baseline
            features['power_deviation'] = ((features['power_consumption'] - baseline_power) / baseline_power) * 100

        # Operational context (these would come from external systems)
        features['time_since_maintenance'] = self._get_time_since_maintenance(machine_id)
        features['cumulative_cycles'] = self._get_cumulative_cycles(machine_id)
        features['hour_of_day'] = datetime.utcnow().hour
        features['day_of_week'] = datetime.utcnow().weekday()

        self.feature_cache[machine_id] = features

    def _compute_rms(self, series: pd.Series) -> float:
        """Compute root mean square."""
        return np.sqrt(np.mean(series ** 2))

    def _compute_kurtosis(self, series: pd.Series) -> float:
        """Compute kurtosis (peakedness of distribution)."""
        if len(series) < 4:
            return 3.0  # Normal distribution kurtosis
        return float(series.kurtosis()) + 3  # Convert to excess kurtosis

    def _compute_rate(self, series: pd.Series) -> float:
        """Compute rate of change (slope)."""
        if len(series) < 2:
            return 0.0
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series, 1)
        return float(slope)

    def _get_time_since_maintenance(self, machine_id: str) -> float:
        """Get hours since last maintenance (would query maintenance DB)."""
        # Simulated - in production would query maintenance database
        return np.random.uniform(100, 500)

    def _get_cumulative_cycles(self, machine_id: str) -> int:
        """Get cumulative machine cycles (would query MES)."""
        # Simulated - in production would query MES system
        return np.random.randint(80000, 150000)

    def _assess_data_quality(self, machine_id: str) -> dict:
        """Assess quality of available data."""
        buffer = self.telemetry_buffer.get(machine_id, [])

        return {
            'buffer_size': len(buffer),
            'sufficient_data': len(buffer) >= 60,
            'last_update': self.last_update.get(machine_id, datetime.min).isoformat(),
            'staleness_seconds': (datetime.utcnow() - self.last_update.get(machine_id, datetime.utcnow())).total_seconds()
        }

    def get_feature_statistics(self, machine_id: str, hours: int = 24) -> dict:
        """Get statistical summary of features over time window."""
        buffer = self.telemetry_buffer.get(machine_id, [])

        if not buffer:
            return {"error": "No data available"}

        df = pd.DataFrame(buffer)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        stats = {}
        for col in numeric_cols:
            stats[col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'current': float(df[col].iloc[-1])
            }

        return stats

    def clear_cache(self, machine_id: Optional[str] = None):
        """Clear feature cache for a machine or all machines."""
        if machine_id:
            self.feature_cache.pop(machine_id, None)
            self.telemetry_buffer.pop(machine_id, None)
        else:
            self.feature_cache.clear()
            self.telemetry_buffer.clear()


# Global feature store instance
feature_store = FeatureStore()
