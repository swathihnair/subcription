import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    
    # Feature Flags
    ENABLE_DEMO_DATA = os.getenv('ENABLE_DEMO_DATA', 'False').lower() == 'true'
    ENABLE_AUDIT_LOGGING = os.getenv('ENABLE_AUDIT_LOGGING', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_ENV = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///subscriptiq_dev.db'
    )

class TestingConfig(Config):
    """Testing configuration"""
    FLASK_ENV = 'testing'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=10)

class ProductionConfig(Config):
    """Production configuration"""
    FLASK_ENV = 'production'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///subscriptiq_prod.db'  # Fallback for dev

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
