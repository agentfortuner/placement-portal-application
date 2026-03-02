from flask import Flask
from application.database import db
from flask import current_app as app
#used this to create the db app, iske wajeh se error aa rha tha

def create_app():
    app = Flask(__name__) 
    app.debug = True
    app.secret_key = "afgjke12359754iloyuremane45j"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.sqlite3'
    db.init_app(app)

    return app

app = create_app()

# models yaha se create hua
with app.app_context():
    from application import models 
    import application.controllers

    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)