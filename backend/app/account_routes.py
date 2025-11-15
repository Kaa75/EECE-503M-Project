from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.account_service import AccountService
from app.models import User, UserRole

account_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')

@account_bp.route('', methods=['POST'])
@jwt_required()
def create_account():
    """Create a new account."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Customers can only create their own accounts
        target_user_id = data.get('user_id', user_id)
        if isinstance(target_user_id, str):
            target_user_id = int(target_user_id)
        
        user = User.query.get(user_id)
        
        if user.role == UserRole.CUSTOMER and target_user_id != user_id:
            return jsonify({'error': 'Customers can only create their own accounts'}), 403
        
        result = AccountService.create_account(
            user_id=target_user_id,
            account_type=data.get('account_type'),
            opening_balance=data.get('opening_balance', 0.0)
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error creating account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    """Get account details."""
    try:
        result = AccountService.get_account(account_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_accounts(user_id):
    """Get all accounts for a user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        result = AccountService.get_user_accounts(user_id)
        return jsonify({'accounts': result}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/<int:account_id>/freeze', methods=['POST'])
@jwt_required()
def freeze_account(account_id):
    """Freeze an account (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        user = User.query.get(admin_id)
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Only admins can freeze accounts'}), 403
        
        result = AccountService.freeze_account(account_id, admin_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/<int:account_id>/unfreeze', methods=['POST'])
@jwt_required()
def unfreeze_account(account_id):
    """Unfreeze an account (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        user = User.query.get(admin_id)
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Only admins can unfreeze accounts'}), 403
        
        result = AccountService.unfreeze_account(account_id, admin_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/<int:account_id>/balance', methods=['GET'])
@jwt_required()
def get_balance(account_id):
    """Get account balance."""
    try:
        result = AccountService.get_account_balance(account_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@account_bp.route('/<int:account_id>/close', methods=['POST'])
@jwt_required()
def close_account(account_id):
    """Close an account (admin only)."""
    try:
        admin_id = int(get_jwt_identity())
        user = User.query.get(admin_id)
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Only admins can close accounts'}), 403
        
        result = AccountService.close_account(account_id, admin_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
