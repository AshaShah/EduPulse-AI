from flask import Blueprint, render_template, session, redirect, url_for
from app.decorators import login_required
from app.models import db, Student, RiskScore
from app.analytics import calculate_dashboard_stats

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    stats = calculate_dashboard_stats()
    
    # Get at-risk students
    at_risk_students = db.session.query(Student, RiskScore).join(
        RiskScore, Student.id == RiskScore.student_id
    ).filter(RiskScore.risk_level.in_(['HIGH', 'MEDIUM'])).order_by(
        RiskScore.risk_score.desc()
    ).limit(10).all()
    
    students_data = []
    for student, risk_score in at_risk_students:
        students_data.append({
            'id': student.id,
            'name': student.name,
            'grade': student.grade,
            'risk_level': risk_score.risk_level,
            'risk_score': risk_score.risk_score,
            'pattern': risk_score.pattern or 'No pattern detected'
        })
    
    return render_template('dashboard.html',
                         stats=stats,
                         students=students_data,
                         user_name=session.get('user_name'))