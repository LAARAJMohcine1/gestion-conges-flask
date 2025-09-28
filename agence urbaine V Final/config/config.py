from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = environ.get('SECRET_KEY') or 'dev-key-à-changer-en-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = 'Agence Urbaine de Taza-Taounate'
    APP_SHORT_NAME = 'Agence Urbaine'
    
class DevelopmentConfig(Config):
    DEBUG = True
    # Configuration MySQL avec les bons identifiants trouvés
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') or 'mysql+pymysql://root:root@localhost/agence_urbaine_db'
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')

class ExecutableConfig(Config):
    DEBUG = False
    # Utilise SQLite pour l'exécutable (pas besoin d'installer MySQL)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///agence_urbaine.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'executable': ExecutableConfig,
    'default': DevelopmentConfig
} 