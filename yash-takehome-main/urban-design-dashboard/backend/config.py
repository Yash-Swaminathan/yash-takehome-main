import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///urban_dashboard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
    HUGGINGFACE_API_URL = 'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium'
    
    # Calgary Open Data API Configuration
    CALGARY_OPEN_DATA_BASE_URL = 'https://data.calgary.ca/resource'
    SOCRATA_APP_TOKEN = os.environ.get('SOCRATA_APP_TOKEN')  # Optional but recommended for higher rate limits
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'https://localhost:3000']

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DEVELOPMENT = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 