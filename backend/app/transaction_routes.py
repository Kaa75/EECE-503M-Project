from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.transaction_service import TransactionService
from app.models import User, UserRole

transaction_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transaction_bp.route('/internal-transfer', methods=['POST'])
@jwt_required()
def internal_transfer():
    """Perform an internal transfer between user's own accounts."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = TransactionService.internal_transfer(
            sender_user_id=user_id,
            sender_account_id=data.get('sender_account_id'),
            receiver_account_id=data.get('receiver_account_id'),
            amount=data.get('amount'),
            description=data.get('description')
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@transaction_bp.route('/external-transfer', methods=['POST'])
@jwt_required()
def external_transfer():
    """Perform an external transfer to another user's account."""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = TransactionService.external_transfer(
            sender_user_id=user_id,
            sender_account_id=data.get('sender_account_id'),
            receiver_account_number=data.get('receiver_account_number'),
            amount=data.get('amount'),
            description=data.get('description')
        )
        
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@transaction_bp.route('/<string:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get transaction details."""
    try:
        result = TransactionService.get_transaction(transaction_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@transaction_bp.route('/account/<int:account_id>/history', methods=['GET'])
@jwt_required()
def get_account_transactions(account_id):
    """Get recent transactions for an account."""
    try:
        limit = request.args.get('limit', 5, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        result = TransactionService.get_account_transactions(account_id, limit, offset)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@transaction_bp.route('/account/<int:account_id>/filter', methods=['GET'])
@jwt_required()
def filter_transactions(account_id):
    """Filter transactions with various criteria."""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        transaction_type = request.args.get('transaction_type')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Convert date strings to datetime objects
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
        
        result = TransactionService.filter_transactions(
            account_id=account_id,
            start_date=start_dt,
            end_date=end_dt,
            transaction_type=transaction_type,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
