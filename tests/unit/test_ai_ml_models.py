"""
Unit tests for AI/ML models
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from models.ai_ml_models import (
    SubstationAnomalyDetector,
    SubstationPredictiveModel,
    SubstationOptimizer,
    SubstationAIManager
)

class TestSubstationAnomalyDetector:
    """Test anomaly detection functionality"""
    
    def test_initialization(self):
        """Test anomaly detector initialization"""
        detector = SubstationAnomalyDetector()
        assert detector.models == {}
        assert detector.scalers == {}
        assert detector.thresholds == {}
        assert detector.is_trained == False
    
    def test_train_with_synthetic_data(self):
        """Test training with synthetic data"""
        detector = SubstationAnomalyDetector()
        
        # Create synthetic data
        data = []
        for i in range(100):
            data.append({
                'asset_type': 'PowerTransformer',
                'voltage': 400.0 + np.random.normal(0, 10),
                'current': 200.0 + np.random.normal(0, 20),
                'power': 80000.0 + np.random.normal(0, 5000),
                'temperature': 45.0 + np.random.normal(0, 5),
                'health_score': 95.0 + np.random.normal(0, 3)
            })
        
        df = pd.DataFrame(data)
        detector.train(df)
        
        assert detector.is_trained == True
        assert 'PowerTransformer' in detector.models
        assert 'PowerTransformer' in detector.scalers
        assert 'PowerTransformer' in detector.thresholds
    
    def test_detect_anomalies(self, mock_assets):
        """Test anomaly detection on current data"""
        detector = SubstationAnomalyDetector()
        
        # Train with synthetic data first
        data = []
        for i in range(100):
            data.append({
                'asset_type': 'PowerTransformer',
                'voltage': 400.0 + np.random.normal(0, 10),
                'current': 200.0 + np.random.normal(0, 20),
                'power': 80000.0 + np.random.normal(0, 5000),
                'temperature': 45.0 + np.random.normal(0, 5),
                'health_score': 95.0 + np.random.normal(0, 3)
            })
        
        df = pd.DataFrame(data)
        detector.train(df)
        
        # Test anomaly detection
        anomalies = detector.detect_anomalies(mock_assets)
        assert isinstance(anomalies, list)
    
    def test_detect_anomalies_untrained(self, mock_assets):
        """Test anomaly detection when not trained"""
        detector = SubstationAnomalyDetector()
        anomalies = detector.detect_anomalies(mock_assets)
        assert anomalies == []

class TestSubstationPredictiveModel:
    """Test predictive maintenance functionality"""
    
    def test_initialization(self):
        """Test predictive model initialization"""
        model = SubstationPredictiveModel()
        assert model.models == {}
        assert model.scalers == {}
        assert model.feature_importance == {}
        assert model.is_trained == False
    
    def test_train_with_synthetic_data(self):
        """Test training with synthetic data"""
        model = SubstationPredictiveModel()
        
        # Create synthetic data
        data = []
        for i in range(200):
            data.append({
                'asset_type': 'PowerTransformer',
                'voltage': 400.0 + np.random.normal(0, 10),
                'current': 200.0 + np.random.normal(0, 20),
                'power': 80000.0 + np.random.normal(0, 5000),
                'temperature': 45.0 + np.random.normal(0, 5),
                'age_days': np.random.uniform(0, 3650),
                'health_score': max(0, min(100, 100 - (i / 200) * 20 + np.random.normal(0, 5)))
            })
        
        df = pd.DataFrame(data)
        model.train(df)
        
        assert model.is_trained == True
        assert 'PowerTransformer' in model.models
        assert 'PowerTransformer' in model.scalers
        assert 'PowerTransformer' in model.feature_importance
    
    def test_predict_health_degradation(self, mock_assets):
        """Test health degradation prediction"""
        model = SubstationPredictiveModel()
        
        # Train with synthetic data first
        data = []
        for i in range(200):
            data.append({
                'asset_type': 'PowerTransformer',
                'voltage': 400.0 + np.random.normal(0, 10),
                'current': 200.0 + np.random.normal(0, 20),
                'power': 80000.0 + np.random.normal(0, 5000),
                'temperature': 45.0 + np.random.normal(0, 5),
                'age_days': np.random.uniform(0, 3650),
                'health_score': max(0, min(100, 100 - (i / 200) * 20 + np.random.normal(0, 5)))
            })
        
        df = pd.DataFrame(data)
        model.train(df)
        
        # Test prediction
        predictions = model.predict_health_degradation(mock_assets)
        assert isinstance(predictions, list)
    
    def test_predict_health_degradation_untrained(self, mock_assets):
        """Test prediction when not trained"""
        model = SubstationPredictiveModel()
        predictions = model.predict_health_degradation(mock_assets)
        assert predictions == []

class TestSubstationOptimizer:
    """Test optimization functionality"""
    
    def test_initialization(self):
        """Test optimizer initialization"""
        optimizer = SubstationOptimizer()
        assert optimizer.optimization_history == []
    
    def test_optimize_power_flow(self, mock_metrics):
        """Test power flow optimization"""
        optimizer = SubstationOptimizer()
        result = optimizer.optimize_power_flow(mock_metrics)
        
        assert 'timestamp' in result
        assert 'current_efficiency' in result
        assert 'target_efficiency' in result
        assert 'recommendations' in result
        assert 'optimization_score' in result
    
    def test_optimize_maintenance_schedule(self, mock_ai_analysis):
        """Test maintenance schedule optimization"""
        optimizer = SubstationOptimizer()
        predictions = mock_ai_analysis['predictions']
        schedule = optimizer.optimize_maintenance_schedule(predictions)
        
        assert 'immediate' in schedule
        assert 'within_7_days' in schedule
        assert 'within_30_days' in schedule
        assert 'total_assets' in schedule

class TestSubstationAIManager:
    """Test AI manager functionality"""
    
    def test_initialization(self):
        """Test AI manager initialization"""
        manager = SubstationAIManager()
        assert manager.anomaly_detector is not None
        assert manager.predictive_model is not None
        assert manager.optimizer is not None
        # is_initialized may be True if pre-trained models exist
        assert isinstance(manager.is_initialized, bool)
    
    def test_initialize_with_synthetic_data(self):
        """Test initialization with synthetic data"""
        manager = SubstationAIManager()
        manager.initialize_with_synthetic_data()
        
        assert manager.is_initialized == True
        assert manager.anomaly_detector.is_trained == True
        assert manager.predictive_model.is_trained == True
    
    def test_analyze_current_state(self, mock_assets, mock_metrics):
        """Test complete AI analysis"""
        manager = SubstationAIManager()
        manager.initialize_with_synthetic_data()
        
        analysis = manager.analyze_current_state(mock_assets, mock_metrics)
        
        assert 'timestamp' in analysis
        assert 'anomalies' in analysis
        assert 'predictions' in analysis
        assert 'optimization' in analysis
        assert 'summary' in analysis
    
    def test_analyze_current_state_uninitialized(self, mock_assets, mock_metrics):
        """Test analysis when not initialized"""
        # Create manager with a non-existent model dir to force uninitialized state
        manager = SubstationAIManager(model_dir="/tmp/nonexistent_model_dir")
        manager.is_initialized = False  # Force uninitialized state
        analysis = manager.analyze_current_state(mock_assets, mock_metrics)
        assert analysis == {}