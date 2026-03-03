from flask import Flask
from flask_login import LoginManager
from application.database import db
from application.models import User, Company

import os
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError


login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "afgjke12359754iloyuremane45j"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.debug = True

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None

        try:
            uid = int(user_id)
        except Exception:
            return None

        user = User.query.get(uid)
        if user:
            return user

        return Company.query.get(uid)

    return app


app = create_app()

# Import routes AFTER app creation
from application.controllers import *


if __name__ == "__main__":

    with app.app_context():

        # Create tables
        db.create_all()

        # Prevent double execution in debug mode
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:

            manager_username = "manager"
            manager_email = "manager@user.com"
            manager_password = "manager143"

            norm_email = manager_email.strip().lower()

            existing = User.query.filter(
                or_(
                    User.username == manager_username,
                    (User.email != None) &
                    (db.func.lower(db.func.trim(User.email)) == norm_email),
                )
            ).first()

            if existing:
                print("Manager already exists - skipping creation.")
            else:
                manager = User(
                    name="Manager",
                    email=norm_email,
                    username=manager_username,
                    password=manager_password,
                    type="manager"
                )

                db.session.add(manager)
                try:
                    db.session.commit()
                    print("Manager user created successfully.")
                except IntegrityError as e:
                    db.session.rollback()
                    print("Could not create manager user:", e)

    app.run(debug=True)