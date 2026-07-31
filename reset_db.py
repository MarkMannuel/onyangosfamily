import os
import shutil
import time

# Remove database file and instance directory
db_path = "instance/family_database.db"
instance_path = "instance"

# Wait a bit for any locks to be released
time.sleep(1)

try:
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed {db_path}")
except Exception as e:
    print(f"Could not remove database file: {e}")

try:
    if os.path.exists(instance_path):
        shutil.rmtree(instance_path)
        print(f"Removed {instance_path} directory")
except Exception as e:
    print(f"Could not remove instance directory: {e}")

# Now create the database fresh
from app import app, db, Admin, GuestInvitation
from datetime import datetime

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    
    # Create admin user
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', email='admin@family.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")
    
    # Create a test invitation
    if not GuestInvitation.query.first():
        invitation = GuestInvitation()
        invitation.code = invitation.generate_code()
        invitation.email = "guest@example.com"
        invitation.expires_at = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        invitation.created_by = 1
        db.session.add(invitation)
        db.session.commit()
        print(f"Test invitation code created: {invitation.code}")

print("Database reset complete!")
