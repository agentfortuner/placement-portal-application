from .database import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String, nullable=False, default="user")
    isBlacklisted = db.Column(db.Boolean, nullable=False, default=False)

    #Relationships
    student = db.relationship('Student', backref='user', uselist=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rollNumber = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    yearOfStudy = db.Column(db.Integer, nullable=False)

class Company(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    # Details
    category = db.Column(db.String(50), nullable=False) # Gold, Silver, etc.
    scale = db.Column(db.String(50), nullable=False)    # MNC, Startup, etc.
    description = db.Column(db.Text, nullable=True)
    placementHistory = db.Column(db.Text, nullable=True)
    
    # Contact Info
    address = db.Column(db.String(100), nullable=True)
    locations = db.Column(db.String(200), nullable=True)
    website = db.Column(db.String(100), nullable=True)
    contactName = db.Column(db.String(100), nullable=True)
    contactEmail = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    isBlacklisted = db.Column(db.Boolean, nullable=False, default=False)
    # Relationship to drives (assuming Drive model exists)
    drives = db.relationship('Drive', backref='company', lazy=True)


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    companyId = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    eligibilityCriteria = db.Column(db.Text, nullable=True)
    applicationDeadline = db.Column(db.DateTime, nullable=False)
    vacancy = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    hiringStatus = db.Column(db.String(50), nullable=False, default="Hiring")
    adminStatus = db.Column(db.String(50), nullable=False, default="Pending")
    applications = db.relationship('Application', backref='drive', lazy=True)
    interviewrounds = db.Column(db.Integer, nullable=False, default="2")


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentId = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    driveId = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    applicationDate = db.Column(db.DateTime, nullable=False)
    gpa = db.Column(db.Float, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Applied")