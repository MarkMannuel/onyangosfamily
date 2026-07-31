import os
from app import app, db, create_admin

DB_PATH = 'family_database.db'

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f'Removed {DB_PATH}')

with app.app_context():
    db.create_all()
    create_admin()
    print('Database recreated and admin user ensured.')
