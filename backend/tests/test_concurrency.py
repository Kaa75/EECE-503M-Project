import pytest
import threading
from app import create_app
from app.models import db, User, Account
from app.auth_service import AuthService
from app.account_service import AccountService
from app.transaction_service import TransactionService

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


class TestConcurrentTransactions:
    """Test concurrent transaction scenarios."""
    
    def test_concurrent_transfers_from_same_account(self, app):
        """Test multiple simultaneous transfers from same account."""
        with app.app_context():
            # Create user and account
            result = AuthService.register_user(
                username='testuser',
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
            
            account1 = AccountService.create_account(
                user_id=result['user_id'],
                account_type='checking',
                opening_balance=1000.0
            )
            
            account2 = AccountService.create_account(
                user_id=result['user_id'],
                account_type='savings',
                opening_balance=0.0
            )
            
            account3 = AccountService.create_account(
                user_id=result['user_id'],
                account_type='savings',
                opening_balance=0.0
            )
            
            errors = []
            successes = []
            
            def transfer(sender_id, receiver_id, amount):
                """Perform transfer in thread."""
                try:
                    with app.app_context():
                        result = TransactionService.internal_transfer(
                            sender_user_id=result['user_id'],
                            sender_account_id=sender_id,
                            receiver_account_id=receiver_id,
                            amount=amount
                        )
                        successes.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Create threads for concurrent transfers
            threads = []
            for i in range(3):
                t = threading.Thread(
                    target=transfer,
                    args=(account1['account_id'], 
                          account2['account_id'] if i % 2 == 0 else account3['account_id'],
                          400.0)
                )
                threads.append(t)
            
            # Start all threads
            for t in threads:
                t.start()
            
            # Wait for all to complete
            for t in threads:
                t.join()
            
            # At least some should fail due to insufficient balance
            # Total requested: 1200, available: 1000
            assert len(errors) > 0 or len(successes) < 3
            
            # Verify final balance consistency
            with app.app_context():
                final_account1 = Account.query.get(account1['account_id'])
                final_account2 = Account.query.get(account2['account_id'])
                final_account3 = Account.query.get(account3['account_id'])
                
                total = final_account1.balance + final_account2.balance + final_account3.balance
                # Total should still be 1000 (conservation of money)
                assert abs(total - 1000.0) < 0.01
    
    def test_concurrent_account_freeze_unfreeze(self, app):
        """Test concurrent freeze/unfreeze operations."""
        with app.app_context():
            result = AuthService.register_user(
                username='testuser',
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
            
            account = AccountService.create_account(
                user_id=result['user_id'],
                account_type='checking',
                opening_balance=1000.0
            )
            
            results = []
            
            def freeze_account():
                """Freeze account in thread."""
                try:
                    with app.app_context():
                        result = AccountService.freeze_account(
                            account['account_id'],
                            result['user_id']
                        )
                        results.append(('freeze', result))
                except Exception as e:
                    results.append(('freeze_error', str(e)))
            
            def unfreeze_account():
                """Unfreeze account in thread."""
                try:
                    with app.app_context():
                        result = AccountService.unfreeze_account(
                            account['account_id'],
                            result['user_id']
                        )
                        results.append(('unfreeze', result))
                except Exception as e:
                    results.append(('unfreeze_error', str(e)))
            
            # Run concurrent freeze/unfreeze
            threads = [
                threading.Thread(target=freeze_account),
                threading.Thread(target=unfreeze_account),
                threading.Thread(target=freeze_account),
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join()
            
            # Should have some errors due to state conflicts
            assert len(results) == 3
            assert any('error' in r[0] for r in results)
    
    def test_concurrent_user_registrations_same_username(self, app):
        """Test concurrent registrations with same username."""
        errors = []
        successes = []
        
        def register_user(username):
            """Register user in thread."""
            try:
                with app.app_context():
                    result = AuthService.register_user(
                        username=username,
                        email=f'{username}{threading.get_ident()}@example.com',
                        phone='+1234567890',
                        password='SecurePass123',
                        full_name='Test User'
                    )
                    successes.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Try to register same username concurrently
        threads = []
        for i in range(5):
            t = threading.Thread(target=register_user, args=('duplicate_user',))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Only one should succeed
        assert len(successes) == 1
        assert len(errors) == 4


class TestBalanceConsistency:
    """Test that account balances remain consistent."""
    
    def test_internal_transfer_balance_conservation(self, app_context):
        """Test that internal transfers conserve total balance."""
        # Create users and accounts
        result = AuthService.register_user(
            username='balanceuser',
            email='balance@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Balance User'
        )
        
        # Create two accounts for the SAME user
        account1 = AccountService.create_account(
            user_id=result['user_id'],
            account_type='checking',
            opening_balance=1000.0
        )
        
        account2 = AccountService.create_account(
            user_id=result['user_id'],
            account_type='savings',
            opening_balance=500.0
        )
        
        initial_total = 1500.0
        
        # Perform internal transfer (same user, different accounts)
        TransactionService.internal_transfer(
            sender_user_id=result['user_id'],
            sender_account_id=account1['account_id'],
            receiver_account_id=account2['account_id'],
            amount=200.0
        )
        
        # Check balances
        acc1 = Account.query.get(account1['account_id'])
        acc2 = Account.query.get(account2['account_id'])
        
        final_total = acc1.balance + acc2.balance
        
        # Total should be conserved
        assert abs(final_total - initial_total) < 0.01
    
    def test_multiple_transfers_preserve_total(self, app_context):
        """Test that multiple transfers preserve system total balance."""
        # Create ONE user with MULTIPLE accounts
        result = AuthService.register_user(
            username='multiuser',
            email='multi@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Multi Account User'
        )
        
        # Create 5 accounts for the same user
        accounts = []
        for i in range(5):
            account = AccountService.create_account(
                user_id=result['user_id'],
                account_type='checking' if i % 2 == 0 else 'savings',
                opening_balance=1000.0
            )
            accounts.append(account)
        
        initial_total = 5000.0
        
        # Perform random internal transfers (all same user)
        TransactionService.internal_transfer(
            sender_user_id=result['user_id'],
            sender_account_id=accounts[0]['account_id'],
            receiver_account_id=accounts[1]['account_id'],
            amount=100.0
        )
        
        TransactionService.internal_transfer(
            sender_user_id=result['user_id'],
            sender_account_id=accounts[1]['account_id'],
            receiver_account_id=accounts[2]['account_id'],
            amount=200.0
        )
        
        TransactionService.internal_transfer(
            sender_user_id=result['user_id'],
            sender_account_id=accounts[2]['account_id'],
            receiver_account_id=accounts[3]['account_id'],
            amount=150.0
        )
        
        # Calculate final total
        final_total = sum(
            Account.query.get(acc['account_id']).balance 
            for acc in accounts
        )
        
        # Total should be conserved
        assert abs(final_total - initial_total) < 0.01
    
    def test_transaction_atomicity(self, app_context):
        """Test that failed transactions don't partially update balances."""
        result = AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        account1 = AccountService.create_account(
            user_id=result['user_id'],
            account_type='checking',
            opening_balance=100.0
        )
        
        account2 = AccountService.create_account(
            user_id=result['user_id'],
            account_type='savings',
            opening_balance=500.0
        )
        
        initial_balance1 = Account.query.get(account1['account_id']).balance
        initial_balance2 = Account.query.get(account2['account_id']).balance
        
        # Try to transfer more than available (should fail)
        try:
            TransactionService.internal_transfer(
                sender_user_id=result['user_id'],
                sender_account_id=account1['account_id'],
                receiver_account_id=account2['account_id'],
                amount=500.0  # More than available
            )
        except ValueError:
            pass  # Expected to fail
        
        # Balances should be unchanged
        final_balance1 = Account.query.get(account1['account_id']).balance
        final_balance2 = Account.query.get(account2['account_id']).balance
        
        assert final_balance1 == initial_balance1
        assert final_balance2 == initial_balance2
