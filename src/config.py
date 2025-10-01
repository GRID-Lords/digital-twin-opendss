"""
Configuration management for Digital Twin system
Reads from environment variables with fallback defaults
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'digitaltwin')
    DB_USER = os.getenv('DB_USER', 'digitaltwin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'securepassword123')

    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

    # InfluxDB Configuration
    INFLUX_HOST = os.getenv('INFLUX_HOST', 'localhost')
    INFLUX_PORT = int(os.getenv('INFLUX_PORT', '8086'))
    INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'my-super-secret-auth-token')
    INFLUX_ORG = os.getenv('INFLUX_ORG', 'digitaltwin')
    INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'metrics')

    # Application Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Data Storage Strategy
    REALTIME_CACHE_TTL = int(os.getenv('REALTIME_CACHE_TTL', '60'))  # seconds
    METRICS_STORAGE_INTERVAL = int(os.getenv('METRICS_STORAGE_INTERVAL', '3600'))  # 1 hour
    ANALYSIS_BATCH_SIZE = int(os.getenv('ANALYSIS_BATCH_SIZE', '100'))

    # SCADA Configuration
    SCADA_ENABLED = os.getenv('SCADA_ENABLED', 'true').lower() == 'true'
    MODBUS_HOST = os.getenv('MODBUS_HOST', 'localhost')
    MODBUS_PORT = int(os.getenv('MODBUS_PORT', '502'))
    SCADA_POLLING_INTERVAL = int(os.getenv('SCADA_POLLING_INTERVAL', '5'))

    # AI/ML Configuration
    ML_ENABLED = os.getenv('ML_ENABLED', 'true').lower() == 'true'
    ANOMALY_THRESHOLD = float(os.getenv('ANOMALY_THRESHOLD', '0.95'))
    PREDICTION_HORIZON = int(os.getenv('PREDICTION_HORIZON', '24'))
    MODEL_UPDATE_INTERVAL = int(os.getenv('MODEL_UPDATE_INTERVAL', '86400'))  # 24 hours

    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dt-jwt-secret-key-2024')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

    # Feature Flags
    ENABLE_3D_VISUALIZATION = os.getenv('ENABLE_3D_VISUALIZATION', 'true').lower() == 'true'
    ENABLE_ANOMALY_DETECTION = os.getenv('ENABLE_ANOMALY_DETECTION', 'true').lower() == 'true'
    ENABLE_PREDICTIVE_MAINTENANCE = os.getenv('ENABLE_PREDICTIVE_MAINTENANCE', 'true').lower() == 'true'
    ENABLE_OPTIMIZATION = os.getenv('ENABLE_OPTIMIZATION', 'true').lower() == 'true'

    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        if cls.DB_TYPE == 'postgresql':
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_TYPE == 'sqlite':
            return f"sqlite:///{cls.DB_NAME}.db"
        else:
            return "sqlite:///digital_twin.db"

    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}"

    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []

        if cls.DB_TYPE not in ['postgresql', 'sqlite']:
            errors.append(f"Invalid DB_TYPE: {cls.DB_TYPE}")

        if cls.METRICS_STORAGE_INTERVAL < 60:
            errors.append("METRICS_STORAGE_INTERVAL must be at least 60 seconds")

        if cls.REALTIME_CACHE_TTL < 1:
            errors.append("REALTIME_CACHE_TTL must be at least 1 second")

        if cls.ANOMALY_THRESHOLD < 0 or cls.ANOMALY_THRESHOLD > 1:
            errors.append("ANOMALY_THRESHOLD must be between 0 and 1")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

# Validate configuration on import
Config.validate()