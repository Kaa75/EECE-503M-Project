from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.rbac_service import RBACService
from app.account_service import AccountService
from app.models import User, UserRole

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def require_admin(f):
    """Decorator to require admin role."""
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get all users (admin only)."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        users = User.query.limit(limit).offset(offset).all()
        total_count = User.query.count()
        
        return jsonify({
            'users': [
                {
                    'id': u.id,
                    'user_id': u.id,  # Keep for backward compatibility
                    'username': u.username,
                    'email': u.email,
                    'phone': u.phone,
                    'full_name': u.full_name,
                    'role': u.role.value,
                    'is_active': u.is_active,
                    'created_at': u.created_at.isoformat(),
                    'last_login': u.last_login.isoformat() if u.last_login else None
                }
                for u in users
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    """Get user details (admin only)."""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'full_name': user.full_name,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'failed_login_attempts': user.failed_login_attempts
        }), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@require_admin
def assign_role(user_id):
    """Assign a role to a user (admin only)."""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = RBACService.assign_role(
            user_id=user_id,
            new_role=data.get('role'),
            admin_id=admin_id
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/role/<string:role>', methods=['GET'])
@require_admin
def get_users_by_role(role):
    """Get all users with a specific role (admin only)."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = RBACService.get_users_by_role(role, limit, offset)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@require_admin
def deactivate_user(user_id):
    """Deactivate a user (admin only)."""
    try:
        admin_id = get_jwt_identity()
        result = RBACService.deactivate_user(user_id, admin_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@require_admin
def activate_user(user_id):
    """Activate a user (admin only)."""
    try:
        admin_id = get_jwt_identity()
        result = RBACService.activate_user(user_id, admin_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@require_admin
def get_user_permissions(user_id):
    """Get user permissions (admin only)."""
    try:
        result = RBACService.get_user_permissions(user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/accounts', methods=['POST'])
@require_admin
def create_account_for_user(user_id):
    """Create an account for any user (admin only)."""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create account for the specified user
        result = AccountService.create_account(
            user_id=user_id,
            account_type=data.get('account_type'),
            opening_balance=data.get('opening_balance', 0.0)
        )
        
        # Log the admin action
        from app.security import log_audit
        from app.models import AuditAction
        log_audit(
            user_id=admin_id,
            action=AuditAction.ADMIN_ACTION,
            resource_type='account',
            resource_id=result['account_number'],
            details=f'Admin created {data.get("account_type")} account for user {user_id}'
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/accounts', methods=['GET'])
@require_admin
def get_user_accounts(user_id):
    """Get all accounts for a specific user (admin only)."""
    try:
        result = AccountService.get_user_accounts(user_id)
        return jsonify({'accounts': result}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

