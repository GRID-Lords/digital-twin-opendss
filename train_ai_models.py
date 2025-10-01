#!/usr/bin/env python3
"""
Train AI/ML models with synthetic historical data
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

sys.path.insert(0, '/root/opendss-test')
from src.models.ai_ml_models import SubstationAnomalyDetector, SubstationPredictiveModel, SubstationAIManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_training_data(num_samples=5000):
    """Generate synthetic training data for AI models"""

    logger.info(f"Generating {num_samples} training samples...")

    data = []
    asset_types = ['Power Transformer', 'Circuit Breaker', 'Current Transformer',
                   'Voltage Transformer', 'Lightning Arrester']

    base_time = datetime.now() - timedelta(days=90)  # 90 days of history

    for i in range(num_samples):
        # Random timestamp within 90 days
        timestamp = base_time + timedelta(seconds=np.random.randint(0, 90*24*3600))

        # Random asset type
        asset_type = np.random.choice(asset_types)

        # Generate realistic operational data based on asset type
        if asset_type == 'Power Transformer':
            voltage = 400 + np.random.normal(0, 5)  # 400kV ± 5kV
            current = 200 + np.random.normal(0, 20)  # 200A ± 20A
            power = voltage * current / 1000  # MW
            temperature = 65 + np.random.normal(0, 10)  # 65°C ± 10°C
            health_score = 90 - (temperature - 65) * 0.5 + np.random.normal(0, 5)

        elif asset_type == 'Circuit Breaker':
            voltage = 400 + np.random.normal(0, 3)
            current = 150 + np.random.normal(0, 15)
            power = voltage * current / 1000
            temperature = 45 + np.random.normal(0, 8)
            health_score = 95 - np.random.exponential(5)

        elif asset_type == 'Current Transformer':
            voltage = 400 + np.random.normal(0, 2)
            current = 100 + np.random.normal(0, 10)
            power = voltage * current / 1000
            temperature = 40 + np.random.normal(0, 5)
            health_score = 92 + np.random.normal(0, 6)

        elif asset_type == 'Voltage Transformer':
            voltage = 400 + np.random.normal(0, 3)
            current = 10 + np.random.normal(0, 2)
            power = voltage * current / 1000
            temperature = 38 + np.random.normal(0, 5)
            health_score = 94 + np.random.normal(0, 4)

        else:  # Lightning Arrester
            voltage = 400 + np.random.normal(0, 5)
            current = 5 + np.random.normal(0, 1)
            power = voltage * current / 1000
            temperature = 35 + np.random.normal(0, 3)
            health_score = 96 + np.random.normal(0, 3)

        # Ensure health score is in valid range
        health_score = np.clip(health_score, 30, 100)

        # Add some anomalies (10% of data)
        if np.random.random() < 0.1:
            temperature += np.random.uniform(15, 30)  # High temperature anomaly
            health_score -= np.random.uniform(10, 30)  # Low health anomaly
            current *= np.random.uniform(1.3, 1.8)  # Overcurrent anomaly

        # Calculate age in days (0-3650 days = 0-10 years)
        age_days = np.random.uniform(0, 3650)

        # Add degradation over time
        health_score -= age_days / 365 * 2  # 2% degradation per year
        health_score = np.clip(health_score, 30, 100)

        data.append({
            'timestamp': timestamp,
            'asset_id': f'{asset_type[:3].upper()}_{i % 20 + 1}',
            'asset_type': asset_type,
            'voltage': voltage,
            'current': current,
            'power': power,
            'temperature': temperature,
            'health_score': health_score,
            'age_days': age_days
        })

    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} training samples")
    logger.info(f"Asset types: {df['asset_type'].value_counts().to_dict()}")
    logger.info(f"Health score range: {df['health_score'].min():.1f} - {df['health_score'].max():.1f}")

    return df

def train_models():
    """Train all AI models"""

    logger.info("=" * 60)
    logger.info("Starting AI/ML Model Training")
    logger.info("=" * 60)

    # Generate training data
    training_data = generate_training_data(num_samples=5000)

    # Initialize models
    anomaly_detector = SubstationAnomalyDetector()
    predictive_model = SubstationPredictiveModel()

    # Train anomaly detection
    logger.info("\n1. Training Anomaly Detection Models...")
    try:
        anomaly_detector.train(training_data)
        logger.info("✓ Anomaly detection models trained successfully")
    except Exception as e:
        logger.error(f"✗ Error training anomaly detector: {e}")
        return False

    # Train predictive maintenance
    logger.info("\n2. Training Predictive Maintenance Models...")
    try:
        predictive_model.train(training_data)
        logger.info("✓ Predictive maintenance models trained successfully")
    except Exception as e:
        logger.error(f"✗ Error training predictive model: {e}")
        return False

    # Save models
    logger.info("\n3. Saving trained models...")
    try:
        import joblib
        joblib.dump(anomaly_detector, 'models/anomaly_detector.pkl')
        joblib.dump(predictive_model, 'models/predictive_maintenance.pkl')
        logger.info("✓ Models saved to 'models/' directory")
    except Exception as e:
        logger.error(f"✗ Error saving models: {e}")
        logger.info("⚠ Models trained but not saved to disk")

    # Test models with sample data
    logger.info("\n4. Testing Models...")
    test_data = {
        'PowerTransformer_T1': {
            'asset_type': 'Power Transformer',
            'voltage': 402.5,
            'current': 215.3,
            'power': 86.7,
            'temperature': 75.2,
            'health_score': 82.5,
            'age_days': 1825
        }
    }

    # Test anomaly detection
    anomalies = anomaly_detector.detect_anomalies(test_data)
    logger.info(f"Anomalies detected: {len(anomalies)}")

    # Test predictive maintenance
    predictions = predictive_model.predict_health_degradation(test_data)
    logger.info(f"Health predictions: {len(predictions)}")
    if predictions:
        pred = predictions[0]
        logger.info(f"  Asset: {pred['asset_id']}")
        logger.info(f"  Current Health: {pred['current_health']:.1f}%")
        logger.info(f"  Predicted Health: {pred['predicted_health']:.1f}%")
        logger.info(f"  Urgency: {pred['urgency']}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ AI/ML Model Training Complete!")
    logger.info("=" * 60)

    return True

if __name__ == "__main__":
    import os
    os.makedirs('models', exist_ok=True)
    success = train_models()
    sys.exit(0 if success else 1)
