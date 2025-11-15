import pytest
from app import create_app
from app.models import db, User, SupportTicket, UserRole, TicketStatus
from app.auth_service import AuthService
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
def test_customer(app_context):
    """Create a test customer."""
    result = AuthService.register_user(
        username='customer',
        email='customer@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test Customer'
    )
    return User.query.get(result['user_id'])

@pytest.fixture
def test_agent(app_context):
    """Create a test support agent."""
    result = AuthService.register_user(
        username='agent',
        email='agent@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test Agent'
    )
    user = User.query.get(result['user_id'])
    user.role = UserRole.SUPPORT_AGENT
    db.session.commit()
    return user

class TestSupportService:
    """Test cases for SupportService."""
    
    def test_create_ticket_success(self, app_context, test_customer):
        """Test successful ticket creation."""
        result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        assert result['success'] is True
        assert result['subject'] == 'Account Issue'
        assert result['status'] == 'open'
    
    def test_create_ticket_short_subject(self, app_context, test_customer):
        """Test ticket creation with short subject."""
        with pytest.raises(ValueError, match='Subject must be at least 5 characters'):
            SupportService.create_ticket(
                customer_id=test_customer.id,
                subject='Help',
                description='I cannot access my account'
            )
    
    def test_create_ticket_short_description(self, app_context, test_customer):
        """Test ticket creation with short description."""
        with pytest.raises(ValueError, match='Description must be at least 10 characters'):
            SupportService.create_ticket(
                customer_id=test_customer.id,
                subject='Account Issue',
                description='Help me'
            )
    
    def test_create_ticket_customer_not_found(self, app_context):
        """Test ticket creation for non-existent customer."""
        with pytest.raises(ValueError, match='Customer not found'):
            SupportService.create_ticket(
                customer_id=999,
                subject='Account Issue',
                description='I cannot access my account'
            )
    
    def test_get_ticket_success(self, app_context, test_customer):
        """Test getting ticket details."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        result = SupportService.get_ticket(ticket_result['ticket_id'])
        
        assert result['subject'] == 'Account Issue'
        assert result['customer_id'] == test_customer.id
        assert result['status'] == 'open'
    
    def test_get_ticket_not_found(self, app_context):
        """Test getting non-existent ticket."""
        with pytest.raises(ValueError, match='Ticket not found'):
            SupportService.get_ticket('invalid-id')
    
    def test_get_open_tickets(self, app_context, test_customer):
        """Test getting all open tickets."""
        # Create multiple tickets
        for i in range(3):
            SupportService.create_ticket(
                customer_id=test_customer.id,
                subject=f'Issue {i}',
                description=f'Description for issue {i}'
            )
        
        result = SupportService.get_open_tickets(limit=10)
        
        assert result['total_count'] == 3
        assert len(result['tickets']) == 3
    
    def test_get_customer_tickets(self, app_context, test_customer):
        """Test getting tickets for a customer."""
        # Create multiple tickets
        for i in range(2):
            SupportService.create_ticket(
                customer_id=test_customer.id,
                subject=f'Issue {i}',
                description=f'Description for issue {i}'
            )
        
        result = SupportService.get_customer_tickets(test_customer.id, limit=10)
        
        assert result['total_count'] == 2
        assert len(result['tickets']) == 2
    
    def test_get_customer_tickets_not_found(self, app_context):
        """Test getting tickets for non-existent customer."""
        with pytest.raises(ValueError, match='Customer not found'):
            SupportService.get_customer_tickets(999)
    
    def test_update_ticket_status_success(self, app_context, test_customer, test_agent):
        """Test successful ticket status update."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        result = SupportService.update_ticket_status(
            ticket_id=ticket_result['ticket_id'],
            new_status='in_progress',
            agent_id=test_agent.id
        )
        
        assert result['success'] is True
        assert result['status'] == 'in_progress'
    
    def test_update_ticket_status_invalid_status(self, app_context, test_customer, test_agent):
        """Test ticket status update with invalid status."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        with pytest.raises(ValueError, match='Invalid status'):
            SupportService.update_ticket_status(
                ticket_id=ticket_result['ticket_id'],
                new_status='invalid',
                agent_id=test_agent.id
            )
    
    def test_update_ticket_status_not_found(self, app_context, test_agent):
        """Test ticket status update for non-existent ticket."""
        with pytest.raises(ValueError, match='Ticket not found'):
            SupportService.update_ticket_status(
                ticket_id='invalid-id',
                new_status='resolved',
                agent_id=test_agent.id
            )
    
    def test_add_note_success(self, app_context, test_customer, test_agent):
        """Test successful note addition."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        result = SupportService.add_note(
            ticket_id=ticket_result['ticket_id'],
            user_id=test_agent.id,
            note='We are investigating this issue'
        )
        
        assert result['success'] is True
        assert result['note'] == 'We are investigating this issue'
    
    def test_add_note_empty(self, app_context, test_customer, test_agent):
        """Test adding empty note."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        with pytest.raises(ValueError, match='Note cannot be empty'):
            SupportService.add_note(
                ticket_id=ticket_result['ticket_id'],
                user_id=test_agent.id,
                note=''
            )
    
    def test_add_note_user_not_found(self, app_context, test_customer):
        """Test adding note with non-existent user."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        with pytest.raises(ValueError, match='User not found'):
            SupportService.add_note(
                ticket_id=ticket_result['ticket_id'],
                user_id=999,
                note='Test note'
            )
    
    def test_add_note_ticket_not_found(self, app_context, test_agent):
        """Test adding note to non-existent ticket."""
        with pytest.raises(ValueError, match='Ticket not found'):
            SupportService.add_note(
                ticket_id='invalid-id',
                user_id=test_agent.id,
                note='Test note'
            )
    
    def test_assign_ticket_success(self, app_context, test_customer, test_agent):
        """Test successful ticket assignment."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        # Create admin user
        admin_result = AuthService.register_user(
            username='admin',
            email='admin@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Admin'
        )
        admin = User.query.get(admin_result['user_id'])
        admin.role = UserRole.ADMIN
        db.session.commit()
        
        result = SupportService.assign_ticket(
            ticket_id=ticket_result['ticket_id'],
            agent_id=test_agent.id,
            admin_id=admin.id
        )
        
        assert result['success'] is True
        assert result['assigned_agent_id'] == test_agent.id
    
    def test_assign_ticket_invalid_agent(self, app_context, test_customer):
        """Test ticket assignment to non-support agent."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        # Create admin user
        admin_result = AuthService.register_user(
            username='admin',
            email='admin@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Admin'
        )
        admin = User.query.get(admin_result['user_id'])
        admin.role = UserRole.ADMIN
        db.session.commit()
        
        # Try to assign to customer (not support agent)
        with pytest.raises(ValueError, match='Invalid support agent'):
            SupportService.assign_ticket(
                ticket_id=ticket_result['ticket_id'],
                agent_id=test_customer.id,
                admin_id=admin.id
            )
    
    def test_ticket_with_multiple_notes(self, app_context, test_customer, test_agent):
        """Test ticket with multiple notes."""
        ticket_result = SupportService.create_ticket(
            customer_id=test_customer.id,
            subject='Account Issue',
            description='I cannot access my account'
        )
        
        # Add multiple notes
        for i in range(3):
            SupportService.add_note(
                ticket_id=ticket_result['ticket_id'],
                user_id=test_agent.id,
                note=f'Note {i}'
            )
        
        result = SupportService.get_ticket(ticket_result['ticket_id'])
        
        assert len(result['notes']) == 3
