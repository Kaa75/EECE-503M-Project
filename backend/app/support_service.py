from datetime import datetime
from app.models import (
    SupportTicket, TicketNote, User, UserRole, TicketStatus, AuditAction, db
)
from app.security import log_audit, sanitize_input

class SupportService:
    """Service for handling customer support tickets."""
    
    @staticmethod
    def create_ticket(customer_id: int, subject: str, description: str) -> dict:
        """
        Create a new support ticket.
        
        Args:
            customer_id: ID of the customer creating the ticket
            subject: Ticket subject
            description: Detailed description of the issue
            
        Returns:
            Dictionary with ticket data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate customer exists
        customer = User.query.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        # Validate inputs
        if not subject or len(subject) < 5:
            raise ValueError("Subject must be at least 5 characters")
        
        if not description or len(description) < 10:
            raise ValueError("Description must be at least 10 characters")
        
        try:
            # Sanitize inputs
            subject = sanitize_input(subject, 255)
            description = sanitize_input(description, 2000)
            
            # Create ticket
            ticket = SupportTicket(
                customer_id=customer_id,
                subject=subject,
                description=description,
                status=TicketStatus.OPEN
            )
            
            db.session.add(ticket)
            db.session.commit()
            
            log_audit(
                user_id=customer_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='ticket',
                resource_id=ticket.ticket_id,
                details=f'Support ticket created: {subject}'
            )
            
            return {
                'success': True,
                'ticket_id': ticket.ticket_id,
                'subject': ticket.subject,
                'status': ticket.status.value,
                'created_at': ticket.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create ticket: {str(e)}")
    
    @staticmethod
    def get_ticket(ticket_id: str) -> dict:
        """
        Get ticket details.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Dictionary with ticket data
            
        Raises:
            ValueError: If ticket not found
        """
        ticket = SupportTicket.query.filter_by(ticket_id=ticket_id).first()
        
        if not ticket:
            raise ValueError("Ticket not found")
        
        return {
            'ticket_id': ticket.ticket_id,
            'customer_id': ticket.customer_id,
            'customer_name': ticket.customer.full_name,
            'assigned_agent_id': ticket.assigned_agent_id,
            'assigned_agent_name': ticket.assigned_agent.full_name if ticket.assigned_agent else None,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status.value,
            'created_at': ticket.created_at.isoformat(),
            'updated_at': ticket.updated_at.isoformat(),
            'notes': [
                {
                    'note_id': note.id,
                    'user_id': note.author_id,
                    'user_name': note.author.full_name,
                    'note': note.content,
                    'created_at': note.created_at.isoformat()
                }
                for note in ticket.notes
            ]
        }
    
    @staticmethod
    def get_open_tickets(limit: int = 10, offset: int = 0) -> dict:
        """
        Get all open support tickets.
        
        Args:
            limit: Maximum number of tickets to return
            offset: Number of tickets to skip
            
        Returns:
            Dictionary with ticket list
        """
        tickets = SupportTicket.query.filter_by(status=TicketStatus.OPEN).order_by(
            SupportTicket.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        total_count = SupportTicket.query.filter_by(status=TicketStatus.OPEN).count()
        
        return {
            'tickets': [
                {
                    'ticket_id': t.ticket_id,
                    'customer_id': t.customer_id,
                    'customer_name': t.customer.full_name,
                    'subject': t.subject,
                    'status': t.status.value,
                    'created_at': t.created_at.isoformat()
                }
                for t in tickets
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

    @staticmethod
    def get_tickets_by_status(status: str, limit: int = 10, offset: int = 0) -> dict:
        """
        Get all tickets filtered by status (open/in_progress/resolved).

        Args:
            status: Ticket status to filter
            limit: Maximum number of tickets to return
            offset: Number of tickets to skip

        Returns:
            Dictionary with ticket list
        """
        try:
            ticket_status = TicketStatus[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

        tickets = SupportTicket.query.filter_by(status=ticket_status).order_by(
            SupportTicket.created_at.desc()
        ).limit(limit).offset(offset).all()

        total_count = SupportTicket.query.filter_by(status=ticket_status).count()

        return {
            'tickets': [
                {
                    'ticket_id': t.ticket_id,
                    'customer_id': t.customer_id,
                    'customer_name': t.customer.full_name,
                    'subject': t.subject,
                    'status': t.status.value,
                    'created_at': t.created_at.isoformat()
                }
                for t in tickets
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_customer_tickets(customer_id: int, limit: int = 10, offset: int = 0) -> dict:
        """
        Get all tickets for a customer.
        
        Args:
            customer_id: ID of the customer
            limit: Maximum number of tickets to return
            offset: Number of tickets to skip
            
        Returns:
            Dictionary with ticket list
            
        Raises:
            ValueError: If customer not found
        """
        customer = User.query.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        tickets = SupportTicket.query.filter_by(customer_id=customer_id).order_by(
            SupportTicket.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        total_count = SupportTicket.query.filter_by(customer_id=customer_id).count()
        
        # Return enriched ticket objects to align with frontend SupportTicket interface expectations
        return {
            'customer_id': customer_id,
            'tickets': [
                {
                    'id': t.id,
                    'ticket_id': t.ticket_id,
                    'customer_id': t.customer_id,
                    'customer_name': t.customer.full_name,
                    'assigned_agent_id': t.assigned_agent_id,
                    'assigned_agent_name': t.assigned_agent.full_name if t.assigned_agent else None,
                    'subject': t.subject,
                    'description': t.description,
                    'status': t.status.value,
                    'priority': t.priority,
                    'created_at': t.created_at.isoformat(),
                    'updated_at': t.updated_at.isoformat(),
                    'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None,
                    # Do not include notes list here for efficiency (details endpoint supplies them)
                    'notes': []
                }
                for t in tickets
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def update_ticket_status(ticket_id: str, new_status: str, agent_id: int) -> dict:
        """
        Update ticket status.
        
        Args:
            ticket_id: ID of the ticket
            new_status: New status (open/in_progress/resolved)
            agent_id: ID of the agent updating the status
            
        Returns:
            Dictionary with updated ticket data
            
        Raises:
            ValueError: If validation fails
        """
        ticket = SupportTicket.query.filter_by(ticket_id=ticket_id).first()
        
        if not ticket:
            raise ValueError("Ticket not found")
        
        # Validate status
        try:
            status = TicketStatus[new_status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {new_status}")
        
        try:
            ticket.status = status
            ticket.assigned_agent_id = agent_id
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=agent_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='ticket',
                resource_id=ticket_id,
                details=f'Ticket status updated to: {new_status}'
            )
            
            return {
                'success': True,
                'ticket_id': ticket.ticket_id,
                'status': ticket.status.value,
                'updated_at': ticket.updated_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to update ticket: {str(e)}")
    
    @staticmethod
    def add_note(ticket_id: str, user_id: int, note: str) -> dict:
        """
        Add a note to a support ticket.
        
        Args:
            ticket_id: ID of the ticket
            user_id: ID of the user adding the note
            note: Note content
            
        Returns:
            Dictionary with note data
            
        Raises:
            ValueError: If validation fails
        """
        ticket = SupportTicket.query.filter_by(ticket_id=ticket_id).first()
        
        if not ticket:
            raise ValueError("Ticket not found")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate note
        if not note or len(note) < 1:
            raise ValueError("Note cannot be empty")
        
        try:
            # Sanitize note
            note = sanitize_input(note, 2000)
            
            # Create note
            ticket_note = TicketNote(
                ticket_id=ticket.id,
                author_id=user_id,
                content=note
            )
            
            db.session.add(ticket_note)
            db.session.commit()
            
            log_audit(
                user_id=user_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='ticket',
                resource_id=ticket_id,
                details='Note added to ticket'
            )
            
            return {
                'success': True,
                'note_id': ticket_note.id,
                'ticket_id': ticket_id,
                'user_id': user_id,
                'note': ticket_note.content,
                'created_at': ticket_note.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to add note: {str(e)}")
    
    @staticmethod
    def assign_ticket(ticket_id: str, agent_id: int, admin_id: int) -> dict:
        """
        Assign a ticket to a support agent.
        
        Args:
            ticket_id: ID of the ticket
            agent_id: ID of the support agent
            admin_id: ID of the admin assigning the ticket
            
        Returns:
            Dictionary with updated ticket data
            
        Raises:
            ValueError: If validation fails
        """
        ticket = SupportTicket.query.filter_by(ticket_id=ticket_id).first()
        
        if not ticket:
            raise ValueError("Ticket not found")
        
        agent = User.query.get(agent_id)
        if not agent or agent.role != UserRole.SUPPORT_AGENT:
            raise ValueError("Invalid support agent")
        
        try:
            ticket.assigned_agent_id = agent_id
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='ticket',
                resource_id=ticket_id,
                details=f'Ticket assigned to agent: {agent.full_name}'
            )
            
            return {
                'success': True,
                'ticket_id': ticket.ticket_id,
                'assigned_agent_id': ticket.assigned_agent_id,
                'assigned_agent_name': agent.full_name
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to assign ticket: {str(e)}")
