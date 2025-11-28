from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    from app.auth_routes import auth_bp
    from app.account_routes import account_bp
    from app.transaction_routes import transaction_bp
    from app.admin_routes import admin_bp
    from app.support_routes import support_bp
    from app.audit_routes import audit_bp
    from app.dashboard_routes import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(account_bp, url_prefix='/api/accounts')
    app.register_blueprint(transaction_bp, url_prefix='/api/transactions')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(dashboard_bp)  # /api/dashboard
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"Invalid token error: {error}")
        return {'error': 'Invalid token', 'message': str(error)}, 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"Missing token error: {error}")
        return {'error': 'Authorization token is missing', 'message': str(error)}, 401
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
