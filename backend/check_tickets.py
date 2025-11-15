from app import create_app, db
from app.models import User, UserRole, SupportTicket, TicketStatus

app = create_app()
with app.app_context():
    print('=== Database Status ===')
    print(f'Users: {User.query.count()}')
    print(f'Support Tickets: {SupportTicket.query.count()}')
    
    print('\n=== User Roles ===')
    for user in User.query.all():
        print(f'{user.username} - {user.role.value}')
    
    print('\n=== Existing Tickets ===')
    tickets = SupportTicket.query.all()
    if tickets:
        for ticket in tickets:
            print(f'Ticket {ticket.ticket_id[:8]} - {ticket.subject} - {ticket.status.value}')
    else:
        print('No tickets found')
