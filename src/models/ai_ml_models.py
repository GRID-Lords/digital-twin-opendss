#!/usr/bin/env python3
"""
AI/ML Models for Indian EHV Substation Digital Twin
Anomaly detection, failure prediction, and optimization
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, classification_report
import joblib
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class SubstationAnomalyDetector:
    """Anomaly detection for substation assets"""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.thresholds = {}
        self.is_trained = False
        self.online_buffer = {}  # Buffer for online learning
        self.buffer_size = 100  # Retrain after 100 new samples per asset type
    
    def train(self, historical_data: pd.DataFrame):
        """Train anomaly detection models"""
        try:
            # Features for anomaly detection
            features = ['voltage', 'current', 'power', 'temperature', 'health_score']
            
            for asset_type in historical_data['asset_type'].unique():
                asset_data = historical_data[historical_data['asset_type'] == asset_type]
                
                if len(asset_data) < 100:  # Need sufficient data
                    continue
                
                # Prepare features
                X = asset_data[features].fillna(0)
                
                # Train Isolation Forest
                model = IsolationForest(
                    contamination=0.1,  # 10% anomaly rate
                    random_state=42,
                    n_estimators=100
                )
                model.fit(X)
                
                # Train scaler
                scaler = StandardScaler()
                scaler.fit(X)
                
                # Calculate threshold
                scores = model.decision_function(X)
                threshold = np.percentile(scores, 10)  # Bottom 10% as anomalies
                
                self.models[asset_type] = model
                self.scalers[asset_type] = scaler
                self.thresholds[asset_type] = threshold
                
                logger.info(f"Trained anomaly detector for {asset_type}")
            
            self.is_trained = True
            logger.info("Anomaly detection models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}")
            raise
    
    def detect_anomalies(self, current_data: Dict[str, Dict]) -> List[Dict]:
        """Detect anomalies in current asset data"""
        anomalies = []
        
        if not self.is_trained:
            return anomalies
        
        for asset_id, asset_data in current_data.items():
            asset_type = asset_data.get('asset_type')
            
            if asset_type not in self.models:
                continue
            
            try:
                # Prepare features
                features = ['voltage', 'current', 'power', 'temperature', 'health_score']
                X = np.array([[asset_data.get(f, 0) for f in features]]).reshape(1, -1)
                
                # Scale features
                X_scaled = self.scalers[asset_type].transform(X)
                
                # Predict anomaly
                score = self.models[asset_type].decision_function(X_scaled)[0]
                is_anomaly = score < self.thresholds[asset_type]
                
                if is_anomaly:
                    anomaly = {
                        'asset_id': asset_id,
                        'asset_type': asset_type,
                        'anomaly_score': float(score),
                        'severity': 'high' if score < self.thresholds[asset_type] * 0.5 else 'medium',
                        'timestamp': datetime.now().isoformat(),
                        'features': {f: asset_data.get(f, 0) for f in features}
                    }
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting anomaly for {asset_id}: {e}")

        return anomalies

    def update_with_new_data(self, asset_type: str, features_dict: Dict):
        """Add new observation to buffer and retrain if buffer is full"""
        if asset_type not in self.online_buffer:
            self.online_buffer[asset_type] = []

        # Add to buffer
        self.online_buffer[asset_type].append(features_dict)

        # Check if we should retrain
        if len(self.online_buffer[asset_type]) >= self.buffer_size:
            logger.info(f"Buffer full for {asset_type}, retraining anomaly detector...")

            # Convert buffer to DataFrame
            buffer_df = pd.DataFrame(self.online_buffer[asset_type])
            buffer_df['asset_type'] = asset_type

            # Retrain with buffered data
            self._retrain_single_type(asset_type, buffer_df)

            # Clear buffer but keep last 20% for continuity
            keep_size = int(self.buffer_size * 0.2)
            self.online_buffer[asset_type] = self.online_buffer[asset_type][-keep_size:]

    def _retrain_single_type(self, asset_type: str, new_data: pd.DataFrame):
        """Retrain model for a specific asset type"""
        try:
            features = ['voltage', 'current', 'power', 'temperature', 'health_score']
            X = new_data[features].fillna(0)

            if len(X) < 50:  # Need minimum data
                logger.warning(f"Insufficient data for retraining {asset_type}")
                return

            # Retrain Isolation Forest
            model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            model.fit(X)

            # Update scaler
            scaler = StandardScaler()
            scaler.fit(X)

            # Recalculate threshold
            scores = model.decision_function(X)
            threshold = np.percentile(scores, 10)

            # Update models
            self.models[asset_type] = model
            self.scalers[asset_type] = scaler
            self.thresholds[asset_type] = threshold

            logger.info(f"Successfully retrained anomaly detector for {asset_type}")

        except Exception as e:
            logger.error(f"Error retraining anomaly detector for {asset_type}: {e}")

class SubstationPredictiveModel:
    """Predictive maintenance model for substation assets"""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.is_trained = False
        self.online_buffer = {}  # Buffer for online learning
        self.buffer_size = 200  # Retrain after 200 new samples per asset type
    
    def train(self, historical_data: pd.DataFrame):
        """Train predictive maintenance models"""
        try:
            # Features for prediction
            features = ['voltage', 'current', 'power', 'temperature', 'age_days']
            target = 'health_score'
            
            for asset_type in historical_data['asset_type'].unique():
                asset_data = historical_data[historical_data['asset_type'] == asset_type]
                
                if len(asset_data) < 200:  # Need sufficient data
                    continue
                
                # Prepare features and target
                X = asset_data[features].fillna(0)
                y = asset_data[target]
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Train Random Forest
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                model.fit(X_train, y_train)
                
                # Train scaler
                scaler = StandardScaler()
                scaler.fit(X_train)
                
                # Evaluate model
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                
                # Store feature importance
                feature_importance = dict(zip(features, model.feature_importances_))
                
                self.models[asset_type] = model
                self.scalers[asset_type] = scaler
                self.feature_importance[asset_type] = feature_importance
                
                logger.info(f"Trained predictive model for {asset_type} (MSE: {mse:.2f})")
            
            self.is_trained = True
            logger.info("Predictive maintenance models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training predictive model: {e}")
            raise
    
    def predict_health_degradation(self, current_data: Dict[str, Dict]) -> List[Dict]:
        """Predict health degradation for assets"""
        predictions = []
        
        if not self.is_trained:
            return predictions
        
        for asset_id, asset_data in current_data.items():
            asset_type = asset_data.get('asset_type')
            
            if asset_type not in self.models:
                continue
            
            try:
                # Prepare features
                features = ['voltage', 'current', 'power', 'temperature', 'age_days']
                X = np.array([[asset_data.get(f, 0) for f in features]]).reshape(1, -1)
                
                # Scale features
                X_scaled = self.scalers[asset_type].transform(X)
                
                # Predict health score
                predicted_health = self.models[asset_type].predict(X_scaled)[0]
                current_health = asset_data.get('health_score', 100)
                
                # Calculate degradation rate
                degradation_rate = (current_health - predicted_health) / 30  # per 30 days
                
                # Determine maintenance urgency
                if predicted_health < 50:
                    urgency = 'critical'
                elif predicted_health < 70:
                    urgency = 'high'
                elif predicted_health < 85:
                    urgency = 'medium'
                else:
                    urgency = 'low'
                
                prediction = {
                    'asset_id': asset_id,
                    'asset_type': asset_type,
                    'current_health': float(current_health),
                    'predicted_health': float(predicted_health),
                    'degradation_rate': float(degradation_rate),
                    'urgency': urgency,
                    'maintenance_window': self._calculate_maintenance_window(predicted_health),
                    'timestamp': datetime.now().isoformat()
                }
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error predicting health for {asset_id}: {e}")
        
        return predictions
    
    def _calculate_maintenance_window(self, predicted_health: float) -> str:
        """Calculate recommended maintenance window"""
        if predicted_health < 50:
            return "immediate"
        elif predicted_health < 70:
            return "within_7_days"
        elif predicted_health < 85:
            return "within_30_days"
        else:
            return "within_90_days"

    def update_with_new_data(self, asset_type: str, features_dict: Dict, health_score: float):
        """Add new observation to buffer and retrain if buffer is full"""
        if asset_type not in self.online_buffer:
            self.online_buffer[asset_type] = []

        # Add health score to features
        features_dict['health_score'] = health_score

        # Add to buffer
        self.online_buffer[asset_type].append(features_dict)

        # Check if we should retrain
        if len(self.online_buffer[asset_type]) >= self.buffer_size:
            logger.info(f"Buffer full for {asset_type}, retraining predictive model...")

            # Convert buffer to DataFrame
            buffer_df = pd.DataFrame(self.online_buffer[asset_type])
            buffer_df['asset_type'] = asset_type

            # Retrain with buffered data
            self._retrain_single_type(asset_type, buffer_df)

            # Clear buffer but keep last 20% for continuity
            keep_size = int(self.buffer_size * 0.2)
            self.online_buffer[asset_type] = self.online_buffer[asset_type][-keep_size:]

    def _retrain_single_type(self, asset_type: str, new_data: pd.DataFrame):
        """Retrain model for a specific asset type"""
        try:
            features = ['voltage', 'current', 'power', 'temperature', 'age_days']
            target = 'health_score'

            X = new_data[features].fillna(0)
            y = new_data[target]

            if len(X) < 100:  # Need minimum data
                logger.warning(f"Insufficient data for retraining {asset_type}")
                return

            # Retrain Random Forest
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X, y)

            # Update scaler
            scaler = StandardScaler()
            scaler.fit(X)

            # Update feature importance
            feature_importance = dict(zip(features, model.feature_importances_))

            # Update models
            self.models[asset_type] = model
            self.scalers[asset_type] = scaler
            self.feature_importance[asset_type] = feature_importance

            logger.info(f"Successfully retrained predictive model for {asset_type}")

        except Exception as e:
            logger.error(f"Error retraining predictive model for {asset_type}: {e}")

class SubstationOptimizer:
    """Optimization model for substation operations"""
    
    def __init__(self):
        self.optimization_history = []
    
    def optimize_power_flow(self, current_state: Dict) -> Dict:
        """Optimize power flow for maximum efficiency"""
        try:
            # Get current metrics
            total_power = current_state.get('total_power', 0)
            efficiency = current_state.get('efficiency', 0)
            voltage_stability = current_state.get('voltage_stability', 0)
            
            # Optimization parameters
            target_efficiency = 95.0
            target_voltage_stability = 98.0
            
            # Calculate optimization recommendations
            recommendations = []
            
            if efficiency < target_efficiency:
                recommendations.append({
                    'type': 'efficiency',
                    'action': 'adjust_transformer_taps',
                    'priority': 'high',
                    'description': f'Current efficiency {efficiency:.1f}% is below target {target_efficiency}%'
                })
            
            if voltage_stability < target_voltage_stability:
                recommendations.append({
                    'type': 'voltage_stability',
                    'action': 'adjust_capacitor_banks',
                    'priority': 'medium',
                    'description': f'Voltage stability {voltage_stability:.1f}% is below target {target_voltage_stability}%'
                })
            
            # Load balancing recommendations
            if total_power > 0:
                recommendations.append({
                    'type': 'load_balancing',
                    'action': 'redistribute_load',
                    'priority': 'low',
                    'description': 'Consider load redistribution for optimal efficiency'
                })
            
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'current_efficiency': efficiency,
                'target_efficiency': target_efficiency,
                'current_voltage_stability': voltage_stability,
                'target_voltage_stability': target_voltage_stability,
                'recommendations': recommendations,
                'optimization_score': self._calculate_optimization_score(efficiency, voltage_stability)
            }
            
            self.optimization_history.append(optimization_result)
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error in power flow optimization: {e}")
            return {}
    
    def _calculate_optimization_score(self, efficiency: float, voltage_stability: float) -> float:
        """Calculate overall optimization score"""
        efficiency_score = min(100, (efficiency / 95.0) * 100)
        stability_score = min(100, (voltage_stability / 98.0) * 100)
        return (efficiency_score + stability_score) / 2
    
    def optimize_maintenance_schedule(self, asset_predictions: List[Dict]) -> Dict:
        """Optimize maintenance schedule based on predictions"""
        try:
            # Group assets by urgency
            critical_assets = [a for a in asset_predictions if a['urgency'] == 'critical']
            high_priority_assets = [a for a in asset_predictions if a['urgency'] == 'high']
            medium_priority_assets = [a for a in asset_predictions if a['urgency'] == 'medium']
            
            # Create maintenance schedule
            schedule = {
                'immediate': critical_assets,
                'within_7_days': high_priority_assets,
                'within_30_days': medium_priority_assets,
                'total_assets': len(asset_predictions),
                'critical_count': len(critical_assets),
                'high_priority_count': len(high_priority_assets),
                'medium_priority_count': len(medium_priority_assets)
            }
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error optimizing maintenance schedule: {e}")
            return {}

class SubstationAIManager:
    """Main AI/ML manager for the digital twin"""

    def __init__(self, model_dir: str = "models"):
        self.anomaly_detector = SubstationAnomalyDetector()
        self.predictive_model = SubstationPredictiveModel()
        self.optimizer = SubstationOptimizer()
        self.is_initialized = False
        self.model_dir = model_dir

        # Try to load pre-trained models
        self.load_pretrained_models()

    def load_pretrained_models(self):
        """Load pre-trained models from disk if available"""
        import os

        try:
            anomaly_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
            predictive_path = os.path.join(self.model_dir, 'predictive_maintenance.pkl')

            # Load anomaly detector
            if os.path.exists(anomaly_path):
                logger.info(f"📦 Loading pre-trained anomaly detector from {anomaly_path}")
                self.anomaly_detector = joblib.load(anomaly_path)
                logger.info(f"✅ Loaded anomaly detector with {len(self.anomaly_detector.models)} asset type models")
                self.is_initialized = True
            else:
                logger.info("⚠️ No pre-trained anomaly detector found")

            # Load predictive model
            if os.path.exists(predictive_path):
                logger.info(f"📦 Loading pre-trained predictive model from {predictive_path}")
                self.predictive_model = joblib.load(predictive_path)
                logger.info(f"✅ Loaded predictive model with {len(self.predictive_model.models)} asset type models")
                self.is_initialized = True
            else:
                logger.info("⚠️ No pre-trained predictive model found")

            if self.is_initialized:
                logger.info("🎯 Pre-trained AI models loaded successfully")

        except Exception as e:
            logger.warning(f"⚠️ Could not load pre-trained models: {e}")
            logger.info("Will use synthetic training data instead")

    def save_models(self):
        """Save trained models to disk"""
        import os

        try:
            os.makedirs(self.model_dir, exist_ok=True)

            anomaly_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
            predictive_path = os.path.join(self.model_dir, 'predictive_maintenance.pkl')

            # Save anomaly detector
            if self.anomaly_detector.is_trained:
                joblib.dump(self.anomaly_detector, anomaly_path)
                logger.info(f"✅ Saved anomaly detector to {anomaly_path}")

            # Save predictive model
            if self.predictive_model.is_trained:
                joblib.dump(self.predictive_model, predictive_path)
                logger.info(f"✅ Saved predictive model to {predictive_path}")

            logger.info("💾 AI models saved successfully")

        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")

    def update_models_online(self, asset_id: str, asset_data: Dict):
        """Update models with new data point (online learning)"""
        try:
            asset_type = asset_data.get('asset_type')
            if not asset_type:
                return

            # Prepare features for anomaly detector
            anomaly_features = {
                'voltage': asset_data.get('voltage', 0),
                'current': asset_data.get('current', 0),
                'power': asset_data.get('power', 0),
                'temperature': asset_data.get('temperature', 0),
                'health_score': asset_data.get('health_score', 100)
            }

            # Update anomaly detector
            self.anomaly_detector.update_with_new_data(asset_type, anomaly_features)

            # Prepare features for predictive model
            predictive_features = {
                'voltage': asset_data.get('voltage', 0),
                'current': asset_data.get('current', 0),
                'power': asset_data.get('power', 0),
                'temperature': asset_data.get('temperature', 0),
                'age_days': asset_data.get('age_days', 0)
            }

            # Update predictive model
            self.predictive_model.update_with_new_data(
                asset_type,
                predictive_features,
                asset_data.get('health_score', 100)
            )

        except Exception as e:
            logger.error(f"Error in online learning update: {e}")

    def initialize_with_synthetic_data(self):
        """Initialize AI models with synthetic data for demonstration"""
        try:
            logger.info("🧠 Training AI/ML models with synthetic data...")
            
            # Generate synthetic historical data
            np.random.seed(42)
            n_samples = 2000  # Increased for better training
            
            synthetic_data = []
            asset_types = ['PowerTransformer', 'DistributionTransformer', 'CircuitBreaker', 'IndustrialLoad']
            
            for asset_type in asset_types:
                for i in range(n_samples // len(asset_types)):
                    # Generate realistic data with correlations
                    base_voltage = 400 if 'Power' in asset_type else 220 if 'Distribution' in asset_type else 12.47
                    voltage = base_voltage + np.random.normal(0, base_voltage * 0.05)
                    
                    base_current = 200 if 'Power' in asset_type else 150 if 'Distribution' in asset_type else 100
                    current = base_current + np.random.normal(0, base_current * 0.1)
                    
                    power = voltage * current * np.random.uniform(0.8, 1.0)
                    
                    # Temperature correlated with power and age
                    base_temp = 45 if 'Power' in asset_type else 50 if 'Distribution' in asset_type else 35
                    power_factor = min(1.0, power / 100000.0)  # Normalize power
                    temperature = base_temp + power_factor * 20 + np.random.normal(0, 5)
                    
                    age_days = np.random.uniform(0, 3650)  # 0-10 years
                    
                    # Health score decreases with age and temperature
                    age_factor = (age_days / 3650) * 20  # Up to 20% reduction
                    temp_factor = max(0, (temperature - 60) / 20) * 10  # Temperature penalty
                    health_score = max(0, min(100, 100 - age_factor - temp_factor + np.random.normal(0, 3)))
                    
                    synthetic_data.append({
                        'asset_id': f'{asset_type}_{i}',
                        'asset_type': asset_type,
                        'voltage': voltage,
                        'current': current,
                        'power': power,
                        'temperature': temperature,
                        'age_days': age_days,
                        'health_score': health_score,
                        'timestamp': datetime.now() - timedelta(days=np.random.uniform(0, 365))
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(synthetic_data)
            logger.info(f"Generated {len(df)} synthetic data points")
            
            # Train models
            logger.info("Training anomaly detection model...")
            self.anomaly_detector.train(df)
            
            logger.info("Training predictive maintenance model...")
            self.predictive_model.train(df)
            
            self.is_initialized = True
            logger.info("✅ AI/ML models trained successfully")
            
            # Log model performance
            self._log_model_performance()
            
        except Exception as e:
            logger.error(f"❌ Error training AI models: {e}")
            raise
    
    def _log_model_performance(self):
        """Log model performance metrics"""
        try:
            logger.info("📊 AI/ML Model Performance:")
            
            # Anomaly detector performance
            if self.anomaly_detector.is_trained:
                for asset_type, model in self.anomaly_detector.models.items():
                    logger.info(f"  • Anomaly Detector ({asset_type}): Trained with {len(model.estimators_)} trees")
            
            # Predictive model performance
            if self.predictive_model.is_trained:
                for asset_type, model in self.predictive_model.models.items():
                    feature_importance = self.predictive_model.feature_importance.get(asset_type, {})
                    logger.info(f"  • Predictive Model ({asset_type}): Trained with {len(model.estimators_)} trees")
                    if feature_importance:
                        top_feature = max(feature_importance.items(), key=lambda x: x[1])
                        logger.info(f"    - Most important feature: {top_feature[0]} ({top_feature[1]:.3f})")
            
            logger.info("🎯 Models ready for real-time analysis")
            
        except Exception as e:
            logger.warning(f"Could not log model performance: {e}")
    
    def train_with_historical_data(self, historical_data_path: str):
        """Train models with real historical data"""
        try:
            logger.info(f"📚 Loading historical data from {historical_data_path}")
            
            # Load historical data
            if historical_data_path.endswith('.csv'):
                df = pd.read_csv(historical_data_path)
            elif historical_data_path.endswith('.json'):
                df = pd.read_json(historical_data_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or JSON.")
            
            logger.info(f"Loaded {len(df)} historical records")
            
            # Validate required columns
            required_columns = ['asset_type', 'voltage', 'current', 'power', 'temperature', 'health_score']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Train models
            logger.info("Training anomaly detection model...")
            self.anomaly_detector.train(df)
            
            logger.info("Training predictive maintenance model...")
            self.predictive_model.train(df)
            
            self.is_initialized = True
            logger.info("✅ AI/ML models trained with historical data")
            
            # Log model performance
            self._log_model_performance()
            
        except Exception as e:
            logger.error(f"❌ Error training with historical data: {e}")
            raise
    
    def retrain_models(self, new_data: pd.DataFrame):
        """Retrain models with new data (online learning)"""
        try:
            logger.info("🔄 Retraining AI/ML models with new data...")
            
            # Combine with existing data if available
            if hasattr(self, '_training_data'):
                combined_data = pd.concat([self._training_data, new_data], ignore_index=True)
            else:
                combined_data = new_data
            
            # Keep only recent data (last 2 years)
            if 'timestamp' in combined_data.columns:
                combined_data['timestamp'] = pd.to_datetime(combined_data['timestamp'])
                cutoff_date = datetime.now() - timedelta(days=730)
                combined_data = combined_data[combined_data['timestamp'] >= cutoff_date]
            
            # Retrain models
            self.anomaly_detector.train(combined_data)
            self.predictive_model.train(combined_data)
            
            # Store for future retraining
            self._training_data = combined_data
            
            logger.info("✅ Models retrained successfully")
            
        except Exception as e:
            logger.error(f"❌ Error retraining models: {e}")
            raise
    
    def analyze_current_state(self, assets: Dict[str, Dict], metrics: Dict) -> Dict:
        """Run complete AI analysis on current state"""
        if not self.is_initialized:
            return {}
        
        try:
            # Anomaly detection
            anomalies = self.anomaly_detector.detect_anomalies(assets)
            
            # Predictive maintenance
            predictions = self.predictive_model.predict_health_degradation(assets)
            
            # Optimization
            optimization = self.optimizer.optimize_power_flow(metrics)
            maintenance_schedule = self.optimizer.optimize_maintenance_schedule(predictions)
            
            # Combine results
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'anomalies': anomalies,
                'predictions': predictions,
                'optimization': optimization,
                'maintenance_schedule': maintenance_schedule,
                'summary': {
                    'anomaly_count': len(anomalies),
                    'critical_assets': len([p for p in predictions if p['urgency'] == 'critical']),
                    'optimization_score': optimization.get('optimization_score', 0)
                }
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {}
    
    def save_models(self, filepath: str):
        """Save trained models to disk"""
        try:
            model_data = {
                'anomaly_detector': self.anomaly_detector,
                'predictive_model': self.predictive_model,
                'optimizer': self.optimizer
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Models saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk"""
        try:
            model_data = joblib.load(filepath)
            self.anomaly_detector = model_data['anomaly_detector']
            self.predictive_model = model_data['predictive_model']
            self.optimizer = model_data['optimizer']
            self.is_initialized = True
            logger.info(f"Models loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_synthetic_substation_data(n_days: int = 30) -> pd.DataFrame:
    """Generate synthetic data for training AI models"""
    np.random.seed(42)
    
    data = []
    base_date = datetime.now() - timedelta(days=n_days)
    
    for day in range(n_days):
        current_date = base_date + timedelta(days=day)
        
        # Generate hourly data
        for hour in range(24):
            timestamp = current_date + timedelta(hours=hour)
            
            # Simulate daily load pattern
            load_factor = 0.6 + 0.4 * np.sin(2 * np.pi * hour / 24)
            
            # Generate data for each asset type
            asset_data = {
                'PowerTransformer': {
                    'voltage': 400 + np.random.normal(0, 10),
                    'current': 200 * load_factor + np.random.normal(0, 20),
                    'temperature': 45 + load_factor * 15 + np.random.normal(0, 3)
                },
                'DistributionTransformer': {
                    'voltage': 220 + np.random.normal(0, 5),
                    'current': 150 * load_factor + np.random.normal(0, 15),
                    'temperature': 50 + load_factor * 10 + np.random.normal(0, 2)
                },
                'CircuitBreaker': {
                    'voltage': 0,
                    'current': 0,
                    'temperature': 30 + np.random.normal(0, 2)
                },
                'IndustrialLoad': {
                    'voltage': 33 + np.random.normal(0, 2),
                    'current': 100 * load_factor + np.random.normal(0, 10),
                    'temperature': 35 + load_factor * 5 + np.random.normal(0, 1)
                }
            }
            
            for asset_type, params in asset_data.items():
                data.append({
                    'timestamp': timestamp,
                    'asset_type': asset_type,
                    'voltage': params['voltage'],
                    'current': params['current'],
                    'power': params['voltage'] * params['current'] * np.random.uniform(0.8, 1.0),
                    'temperature': params['temperature'],
                    'age_days': np.random.uniform(0, 3650),
                    'health_score': max(0, min(100, 100 - np.random.uniform(0, 20)))
                })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Test the AI models
    print("Testing AI/ML Models for Substation Digital Twin...")
    
    # Generate synthetic data
    data = generate_synthetic_substation_data(30)
    print(f"Generated {len(data)} data points")
    
    # Initialize AI manager
    ai_manager = SubstationAIManager()
    ai_manager.initialize_with_synthetic_data()
    
    # Test analysis
    test_assets = {
        'TX1': {'asset_type': 'PowerTransformer', 'voltage': 400, 'current': 200, 'power': 80000, 'temperature': 60, 'health_score': 85, 'age_days': 1000},
        'DTX1': {'asset_type': 'DistributionTransformer', 'voltage': 220, 'current': 150, 'power': 33000, 'temperature': 55, 'health_score': 90, 'age_days': 500},
        'CB1': {'asset_type': 'CircuitBreaker', 'voltage': 0, 'current': 0, 'power': 0, 'temperature': 30, 'health_score': 95, 'age_days': 200}
    }
    
    test_metrics = {
        'total_power': 100000,
        'efficiency': 92.5,
        'voltage_stability': 96.8
    }
    
    result = ai_manager.analyze_current_state(test_assets, test_metrics)
    print("AI Analysis Result:")
    print(json.dumps(result, indent=2))