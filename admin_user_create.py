from app import db, User, Role, user_datastore, encrypt_password, app
from datetime import datetime
from flask import Flask, current_app

def create_admin_user_to_db():
    print(db.session.query(User).count())
    user = User.query.filter(User.email == "admin").first()
    user_role = Role.query.filter(Role.name == "user").first()
    super_user_role = Role.query.filter(Role.name == "superuser").first()

    if not user_role:
        user_role = Role(name="user")
        db.session.add(user_role)
        db.session.commit()

    if not super_user_role:
        super_user_role = Role(name="superuser")
        db.session.add(super_user_role)
        db.session.commit()

    if not user:
        now = datetime.now()

        user_datastore.create_user(
            email='admin',
            password=encrypt_password('8Lapis6Luna'),
            connect_date = now,
            roles=[user_role, super_user_role]
        )
        db.session.commit()
        print("admin user created")

def main():
    with app.app_context():
        #print(current_app.name)
        create_admin_user_to_db()

if __name__ == '__main__':
    main()
