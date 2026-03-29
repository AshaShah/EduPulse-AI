from flask import Blueprint, render_template, session, redirect, url_for
from app.decorators import login_required
from app.models import db, Student, RiskScore, StudentDataSnapshot
import json

students_bp = Blueprint('students', __name__)

@students_bp.route('/student/<int:student_id>')
@login_required
def profile(student_id):
    """Student profile page"""
    student = Student.query.get_or_404(student_id)
    
    risk_score = RiskScore.query.filter_by(student_id=student_id).order_by(
        RiskScore.scored_at.desc()
    ).first()
    
    snapshot = StudentDataSnapshot.query.filter_by(student_id=student_id).order_by(
        StudentDataSnapshot.created_at.desc()
    ).first()
    
    # Parse attendance
    attendance_data = []
    if snapshot and snapshot.attendance_json:
        try:
            attendance_data = json.loads(snapshot.attendance_json)
        except:
            pass
    
    student_data = {
        'id': student.id,
        'name': student.name,
        'address': student.address,
        'email': student.email,
        'grade': student.grade,
        'travel_time': student.travel_time,
        'father_occupation': student.father_occupation,
        'mother_occupation': student.mother_occupation,
        'father_education': student.father_education,
        'mother_education': student.mother_education,
    }
    
    if snapshot:
        student_data.update({
            'ias': snapshot.ias,
            'attendance': snapshot.attendance,
            'fee_status': snapshot.fee_status,
            'teacher_rating': snapshot.teacher_rating,
            'teacher_notes': snapshot.teacher_notes,
            'num_friends': snapshot.num_friends,
            'counseling_visits': snapshot.counseling_visits,
            'mental_health_summary': snapshot.mental_health_summary,
        })
    
    if risk_score:
        student_data.update({
            'risk_level': risk_score.risk_level,
            'risk_score': risk_score.risk_score,
            'pattern': risk_score.pattern,
            'key_signals': risk_score.signals,
            'counselor_action': risk_score.counselor_action,
        })
    
    return render_template('profile.html',
                         student=student_data,
                         attendance_data=attendance_data)