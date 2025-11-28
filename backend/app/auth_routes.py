from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import BadRequest
from app.auth_service import AuthService
from app.security import require_auth, require_role, generate_csrf_token
from app.models import User, UserRole

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"Registration data received: {data}")
        
        result = AuthService.register_user(
            username=data.get('username'),
            email=data.get('email'),
            phone=data.get('phone'),
            password=data.get('password'),
            full_name=data.get('full_name')
        )
        
        return jsonify(result), 201
    except BadRequest as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except ValueError as e:
        print(f"ValueError during registration: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception during registration: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = AuthService.login(
            username=data.get('username'),
            password=data.get('password'),
            ip_address=request.remote_addr
        )
        # If must_change_credentials True, still return success but flag present
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user."""
    try:
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        
        # Check if user is an auditor
        user = User.query.get(user_id)
        if user and user.role == UserRole.AUDITOR:
            return jsonify({'error': 'Auditors cannot change their password'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = AuthService.change_password(
            user_id=user_id,
            old_password=data.get('old_password'),
            new_password=data.get('new_password')
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        print(f"Getting profile for user_id: {user_id}, type: {type(user_id)}")
        result = AuthService.get_user(user_id)
        return jsonify(result), 200
    except ValueError as e:
        print(f"ValueError in get_profile: {str(e)}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        print(f"Exception in get_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        
        # Check if user is an auditor
        user = User.query.get(user_id)
        if user and user.role == UserRole.AUDITOR:
            return jsonify({'error': 'Auditors cannot modify their profile'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = AuthService.update_profile(
            user_id=user_id,
            email=data.get('email'),
            phone=data.get('phone'),
            full_name=data.get('full_name')
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

        
@auth_bp.route('/csrf', methods=['GET'])
@jwt_required()
def get_csrf_token():
    """Return CSRF token for the current authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        token = generate_csrf_token(user_id)
        return jsonify({'csrf_token': token}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-credentials', methods=['POST'])
@jwt_required()
@require_role(UserRole.ADMIN)
def change_credentials():
    """Rotate admin credentials (username + password) as required on first login.

    JSON Body:
    {
      "current_password": "...",
      "new_username": "...",
      "new_password": "..."
    }
    Returns success JSON and clears must_change_credentials flag.
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        result = AuthService.change_credentials(
            user_id=user_id,
            current_password=data.get('current_password'),
            new_username=data.get('new_username'),
            new_password=data.get('new_password')
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
