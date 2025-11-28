from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.audit_service import AuditService
from app.models import User, UserRole
from app.security import require_role

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_audit_logs():
    """Get audit logs (auditors and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view audit logs'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        action = request.args.get('action')
        filter_user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert date strings
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        result = AuditService.get_audit_logs(
            limit=limit,
            offset=offset,
            action=action,
            user_id=filter_user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@audit_bp.route('/user/<int:user_id>/logs', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_user_audit_logs(user_id):
    """Get audit logs for a specific user (auditors and admins only)."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if current_user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view audit logs'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = AuditService.get_user_audit_logs(user_id, limit, offset)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@audit_bp.route('/login-attempts', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_login_attempts():
    """Get login attempts (auditors and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view login attempts'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        filter_user_id = request.args.get('user_id', type=int)
        
        result = AuditService.get_login_attempts(filter_user_id, limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@audit_bp.route('/suspicious-activities', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_suspicious_activities():
    """Get suspicious activities (auditors and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view suspicious activities'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = AuditService.get_suspicious_activities(limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@audit_bp.route('/admin-actions', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_admin_actions():
    """Get admin actions (auditors and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view admin actions'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = AuditService.get_admin_actions(limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@audit_bp.route('/account-freeze-logs', methods=['GET'])
@jwt_required()
@require_role(UserRole.AUDITOR, UserRole.ADMIN)
def get_account_freeze_logs():
    """Get account freeze/unfreeze logs (auditors and admins only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in [UserRole.AUDITOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only auditors and admins can view account freeze logs'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = AuditService.get_account_freeze_logs(limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
