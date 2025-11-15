from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    print('Converting all usernames to lowercase...')
    
    users = User.query.all()
    updated_count = 0
    
    for user in users:
        original = user.username
        lowercase = user.username.lower()
        
        if original != lowercase:
            # Check if lowercase version already exists
            existing = User.query.filter(
                db.func.lower(User.username) == lowercase,
                User.id != user.id
            ).first()
            
            if existing:
                print(f'⚠️  Cannot convert {original} to {lowercase} - already exists!')
            else:
                user.username = lowercase
                updated_count += 1
                print(f'✓ Converted: {original} → {lowercase}')
        else:
            print(f'  Already lowercase: {original}')
    
    if updated_count > 0:
        db.session.commit()
        print(f'\n✓ Successfully converted {updated_count} username(s) to lowercase')
    else:
        print('\n✓ All usernames are already lowercase')
    
    print('\n=== Current Users ===')
    for user in User.query.all():
        print(f'{user.username} - {user.role.value}')
