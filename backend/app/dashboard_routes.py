from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.security import require_role
from app.models import UserRole
from app.account_service import AccountService
from app.transaction_service import TransactionService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_role(UserRole.CUSTOMER, UserRole.ADMIN)
def get_dashboard():
    """Return composite dashboard data for the authenticated customer/admin.

    Response structure:
    {
      "accounts": [
        {
          <account fields>,
          "recent_transactions": [ { <txn fields> }, ... up to 5 ]
        }, ...
      ],
      "quick_links": [ {"label": str, "path": str}, ... ]
    }
    """
    try:
        user_id_raw = get_jwt_identity()
        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid user identity'}), 401

        accounts = AccountService.get_user_accounts(user_id)
        composite_accounts = []
        for acc in accounts:
            # Fetch last 5 transactions via existing service
            txn_data = TransactionService.get_account_transactions(acc['id'], limit=5, offset=0)
            composite_accounts.append({
                **acc,
                'recent_transactions': txn_data.get('transactions', [])
            })

        quick_links = [
            { 'label': 'Internal Transfer', 'path': '/transfer/internal' },
            { 'label': 'External Transfer', 'path': '/transfer/external' },
            { 'label': 'Pay Bills', 'path': '/bills' },
            { 'label': 'View All Transactions', 'path': '/transactions' }
        ]

        return jsonify({
            'accounts': composite_accounts,
            'quick_links': quick_links
        }), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500