from app import create_app, db
from app.models import User, UserRole

app = create_app()
with app.app_context():
    # Change test1 to customer
    test1 = User.query.filter_by(username='test1').first()
    
    if test1:
        print(f'Changing {test1.username} from {test1.role.value} to customer')
        test1.role = UserRole.CUSTOMER
        db.session.commit()
        print(f'✓ User {test1.username} is now a {test1.role.value}')
    else:
        print('test1 user not found')
    
    # List all users with roles
    print('\n=== All Users and Roles ===')
    for user in User.query.all():
        print(f'{user.username:15} - {user.role.value:15} ({user.email})')
