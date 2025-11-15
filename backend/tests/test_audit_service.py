import pytest
from datetime import datetime, timedelta
from app import create_app
from app.models import db, User, AuditLog, AuditAction, UserRole
from app.auth_service import AuthService
from app.audit_service import AuditService
from app.security import log_audit

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

@pytest.fixture
def test_auditor(app_context):
    """Create a test auditor."""
    result = AuthService.register_user(
        username='auditor',
        email='auditor@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test Auditor'
    )
    user = User.query.get(result['user_id'])
    user.role = UserRole.AUDITOR
    db.session.commit()
    return user

class TestAuditService:
    """Test cases for AuditService."""
    
    def test_get_audit_logs_success(self, app_context, test_user, test_auditor):
        """Test getting audit logs."""
        # Create some audit logs
        for i in range(3):
            log_audit(
                user_id=test_user.id,
                action=AuditAction.LOGIN,
                resource_type='user',
                resource_id=str(test_user.id),
                details='Test login'
            )
        
        result = AuditService.get_audit_logs(limit=10)
        
        assert result['total_count'] >= 3
        assert len(result['logs']) >= 3
    
    def test_get_audit_logs_with_action_filter(self, app_context, test_user):
        """Test getting audit logs filtered by action."""
        # Create logs with different actions
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id)
        )
        
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN_FAILED,
            resource_type='user',
            resource_id=str(test_user.id)
        )
        
        result = AuditService.get_audit_logs(action='login')
        
        assert all(log['action'] == 'login' for log in result['logs'])
    
    def test_get_audit_logs_with_user_filter(self, app_context, test_user):
        """Test getting audit logs filtered by user."""
        # Create logs for specific user
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id)
        )
        
        result = AuditService.get_audit_logs(user_id=test_user.id)
        
        assert all(log['user_id'] == test_user.id for log in result['logs'])
    
    def test_get_audit_logs_with_date_filter(self, app_context, test_user):
        """Test getting audit logs filtered by date range."""
        # Create a log
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id)
        )
        
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        result = AuditService.get_audit_logs(start_date=start_date, end_date=end_date)
        
        assert result['total_count'] >= 1
    
    def test_get_audit_logs_invalid_action(self, app_context):
        """Test getting audit logs with invalid action."""
        with pytest.raises(ValueError, match='Invalid action'):
            AuditService.get_audit_logs(action='invalid_action')
    
    def test_get_user_audit_logs_success(self, app_context, test_user):
        """Test getting audit logs for a specific user."""
        # Create logs for the user
        for i in range(2):
            log_audit(
                user_id=test_user.id,
                action=AuditAction.LOGIN,
                resource_type='user',
                resource_id=str(test_user.id)
            )
        
        result = AuditService.get_user_audit_logs(test_user.id)
        
        assert result['user_id'] == test_user.id
        assert result['total_count'] >= 2
    
    def test_get_user_audit_logs_not_found(self, app_context):
        """Test getting audit logs for non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            AuditService.get_user_audit_logs(999)
    
    def test_get_login_attempts_success(self, app_context, test_user):
        """Test getting login attempts."""
        # Create login logs
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id),
            details='Successful login'
        )
        
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN_FAILED,
            resource_type='user',
            resource_id=str(test_user.id),
            details='Failed login'
        )
        
        result = AuditService.get_login_attempts()
        
        assert result['total_count'] >= 2
        assert any(log['action'] == 'login' for log in result['logs'])
        assert any(log['action'] == 'login_failed' for log in result['logs'])
    
    def test_get_login_attempts_filtered_by_user(self, app_context, test_user):
        """Test getting login attempts for a specific user."""
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id)
        )
        
        result = AuditService.get_login_attempts(user_id=test_user.id)
        
        assert all(log['user_id'] == test_user.id for log in result['logs'])
    
    def test_get_suspicious_activities_success(self, app_context, test_user):
        """Test getting suspicious activities."""
        # Create suspicious activity logs
        log_audit(
            user_id=test_user.id,
            action=AuditAction.SUSPICIOUS_ACTIVITY,
            resource_type='transaction',
            resource_id='123',
            details='Unusual transfer amount'
        )
        
        result = AuditService.get_suspicious_activities()
        
        assert result['total_count'] >= 1
        assert all(log['action'] == 'suspicious_activity' for log in result['logs'])
    
    def test_get_admin_actions_success(self, app_context, test_user):
        """Test getting admin actions."""
        # Create admin action logs
        log_audit(
            user_id=test_user.id,
            action=AuditAction.ADMIN_ACTION,
            resource_type='user',
            resource_id=str(test_user.id),
            details='User role changed'
        )
        
        result = AuditService.get_admin_actions()
        
        assert result['total_count'] >= 1
        assert all(log['action'] == 'admin_action' for log in result['logs'])
    
    def test_get_account_freeze_logs_success(self, app_context, test_user):
        """Test getting account freeze logs."""
        # Create freeze logs
        log_audit(
            user_id=test_user.id,
            action=AuditAction.ACCOUNT_FREEZE,
            resource_type='account',
            resource_id='ACC-123',
            details='Account frozen'
        )
        
        log_audit(
            user_id=test_user.id,
            action=AuditAction.ACCOUNT_UNFREEZE,
            resource_type='account',
            resource_id='ACC-123',
            details='Account unfrozen'
        )
        
        result = AuditService.get_account_freeze_logs()
        
        assert result['total_count'] >= 2
        actions = [log['action'] for log in result['logs']]
        assert 'account_freeze' in actions
        assert 'account_unfreeze' in actions
    
    def test_audit_log_pagination(self, app_context, test_user):
        """Test pagination of audit logs."""
        # Create multiple logs
        for i in range(15):
            log_audit(
                user_id=test_user.id,
                action=AuditAction.LOGIN,
                resource_type='user',
                resource_id=str(test_user.id)
            )
        
        # Get first page
        result1 = AuditService.get_audit_logs(limit=5, offset=0)
        
        # Get second page
        result2 = AuditService.get_audit_logs(limit=5, offset=5)
        
        assert len(result1['logs']) == 5
        assert len(result2['logs']) == 5
        assert result1['logs'][0] != result2['logs'][0]
    
    def test_audit_log_ip_address(self, app_context, test_user):
        """Test that IP address is logged."""
        log_audit(
            user_id=test_user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(test_user.id),
            ip_address='192.168.1.1'
        )
        
        result = AuditService.get_audit_logs(user_id=test_user.id)
        
        assert any(log['ip_address'] == '192.168.1.1' for log in result['logs'])
    
    def test_audit_log_details(self, app_context, test_user):
        """Test that details are logged."""
        details = 'User attempted to access restricted resource'
        
        log_audit(
            user_id=test_user.id,
            action=AuditAction.SUSPICIOUS_ACTIVITY,
            resource_type='user',
            resource_id=str(test_user.id),
            details=details
        )
        
        result = AuditService.get_suspicious_activities()
        
        assert any(log['details'] == details for log in result['logs'])
