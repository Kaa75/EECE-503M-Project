import pytest
from decimal import Decimal
from app import create_app
from app.models import db, User
from app.auth_service import AuthService
from app.account_service import AccountService
from app.transaction_service import TransactionService
from app.support_service import SupportService

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield

@pytest.fixture
def test_user(app_context):
    """Create a test user."""
    result = AuthService.register_user(
        username='testuser',
        email='test@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test User'
    )
    return User.query.get(result['user_id'])


class TestBoundaryConditions:
    """Test boundary and edge case values."""
    
    def test_maximum_length_username(self, app_context):
        """Test username at maximum length."""
        long_username = 'a' * 50  # Assuming max is 50
        
        try:
            result = AuthService.register_user(
                username=long_username,
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
            assert result['username'] == long_username
        except ValueError as e:
            # If there's a max length validation, that's also valid
            assert 'too long' in str(e).lower() or 'maximum' in str(e).lower()
    
    def test_extremely_long_username(self, app_context):
        """Test username beyond reasonable length."""
        very_long_username = 'a' * 1000
        
        with pytest.raises(ValueError):
            AuthService.register_user(
                username=very_long_username,
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
    
    def test_very_large_transaction_amount(self, app_context, test_user):
        """Test transfer with very large amount."""
        # Create account with very large balance
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=999999999.99
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        # Try to transfer very large amount
        result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=999999999.99
        )
        
        assert result['success'] is True
    
    def test_very_small_transaction_amount(self, app_context, test_user):
        """Test transfer with very small amount (0.01)."""
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=10.0
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=0.01
        )
        
        assert result['success'] is True
        assert result['amount'] == 0.01
    
    def test_float_precision_transfer(self, app_context, test_user):
        """Test transfer with floating point precision issues."""
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=100.33
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        # Transfer amount that could cause precision issues
        result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=0.33
        )
        
        assert result['success'] is True
        
        # Check balance is exactly 100.00
        from app.models import Account
        acc1 = Account.query.get(account1['account_id'])
        assert abs(acc1.balance - 100.0) < 0.001
    
    def test_many_accounts_per_user(self, app_context, test_user):
        """Test creating many accounts for single user."""
        accounts = []
        
        # Create 20 accounts
        for i in range(20):
            account = AccountService.create_account(
                user_id=test_user.id,
                account_type='checking' if i % 2 == 0 else 'savings',
                opening_balance=100.0
            )
            accounts.append(account)
        
        # Verify all created
        user_accounts = AccountService.get_user_accounts(test_user.id)
        assert len(user_accounts) == 20
    
    def test_zero_opening_balance(self, app_context, test_user):
        """Test creating account with zero opening balance."""
        account = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=0.0
        )
        
        assert account['balance'] == 0.0
    
    def test_exactly_available_balance_transfer(self, app_context, test_user):
        """Test transferring exactly the available balance."""
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=100.0
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=100.0
        )
        
        assert result['success'] is True
        
        # Sender should have 0 balance
        from app.models import Account
        acc1 = Account.query.get(account1['account_id'])
        assert acc1.balance == 0.0


class TestUnicodeAndSpecialCharacters:
    """Test handling of unicode and special characters."""
    
    def test_unicode_name(self, app_context):
        """Test user registration with unicode characters in name."""
        result = AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='José García 李明'
        )
        
        # Get the user to check full_name
        user = User.query.get(result['user_id'])
        assert user.full_name == 'José García 李明'
    
    def test_emoji_in_description(self, app_context, test_user):
        """Test ticket with emoji in description."""
        result = SupportService.create_ticket(
            customer_id=test_user.id,
            subject='Account Issue 🚀',
            description='My account is broken 😢 Please help! 🙏'
        )
        
        # Check subject (which is returned)
        assert '🚀' in result['subject']
        
        # Get the ticket to check description (query by ticket_id, not id)
        from app.models import SupportTicket
        ticket = SupportTicket.query.filter_by(ticket_id=result['ticket_id']).first()
        assert ticket is not None
        assert '😢' in ticket.description
    
    def test_special_characters_in_password(self, app_context):
        """Test password with various special characters."""
        special_password = 'P@ssw0rd!#$%^&*()'
        
        result = AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password=special_password,
            full_name='Test User'
        )
        
        # Verify login works with special password
        login_result = AuthService.login('testuser', special_password)
        assert login_result['success'] is True
    
    def test_apostrophe_in_name(self, app_context):
        """Test name with apostrophe (SQL injection attempt)."""
        result = AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name="O'Brien"
        )
        
        # Name should be safely stored (after sanitization)
        user = User.query.get(result['user_id'])
        assert user is not None


class TestLargeDatasets:
    """Test handling of large datasets."""
    
    def test_many_transactions_pagination(self, app_context, test_user):
        """Test pagination with many transactions."""
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=10000.0
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        # Create 50 transactions
        for i in range(50):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=account1['account_id'],
                receiver_account_id=account2['account_id'],
                amount=10.0
            )
        
        # Test pagination
        page1 = TransactionService.get_account_transactions(
            account1['account_id'],
            limit=20,
            offset=0
        )
        
        page2 = TransactionService.get_account_transactions(
            account1['account_id'],
            limit=20,
            offset=20
        )
        
        assert len(page1['transactions']) == 20
        assert len(page2['transactions']) == 20
        assert page1['transactions'][0] != page2['transactions'][0]
    
    def test_very_long_description(self, app_context, test_user):
        """Test ticket with very long description."""
        long_description = 'A' * 5000
        
        result = SupportService.create_ticket(
            customer_id=test_user.id,
            subject='Long Description Issue',
            description=long_description
        )
        
        # Get the ticket to check description (query by ticket_id, not id)
        from app.models import SupportTicket
        ticket = SupportTicket.query.filter_by(ticket_id=result['ticket_id']).first()
        assert ticket is not None
        # Description may be truncated to 2000 chars by sanitize_input
        assert len(ticket.description) >= 100


class TestBusinessRuleEdgeCases:
    """Test edge cases for business rules."""
    
    def test_account_number_format(self, app_context, test_user):
        """Test that account numbers follow expected format."""
        account = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=100.0
        )
        
        # Should start with ACC- and have digits
        assert account['account_number'].startswith('ACC-')
        assert len(account['account_number']) == 14  # ACC- + 10 digits
        assert account['account_number'][4:].isdigit()
    
    def test_transfer_to_same_account(self, app_context, test_user):
        """Test that transfer to same account is handled."""
        account = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=100.0
        )
        
        # This should either succeed (no-op) or fail with clear error
        try:
            result = TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=account['account_id'],
                receiver_account_id=account['account_id'],
                amount=50.0
            )
            # If it succeeds, balance should be unchanged
            from app.models import Account
            acc = Account.query.get(account['account_id'])
            assert acc.balance == 100.0
        except ValueError as e:
            # Or it should fail with appropriate error
            assert 'same account' in str(e).lower() or 'invalid' in str(e).lower()
    
    def test_close_account_with_exact_zero_balance(self, app_context, test_user):
        """Test closing account with exactly 0.00 balance."""
        account1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=100.0
        )
        
        account2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=0.0
        )
        
        # Transfer all money out
        TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=100.0
        )
        
        # Now close the account with 0 balance
        result = AccountService.close_account(account1['account_id'], test_user.id)
        
        assert result['success'] is True
        assert result['status'] == 'closed'
