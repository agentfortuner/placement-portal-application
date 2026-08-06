from flask import Flask, redirect, url_for
from flask_login import LoginManager
from application.database import db
from application.models import User, Company

import os
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError


login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "afgjke12359754iloyuremane45j")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/placement_portal.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

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


# Root redirect → /home
@app.route("/")
def index():
    return redirect(url_for("home"))


def init_db():
    """Create tables and seed the manager user. Safe to call multiple times."""
    try:
        with app.app_context():
            db.create_all()

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
    except Exception as e:
        print("DB init error (non-fatal):", e)


# Initialize DB at module load (works for Vercel serverless and direct run)
init_db()


if __name__ == "__main__":
    app.run(debug=True)