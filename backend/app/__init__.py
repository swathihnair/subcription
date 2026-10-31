"""Flask application factory"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from app.extensions import db, migrate, jwt, cors
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name=None):
    """Create and configure the Flask application"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configure CORS more explicitly
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    
    # Configure logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register JWT error handlers
    register_jwt_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create tables and seed initial data (only once)
    if not hasattr(app, '_db_seeded'):
        with app.app_context():
            db.create_all()
            seed_initial_data(app)
            app._db_seeded = True
    
    return app

def register_blueprints(app):
    """Register application blueprints"""
    from app.api import api_bp
    from app.auth import auth_bp
    
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'The request is malformed or contains invalid data.'
            }
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication credentials are missing or invalid.'
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access this resource.'
            }
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found.'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An internal server error occurred.'
            }
        }), 500

def register_jwt_handlers(app):
    """Register JWT error handlers"""
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.models import User
        import uuid
        identity = jwt_data["sub"]
        return User.query.filter_by(id=uuid.UUID(identity) if isinstance(identity, str) else identity).first()
    
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        from app.models import User
        import uuid
        user = User.query.filter_by(id=uuid.UUID(identity) if isinstance(identity, str) else identity).first()
        if user:
            return {
                'role': user.role.name if user.role else None,
                'email': user.email
            }
        return {}

def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/subscriptiq.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SubscriptIQ startup')

def seed_initial_data(app):
    """Seed initial data into database"""
    from app.models import Role
    
    # Create default roles if they don't exist
    roles = ['admin', 'finance', 'sales', 'customer']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=f'{role_name.capitalize()} role')
            db.session.add(role)
    
    db.session.commit()
