"""API blueprint"""
from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'version': '1.0.0'
        }
    }), 200

# Import routes to register them with the blueprint
from app.api import customers, products, plans, quotations, subscriptions

# Module 4: Customer Portal, Analytics, Notifications, Renewals, Audit
from app.api import portal, notifications, renewals, analytics, audit
