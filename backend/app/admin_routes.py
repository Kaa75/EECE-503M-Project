from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.rbac_service import RBACService
from app.account_service import AccountService
from app.models import User, UserRole
from app.security import require_role, require_csrf
from app.security import hash_password, sanitize_input, validate_email, validate_phone, log_audit
from app.models import AuditAction, db

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# NOTE: Legacy require_admin retained for backward compatibility but new RBAC uses generic require_role.

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_role(UserRole.SUPPORT_AGENT, UserRole.AUDITOR, UserRole.ADMIN)
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

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@require_role(UserRole.ADMIN)
@require_csrf
def create_user():
    """Create a new user (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json() or {}

        required_fields = ['username', 'password', 'email', 'phone', 'full_name', 'role']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

        username = sanitize_input(data['username'], 80).lower()
        email = sanitize_input(data['email'], 120)
        full_name = sanitize_input(data['full_name'], 120)
        phone = data['phone']
        password = data['password']
        role_raw = data['role']

        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Username must be 3-50 characters'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if not validate_phone(phone):
            return jsonify({'error': 'Invalid phone format'}), 400
        if not password or len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if len(full_name) < 2:
            return jsonify({'error': 'Full name must be at least 2 characters'}), 400

        existing = User.query.filter((db.func.lower(User.username) == username) | (User.email == email)).first()
        if existing:
            return jsonify({'error': 'Username or email already exists'}), 400

        try:
            role = UserRole[role_raw.upper()]
        except KeyError:
            return jsonify({'error': f'Invalid role: {role_raw}'}), 400

        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Audit (admin action)
        log_audit(
            user_id=admin_id,
            action=AuditAction.ADMIN_ACTION,
            resource_type='user',
            resource_id=str(user.id),
            details=f'Admin created user {username} with role {role.value}'
        )

        return jsonify({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'full_name': user.full_name,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@require_role(UserRole.SUPPORT_AGENT, UserRole.AUDITOR, UserRole.ADMIN)
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

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_role(UserRole.ADMIN)
@require_csrf
def update_user(user_id):
    """Update another user's profile (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json() or {}
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        changed_fields = []

        new_username = data.get('username')
        if new_username:
            norm_username = sanitize_input(new_username, 80).lower()
            if len(norm_username) < 3 or len(norm_username) > 50:
                return jsonify({'error': 'Username must be 3-50 characters'}), 400
            existing = User.query.filter(db.func.lower(User.username) == norm_username, User.id != user_id).first()
            if existing:
                return jsonify({'error': 'Username already exists'}), 400
            user.username = norm_username
            changed_fields.append('username')

        new_email = data.get('email')
        if new_email:
            if not validate_email(new_email):
                return jsonify({'error': 'Invalid email format'}), 400
            existing_email = User.query.filter(User.email == new_email, User.id != user_id).first()
            if existing_email:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = sanitize_input(new_email, 120)
            changed_fields.append('email')

        new_phone = data.get('phone')
        if new_phone:
            if not validate_phone(new_phone):
                return jsonify({'error': 'Invalid phone format'}), 400
            user.phone = new_phone
            changed_fields.append('phone')

        new_full_name = data.get('full_name')
        if new_full_name:
            if len(new_full_name) < 2:
                return jsonify({'error': 'Full name must be at least 2 characters'}), 400
            user.full_name = sanitize_input(new_full_name, 120)
            changed_fields.append('full_name')

        if not changed_fields:
            return jsonify({'error': 'No updatable fields provided'}), 400

        try:
            db.session.commit()
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details=f'Admin updated fields: {", ".join(changed_fields)}'
            )
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Failed to update user'}), 500

        return jsonify({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'full_name': user.full_name,
            'role': user.role.value,
            'updated_fields': changed_fields
        }), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_role(UserRole.ADMIN)
@require_csrf
def delete_user(user_id):
    """Delete a user (admin only). Reject if user has accounts."""
    try:
        admin_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Simple business rule: prevent deletion if accounts exist
        if user.accounts and len(user.accounts) > 0:
            return jsonify({'error': 'Cannot delete user with existing accounts'}), 400

        try:
            db.session.delete(user)
            db.session.commit()
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user_id),
                details='Admin deleted user'
            )
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete user'}), 500

        return jsonify({'success': True, 'deleted_user_id': user_id}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/password', methods=['PUT'])
@jwt_required()
@require_role(UserRole.ADMIN)
@require_csrf
def reset_user_password(user_id):
    """Reset a user's password (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json() or {}
        new_password = data.get('new_password')
        if not new_password or len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        try:
            user.password_hash = hash_password(new_password)
            db.session.commit()
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details='Admin reset user password'
            )
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Failed to reset password'}), 500

        return jsonify({'success': True, 'user_id': user.id}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@require_role(UserRole.ADMIN)
@require_csrf
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
@jwt_required()
@require_role(UserRole.SUPPORT_AGENT, UserRole.AUDITOR, UserRole.ADMIN)
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
@jwt_required()
@require_role(UserRole.ADMIN)
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
@jwt_required()
@require_role(UserRole.ADMIN)
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
@jwt_required()
@require_role(UserRole.ADMIN)
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
@jwt_required()
@require_role(UserRole.ADMIN)
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
@jwt_required()
@require_role(UserRole.SUPPORT_AGENT, UserRole.AUDITOR, UserRole.ADMIN)
def get_user_accounts(user_id):
    """Get all accounts for a specific user (admin only)."""
    try:
        result = AccountService.get_user_accounts(user_id)
        return jsonify({'accounts': result}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

