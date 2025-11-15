import pytest
from app import create_app
from app.models import db, User, UserRole
from app.auth_service import AuthService
from app.rbac_service import RBACService

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
    """Create a test customer user."""
    result = AuthService.register_user(
        username='customer',
        email='customer@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test Customer'
    )
    return User.query.get(result['user_id'])

@pytest.fixture
def test_admin(app_context):
    """Create a test admin user."""
    result = AuthService.register_user(
        username='admin',
        email='admin@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test Admin'
    )
    user = User.query.get(result['user_id'])
    user.role = UserRole.ADMIN
    db.session.commit()
    return user

class TestRBACService:
    """Test cases for RBACService."""
    
    def test_customer_permissions(self, app_context, test_user):
        """Test customer role permissions."""
        assert RBACService.has_permission(test_user, 'register_login') is True
        assert RBACService.has_permission(test_user, 'manage_own_profile') is True
        assert RBACService.has_permission(test_user, 'create_accounts') is True
        assert RBACService.has_permission(test_user, 'internal_transfers') is True
        assert RBACService.has_permission(test_user, 'external_transfers') is True
        assert RBACService.has_permission(test_user, 'freeze_unfreeze_accounts') is False
        assert RBACService.has_permission(test_user, 'assign_change_user_roles') is False
    
    def test_admin_permissions(self, app_context, test_admin):
        """Test admin role permissions."""
        assert RBACService.has_permission(test_admin, 'register_login') is True
        assert RBACService.has_permission(test_admin, 'manage_own_profile') is True
        assert RBACService.has_permission(test_admin, 'freeze_unfreeze_accounts') is True
        assert RBACService.has_permission(test_admin, 'assign_change_user_roles') is True
        assert RBACService.has_permission(test_admin, 'view_audit_security_logs') is True
    
    def test_check_permission_by_user_id(self, app_context, test_user):
        """Test checking permission by user ID."""
        assert RBACService.check_permission(test_user.id, 'create_accounts') is True
        assert RBACService.check_permission(test_user.id, 'freeze_unfreeze_accounts') is False
    
    def test_check_permission_invalid_user(self, app_context):
        """Test checking permission for non-existent user."""
        assert RBACService.check_permission(999, 'create_accounts') is False
    
    def test_get_user_permissions_customer(self, app_context, test_user):
        """Test getting customer permissions."""
        result = RBACService.get_user_permissions(test_user.id)
        
        assert result['role'] == 'customer'
        assert 'permissions' in result
        assert result['permissions']['create_accounts'] is True
        assert result['permissions']['freeze_unfreeze_accounts'] is False
    
    def test_get_user_permissions_admin(self, app_context, test_admin):
        """Test getting admin permissions."""
        result = RBACService.get_user_permissions(test_admin.id)
        
        assert result['role'] == 'admin'
        assert result['permissions']['freeze_unfreeze_accounts'] is True
        assert result['permissions']['assign_change_user_roles'] is True
    
    def test_get_user_permissions_not_found(self, app_context):
        """Test getting permissions for non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            RBACService.get_user_permissions(999)
    
    def test_assign_role_success(self, app_context, test_user, test_admin):
        """Test successful role assignment."""
        result = RBACService.assign_role(
            user_id=test_user.id,
            new_role='support_agent',
            admin_id=test_admin.id
        )
        
        assert result['success'] is True
        assert result['new_role'] == 'support_agent'
        
        # Verify role was changed in database
        user = User.query.get(test_user.id)
        assert user.role == UserRole.SUPPORT_AGENT
    
    def test_assign_role_invalid_role(self, app_context, test_user, test_admin):
        """Test role assignment with invalid role."""
        with pytest.raises(ValueError, match='Invalid role'):
            RBACService.assign_role(
                user_id=test_user.id,
                new_role='invalid_role',
                admin_id=test_admin.id
            )
    
    def test_assign_role_user_not_found(self, app_context, test_admin):
        """Test role assignment for non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            RBACService.assign_role(
                user_id=999,
                new_role='auditor',
                admin_id=test_admin.id
            )
    
    def test_get_users_by_role_customer(self, app_context, test_user):
        """Test getting users by customer role."""
        result = RBACService.get_users_by_role('customer', limit=10)
        
        assert result['role'] == 'customer'
        assert result['total_count'] >= 1
        assert any(u['user_id'] == test_user.id for u in result['users'])
    
    def test_get_users_by_role_admin(self, app_context, test_admin):
        """Test getting users by admin role."""
        result = RBACService.get_users_by_role('admin', limit=10)
        
        assert result['role'] == 'admin'
        assert any(u['user_id'] == test_admin.id for u in result['users'])
    
    def test_get_users_by_role_invalid_role(self, app_context):
        """Test getting users by invalid role."""
        with pytest.raises(ValueError, match='Invalid role'):
            RBACService.get_users_by_role('invalid_role')
    
    def test_deactivate_user_success(self, app_context, test_user, test_admin):
        """Test successful user deactivation."""
        result = RBACService.deactivate_user(test_user.id, test_admin.id)
        
        assert result['success'] is True
        assert result['is_active'] is False
        
        # Verify user is deactivated in database
        user = User.query.get(test_user.id)
        assert user.is_active is False
    
    def test_deactivate_user_not_found(self, app_context, test_admin):
        """Test deactivating non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            RBACService.deactivate_user(999, test_admin.id)
    
    def test_activate_user_success(self, app_context, test_user, test_admin):
        """Test successful user activation."""
        # First deactivate the user
        RBACService.deactivate_user(test_user.id, test_admin.id)
        
        # Then activate
        result = RBACService.activate_user(test_user.id, test_admin.id)
        
        assert result['success'] is True
        assert result['is_active'] is True
        
        # Verify user is activated in database
        user = User.query.get(test_user.id)
        assert user.is_active is True
    
    def test_activate_user_not_found(self, app_context, test_admin):
        """Test activating non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            RBACService.activate_user(999, test_admin.id)
    
    def test_support_agent_permissions(self, app_context):
        """Test support agent role permissions."""
        result = AuthService.register_user(
            username='agent',
            email='agent@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test Agent'
        )
        agent = User.query.get(result['user_id'])
        agent.role = UserRole.SUPPORT_AGENT
        db.session.commit()
        
        assert RBACService.has_permission(agent, 'view_all_user_accounts') is True
        assert RBACService.has_permission(agent, 'view_open_tickets') is True
        assert RBACService.has_permission(agent, 'update_ticket_status') is True
        assert RBACService.has_permission(agent, 'create_accounts') is False
        assert RBACService.has_permission(agent, 'internal_transfers') is False
    
    def test_auditor_permissions(self, app_context):
        """Test auditor role permissions."""
        result = AuthService.register_user(
            username='auditor',
            email='auditor@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test Auditor'
        )
        auditor = User.query.get(result['user_id'])
        auditor.role = UserRole.AUDITOR
        db.session.commit()
        
        assert RBACService.has_permission(auditor, 'view_all_user_accounts') is True
        assert RBACService.has_permission(auditor, 'view_audit_security_logs') is True
        assert RBACService.has_permission(auditor, 'manage_own_profile') is False
        assert RBACService.has_permission(auditor, 'create_accounts') is False
        assert RBACService.has_permission(auditor, 'internal_transfers') is False
