from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config.config import config

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions avec l'application
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configuration du login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    # Import des modèles pour que SQLAlchemy les connaisse
    from app.models import user, employee, department, leave
    
    # Route racine
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Enregistrement des blueprints
    from app.routes import auth, dashboard, employee, department, leave, profile
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(employee.bp)
    app.register_blueprint(department.bp)
    app.register_blueprint(leave.bp)
    app.register_blueprint(profile.bp)
    
    # Création des tables
    with app.app_context():
        db.create_all()
    
    return app