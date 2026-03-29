from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='counselor')
    name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    address = db.Column(db.String(255))
    email = db.Column(db.String(120))
    grade = db.Column(db.Integer)
    travel_time = db.Column(db.Float, default=0)
    father_occupation = db.Column(db.String(120))
    mother_occupation = db.Column(db.String(120))
    father_education = db.Column(db.String(50))
    mother_education = db.Column(db.String(50))
    counselor_email = db.Column(db.String(120))
    parent_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    snapshots = db.relationship('StudentDataSnapshot', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    risk_scores = db.relationship('RiskScore', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name}>'

class StudentDataSnapshot(db.Model):
    __tablename__ = 'student_data_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    # Academic Performance
    ias = db.Column(db.Float, default=0)
    twp = db.Column(db.Float, default=0)
    tnp = db.Column(db.Float, default=0)
    arr = db.Column(db.String(1), default='N')
    
    # Attendance & Finance
    attendance = db.Column(db.Float, default=0)
    fee_status = db.Column(db.String(50), default='Paid')
    teacher_rating = db.Column(db.Float, default=3)
    
    # Engagement & Wellbeing
    teacher_notes = db.Column(db.Text)
    num_friends = db.Column(db.Integer, default=0)
    counseling_visits = db.Column(db.Integer, default=0)
    mental_health_summary = db.Column(db.Text)
    
    # Assignment Data
    assignments_json = db.Column(db.Text, default='[]')
    
    # Attendance History
    attendance_json = db.Column(db.Text, default='[]')
    
    # Raw CSV Data
    raw_data = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f'<StudentDataSnapshot {self.student_id}>'
    
    @property
    def assignments(self):
        try:
            return json.loads(self.assignments_json or '[]')
        except:
            return []
    
    @assignments.setter
    def assignments(self, value):
        self.assignments_json = json.dumps(value)

class RiskScore(db.Model):
    __tablename__ = 'risk_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    risk_score = db.Column(db.Float, default=0)
    risk_level = db.Column(db.String(50), default='LOW')
    pattern = db.Column(db.Text)
    key_signals = db.Column(db.Text, default='[]')
    counselor_action = db.Column(db.Text)
    notes = db.Column(db.Text)  # ✅ ADD THIS COLUMN
    
    scored_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f'<RiskScore {self.student_id} - {self.risk_level}>'
    
    @property
    def signals(self):
        try:
            return json.loads(self.key_signals or '[]')
        except:
            return []

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    
    id = db.Column(db.Integer, primary_key=True)
    uploaded_by = db.Column(db.String(120))
    file_name = db.Column(db.String(255), nullable=False)
    record_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    new_students = db.Column(db.Integer, default=0)          # ✅ ADD THIS COLUMN
    updated_students = db.Column(db.Integer, default=0)      # ✅ ADD THIS COLUMN
    errors = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f'<UploadHistory {self.file_name}>'