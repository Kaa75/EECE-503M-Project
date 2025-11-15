from app import create_app, db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check for existing support agent
    support_agent = User.query.filter_by(role=UserRole.SUPPORT_AGENT).first()
    
    if support_agent:
        print(f'Support agent already exists: {support_agent.username}')
    else:
        print('No support agent found. Creating one...')
        
        # Create support agent
        agent = User(
            username='agent1',
            email='agent1@example.com',
            phone='555-0103',
            password_hash=generate_password_hash('Password123!'),
            full_name='Support Agent',
            role=UserRole.SUPPORT_AGENT,
            is_active=True
        )
        
        db.session.add(agent)
        db.session.commit()
        
        print(f'✓ Support agent created: {agent.username}')
        print(f'  Email: {agent.email}')
        print(f'  Password: Password123!')
        print(f'  Role: {agent.role.value}')
    
    # List all users
    print('\n=== All Users ===')
    for user in User.query.all():
        print(f'{user.username} ({user.email}) - {user.role.value}')
