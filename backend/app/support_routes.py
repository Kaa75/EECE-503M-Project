from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.support_service import SupportService
from app.models import User, UserRole

support_bp = Blueprint('support', __name__, url_prefix='/api/support')

@support_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    """Create a new support ticket."""
    try:
        customer_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = SupportService.create_ticket(
            customer_id=customer_id,
            subject=data.get('subject'),
            description=data.get('description')
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/<string:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """Get ticket details."""
    try:
        result = SupportService.get_ticket(ticket_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/open', methods=['GET'])
@jwt_required()
def get_open_tickets():
    """Get all open support tickets (support agents and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.SUPPORT_AGENT, UserRole.ADMIN]:
            return jsonify({'error': 'Only support agents and admins can view open tickets'}), 403
        
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = SupportService.get_open_tickets(limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_tickets(customer_id):
    """Get all tickets for a customer."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Customers can only view their own tickets
        if user.role == UserRole.CUSTOMER and user_id != customer_id:
            return jsonify({'error': 'You can only view your own tickets'}), 403
        
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = SupportService.get_customer_tickets(customer_id, limit, offset)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/<string:ticket_id>/status', methods=['PUT'])
@jwt_required()
def update_ticket_status(ticket_id):
    """Update ticket status (support agents and admins only)."""
    try:
        agent_id = get_jwt_identity()
        user = User.query.get(agent_id)
        
        if user.role not in [UserRole.SUPPORT_AGENT, UserRole.ADMIN]:
            return jsonify({'error': 'Only support agents and admins can update ticket status'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = SupportService.update_ticket_status(
            ticket_id=ticket_id,
            new_status=data.get('status'),
            agent_id=agent_id
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/<string:ticket_id>/notes', methods=['POST'])
@jwt_required()
def add_note(ticket_id):
    """Add a note to a support ticket."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = SupportService.add_note(
            ticket_id=ticket_id,
            user_id=user_id,
            note=data.get('note')
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/tickets/<string:ticket_id>/assign', methods=['POST'])
@jwt_required()
def assign_ticket(ticket_id):
    """Assign a ticket to a support agent (admin only)."""
    try:
        admin_id = get_jwt_identity()
        user = User.query.get(admin_id)
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Only admins can assign tickets'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = SupportService.assign_ticket(
            ticket_id=ticket_id,
            agent_id=data.get('agent_id'),
            admin_id=admin_id
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
