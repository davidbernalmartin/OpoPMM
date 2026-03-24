# Central Configuration for the Application

class Config:
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'sqlite:///:memory:'

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URI = 'sqlite:///development.db'

class TestingConfig(Config):
    TESTING = True
    DATABASE_URI = 'sqlite:///testing.db'

class ProductionConfig(Config):
    DATABASE_URI = 'sqlite:///production.db'