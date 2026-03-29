from flask import Blueprint, request, jsonify, session
from app.models import db, Student, RiskScore, StudentDataSnapshot
from app.chatbot import get_chatbot_response, analyze_student_needs

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/search-students', methods=['GET'])
def search_students():
    """Search for students"""
    query = request.args.get('q', '').lower()
    risk_filter = request.args.get('risk', 'all')
    
    students_query = db.session.query(Student, RiskScore).join(
        RiskScore, Student.id == RiskScore.student_id
    )
    
    if query:
        students_query = students_query.filter(Student.name.ilike(f'%{query}%'))
    
    if risk_filter != 'all':
        students_query = students_query.filter(RiskScore.risk_level == risk_filter.upper())
    
    results = students_query.limit(50).all()
    
    data = [{
        'id': student.id,
        'name': student.name,
        'grade': student.grade,
        'risk_level': risk_score.risk_level,
        'risk_score': risk_score.risk_score,
        'pattern': risk_score.pattern or 'No pattern'
    } for student, risk_score in results]
    
    return jsonify(data)

@api_bp.route('/dashboard-stats')
def dashboard_stats():
    """Get dashboard statistics"""
    from app.analytics import calculate_dashboard_stats
    stats = calculate_dashboard_stats()
    return jsonify(stats)

@api_bp.route('/student/<int:student_id>/ai-insight', methods=['GET'])
def student_ai_insight(student_id):
    """Get AI insights for a student"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        latest_risk = RiskScore.query.filter_by(student_id=student_id).order_by(
            RiskScore.scored_at.desc()
        ).first()
        
        latest_snapshot = StudentDataSnapshot.query.filter_by(student_id=student_id).order_by(
            StudentDataSnapshot.created_at.desc()
        ).first()
        
        if not latest_risk or not latest_snapshot:
            return jsonify({'analysis': ['⏳ Insufficient data to generate insights yet.']})
        
        # Create analysis data
        student_data = {
            'name': student.name,
            'grade': student.grade,
            'risk_level': latest_risk.risk_level,
            'risk_score': latest_risk.risk_score,
            'key_signals': latest_risk.signals,
            'pattern': latest_risk.pattern,
            'attendance_rate': latest_snapshot.attendance,
            'teacher_rating': latest_snapshot.teacher_rating,
            'num_friends': latest_snapshot.num_friends,
            'ias': latest_snapshot.ias,
            'fee_status': latest_snapshot.fee_status,
            'counseling_visits': latest_snapshot.counseling_visits,
            'teacher_notes': latest_snapshot.teacher_notes,
            'mental_health_summary': latest_snapshot.mental_health_summary,
        }
        
        # Generate analysis
        analysis_result = analyze_student_needs(student_data)
        
        # Format response
        analysis_lines = [
            f"📊 **Risk Status**: {analysis_result.get('urgency')} - {analysis_result.get('risk_description')}",
            "",
            f"📍 **Attendance**: {analysis_result.get('attendance_issue')}",
            f"⭐ **Teacher Feedback**: {analysis_result.get('teacher_concern')}",
        ]
        
        if analysis_result.get('has_warning_signals'):
            analysis_lines.append("")
            analysis_lines.append("🚨 **Warning Signals Detected**:")
            for signal in analysis_result.get('warning_signals', []):
                analysis_lines.append(f"  • {signal}")
        
        analysis_lines.append("")
        analysis_lines.append("💡 **Recommended Support**:")
        for help_type in analysis_result.get('help_types', []):
            analysis_lines.append(f"  • {help_type}")
        
        return jsonify({'analysis': analysis_lines})
    
    except Exception as e:
        return jsonify({'error': str(e), 'analysis': ['❌ Error generating insights']}), 500

@api_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """Chatbot endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        response = get_chatbot_response(user_message, db.session)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500