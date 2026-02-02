"""
Synthetic Data Generator for AegisOps
Generates realistic manufacturing telemetry with failure events
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegisops.datagen")

# Configuration
NUM_MACHINES = 8
DAYS_OF_DATA = 180
SAMPLES_PER_DAY = 288  # 5-minute intervals
FAILURE_RATE = 0.02  # ~2% of days have failures

MACHINES = [
    "CNC-ALPHA-921", "CNC-ALPHA-922",
    "CNC-BETA-101", "CNC-BETA-102",
    "MILL-GAMMA-301", "MILL-GAMMA-302",
    "LATHE-DELTA-401", "LATHE-DELTA-402"
]


def generate_normal_operation(n_samples: int) -> dict:
    """Generate telemetry for normal machine operation."""
    return {
        'vibration_rms': np.random.normal(20, 2, n_samples),
        'vibration_peak': np.random.normal(35, 5, n_samples),
        'vibration_kurtosis': np.random.normal(3.2, 0.3, n_samples),
        'temperature': np.random.normal(44, 2, n_samples),
        'temp_rate_of_change': np.random.normal(0, 0.5, n_samples),
        'power_consumption': np.random.normal(12, 0.5, n_samples),
        'power_deviation': np.random.normal(0, 2, n_samples),
    }


def generate_degradation_pattern(n_samples: int, severity: float = 1.0) -> dict:
    """
    Generate telemetry showing degradation leading to failure.

    Patterns based on real bearing degradation signatures:
    - Vibration kurtosis increases (impulsive vibration)
    - RMS vibration trends upward
    - Temperature rises
    """
    progress = np.linspace(0, 1, n_samples) * severity

    return {
        'vibration_rms': 20 + progress * 35 + np.random.normal(0, 3, n_samples),
        'vibration_peak': 35 + progress * 50 + np.random.normal(0, 8, n_samples),
        'vibration_kurtosis': 3.2 + progress * 4 + np.random.normal(0, 0.5, n_samples),
        'temperature': 44 + progress * 15 + np.random.normal(0, 2, n_samples),
        'temp_rate_of_change': progress * 2 + np.random.normal(0, 0.3, n_samples),
        'power_consumption': 12 + progress * 3 + np.random.normal(0, 0.5, n_samples),
        'power_deviation': progress * 15 + np.random.normal(0, 3, n_samples),
    }


def generate_machine_data(machine_id: str, start_date: datetime) -> pd.DataFrame:
    """Generate complete telemetry history for a single machine."""
    logger.info(f"Generating data for {machine_id}...")

    all_data = []
    current_date = start_date
    time_since_maintenance = 0
    cumulative_cycles = np.random.randint(50000, 150000)

    # Track failure events for this machine
    failure_windows = []

    # Decide on failure events
    for day in range(DAYS_OF_DATA):
        if np.random.random() < FAILURE_RATE:
            # Schedule a failure event
            degradation_start = day - np.random.randint(2, 5)  # 2-5 days before
            failure_windows.append((max(0, degradation_start), day))

    for day in range(DAYS_OF_DATA):
        day_date = current_date + timedelta(days=day)

        # Check if we're in a degradation window
        in_degradation = False
        days_until_failure = None
        for start, end in failure_windows:
            if start <= day <= end:
                in_degradation = True
                days_until_failure = end - day
                break

        # Generate day's data
        if in_degradation and days_until_failure is not None:
            # Calculate degradation severity
            severity = 1 - (days_until_failure / 5)
            day_telemetry = generate_degradation_pattern(SAMPLES_PER_DAY, severity)
        else:
            day_telemetry = generate_normal_operation(SAMPLES_PER_DAY)

        # Create timestamps for day
        timestamps = [
            day_date + timedelta(minutes=5 * i)
            for i in range(SAMPLES_PER_DAY)
        ]

        # Add operational context
        for i, ts in enumerate(timestamps):
            sample = {
                'timestamp': ts,
                'machine_id': machine_id,
                'vibration_rms': max(0, day_telemetry['vibration_rms'][i]),
                'vibration_peak': max(0, day_telemetry['vibration_peak'][i]),
                'vibration_kurtosis': max(2, day_telemetry['vibration_kurtosis'][i]),
                'temperature': max(20, day_telemetry['temperature'][i]),
                'temp_rate_of_change': day_telemetry['temp_rate_of_change'][i],
                'power_consumption': max(5, day_telemetry['power_consumption'][i]),
                'power_deviation': day_telemetry['power_deviation'][i],
                'time_since_maintenance': time_since_maintenance + i * (5 / 60),
                'cumulative_cycles': cumulative_cycles + i * np.random.randint(1, 5),
                'hour_of_day': ts.hour,
                'day_of_week': ts.weekday(),
                'failure_within_72h': 1 if (in_degradation and days_until_failure <= 3) else 0,
                'failure_event': 1 if (in_degradation and days_until_failure == 0 and i > SAMPLES_PER_DAY - 10) else 0
            }
            all_data.append(sample)

        # Simulate maintenance resets
        if day_telemetry['vibration_rms'].mean() > 50 or np.random.random() < 0.01:
            time_since_maintenance = 0
        else:
            time_since_maintenance += 24

        cumulative_cycles += SAMPLES_PER_DAY * 3

    return pd.DataFrame(all_data)


def generate_maintenance_logs(machines_data: pd.DataFrame) -> pd.DataFrame:
    """Generate maintenance event logs from telemetry data."""
    logs = []

    for machine_id in MACHINES:
        machine_data = machines_data[machines_data['machine_id'] == machine_id]
        failure_events = machine_data[machine_data['failure_event'] == 1]

        for _, event in failure_events.iterrows():
            logs.append({
                'event_id': f"MNT-{np.random.randint(10000, 99999)}",
                'machine_id': machine_id,
                'timestamp': event['timestamp'],
                'event_type': 'corrective',
                'component': np.random.choice(['spindle_bearing', 'drive_belt', 'coolant_pump', 'encoder']),
                'severity': np.random.choice(['critical', 'high', 'medium']),
                'downtime_hours': np.random.uniform(2, 12),
                'root_cause': np.random.choice(['bearing_wear', 'misalignment', 'contamination', 'fatigue'])
            })

        # Add preventive maintenance events
        for month in range(6):
            logs.append({
                'event_id': f"PM-{np.random.randint(10000, 99999)}",
                'machine_id': machine_id,
                'timestamp': machines_data['timestamp'].min() + timedelta(days=30 * month),
                'event_type': 'preventive',
                'component': 'general',
                'severity': 'routine',
                'downtime_hours': 4,
                'root_cause': 'scheduled_pm'
            })

    return pd.DataFrame(logs)


def main():
    """Generate complete synthetic dataset."""
    logger.info("Starting synthetic data generation...")

    output_dir = Path(__file__).parent.parent / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)

    start_date = datetime(2024, 1, 1)

    # Generate telemetry for all machines
    all_machine_data = []
    for machine_id in MACHINES:
        machine_data = generate_machine_data(machine_id, start_date)
        all_machine_data.append(machine_data)

    telemetry_df = pd.concat(all_machine_data, ignore_index=True)

    # Generate maintenance logs
    maintenance_df = generate_maintenance_logs(telemetry_df)

    # Save datasets
    telemetry_path = output_dir / "telemetry_data.csv"
    training_path = output_dir / "training_data.csv"
    maintenance_path = output_dir / "maintenance_logs.csv"

    telemetry_df.to_csv(telemetry_path, index=False)
    telemetry_df.to_csv(training_path, index=False)  # Same as training data
    maintenance_df.to_csv(maintenance_path, index=False)

    # Print summary
    logger.info(f"\nData Generation Complete!")
    logger.info(f"=" * 50)
    logger.info(f"Telemetry records: {len(telemetry_df):,}")
    logger.info(f"Maintenance events: {len(maintenance_df):,}")
    logger.info(f"Failure events: {telemetry_df['failure_event'].sum():,}")
    logger.info(f"Positive samples (72h): {telemetry_df['failure_within_72h'].sum():,}")
    logger.info(f"Class balance: {telemetry_df['failure_within_72h'].mean():.2%} positive")
    logger.info(f"\nFiles saved to: {output_dir}")

    # Summary statistics
    print("\n" + "=" * 50)
    print("FEATURE STATISTICS")
    print("=" * 50)
    feature_cols = ['vibration_rms', 'vibration_peak', 'vibration_kurtosis',
                    'temperature', 'power_consumption']
    print(telemetry_df[feature_cols].describe().round(2))


if __name__ == "__main__":
    main()
