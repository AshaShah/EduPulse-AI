from app.models import db, Student, RiskScore, StudentDataSnapshot
from datetime import datetime
import json

def calculate_dashboard_stats():
    """Calculate dashboard overview statistics"""
    total_students = Student.query.count()
    
    high_risk = db.session.query(RiskScore).filter(
        RiskScore.risk_level == 'HIGH'
    ).count()
    
    medium_risk = db.session.query(RiskScore).filter(
        RiskScore.risk_level == 'MEDIUM'
    ).count()
    
    low_risk = db.session.query(RiskScore).filter(
        RiskScore.risk_level == 'LOW'
    ).count()
    
    all_snapshots = db.session.query(StudentDataSnapshot).all()
    avg_attendance = 0
    avg_rating = 0
    
    if all_snapshots:
        # Accepts 0, None, and decimal (0-1) or percent (0-100)
        attendance_values = [float(s.attendance) for s in all_snapshots if s.attendance is not None]
        rating_values = [float(s.teacher_rating) for s in all_snapshots if s.teacher_rating is not None and s.teacher_rating > 0]

        if attendance_values:
            max_att = max(attendance_values)
            min_att = min(attendance_values)
            # If all values are 0, average is 0
            if max_att == 0 and min_att == 0:
                avg_attendance = 0.0
            else:
                # If max is <= 1, treat as fraction and scale to percent
                if max_att <= 1:
                    attendance_values = [v * 100 for v in attendance_values]
                avg_attendance = round(sum(attendance_values) / len(attendance_values), 2)

        if rating_values:
            avg_rating = round(sum(rating_values) / len(rating_values), 2)
    
    high_risk_percentage = (high_risk / total_students * 100) if total_students > 0 else 0
    
    return {
        'total_students': total_students,
        'high_risk_count': high_risk,
        'medium_risk_count': medium_risk,
        'low_risk_count': low_risk,
        'high_risk_percentage': round(high_risk_percentage, 1),
        'avg_attendance': avg_attendance,  # ✅ Now shows % correctly
        'avg_rating': avg_rating,
        'risk_distribution': {
            'high': high_risk,
            'medium': medium_risk,
            'low': low_risk
        }
    }

def calculate_risk_score(student_id):
    """Calculate risk score based on student data"""
    student = Student.query.get(student_id)
    snapshot = StudentDataSnapshot.query.filter_by(student_id=student_id).order_by(
        StudentDataSnapshot.created_at.desc()
    ).first()
    
    if not snapshot:
        risk_score_value = 20
        risk_level = 'LOW'
        key_signals = ['Insufficient data']
    else:
        risk_score_value = 0
        key_signals = []
        
        # Safely convert values to float
        attendance = float(snapshot.attendance) if snapshot.attendance is not None else 0
        ias = float(snapshot.ias) if snapshot.ias is not None else 0
        teacher_rating = float(snapshot.teacher_rating) if snapshot.teacher_rating is not None else 0
        num_friends = int(snapshot.num_friends) if snapshot.num_friends is not None else 0
        counseling_visits = int(snapshot.counseling_visits) if snapshot.counseling_visits is not None else 0
        
        # Attendance risk (0-25 points)
        if attendance < 75:
            risk_score_value += 25
            key_signals.append('🔴 Low attendance (<75%)')
        elif attendance < 85:
            risk_score_value += 15
            key_signals.append('🟡 Below average attendance')
        
        # Academic performance risk (0-30 points)
        if ias < 40:
            risk_score_value += 30
            key_signals.append('🔴 Critical academic performance')
        elif ias < 50:
            risk_score_value += 25
            key_signals.append('🔴 Low internal assessment score')
        elif ias < 60:
            risk_score_value += 15
            key_signals.append('🟡 Below average performance')
        
        # Teacher rating risk (0-20 points)
        if teacher_rating < 2:
            risk_score_value += 20
            key_signals.append('🔴 Low teacher rating')
        elif teacher_rating < 3:
            risk_score_value += 10
            key_signals.append('🟡 Below average teacher rating')
        
        # Fee status risk (0-15 points)
        fee_status = str(snapshot.fee_status).strip() if snapshot.fee_status else ''
        if 'Overdue' in fee_status:
            risk_score_value += 15
            key_signals.append('🔴 Overdue fee payment')
        
        # Social engagement risk (0-15 points)
        if num_friends < 2:
            risk_score_value += 15
            key_signals.append('🔴 Social isolation (<2 friends)')
        elif num_friends < 3:
            risk_score_value += 8
            key_signals.append('🟡 Limited social connections')
        
        # Counseling frequency (0-10 points)
        if counseling_visits > 5:
            risk_score_value += 10
            key_signals.append('🟡 Frequent counseling visits')
        
        # Failed exam (0-5 points)
        arr = str(snapshot.arr).strip().upper() if snapshot.arr else 'N'
        if arr == 'Y':
            risk_score_value += 5
            key_signals.append('🟡 Previous exam failure')
        
        # Cap the score at 100
        risk_score_value = min(risk_score_value, 100)
        
        # Determine risk level
        if risk_score_value >= 70:
            risk_level = 'HIGH'
        elif risk_score_value >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
    
    pattern = _determine_pattern(snapshot) if snapshot else 'Insufficient data'
    counselor_action = _suggest_action(risk_level, snapshot)
    
    risk_record = RiskScore(
        student_id=student_id,
        risk_score=risk_score_value,
        risk_level=risk_level,
        pattern=pattern,
        key_signals=json.dumps(key_signals),
        counselor_action=counselor_action,
        scored_at=datetime.now()
    )
    
    return risk_record

def _determine_pattern(snapshot):
    """Determine student behavior pattern"""
    if not snapshot:
        return 'Insufficient data'
    
    patterns = []
    
    # Safely convert values
    attendance = float(snapshot.attendance) if snapshot.attendance is not None else 0
    ias = float(snapshot.ias) if snapshot.ias is not None else 0
    teacher_rating = float(snapshot.teacher_rating) if snapshot.teacher_rating is not None else 0
    num_friends = int(snapshot.num_friends) if snapshot.num_friends is not None else 0
    
    if attendance < 80 and ias < 60:
        patterns.append('Declining academic and attendance pattern')
    elif attendance > 90 and ias > 75:
        patterns.append('Strong engagement and academic performance')
    elif ias < 50:
        patterns.append('Struggling academically')
    elif attendance < 75:
        patterns.append('Poor school attendance')
    elif num_friends < 2 and ias < 60:
        patterns.append('Social isolation with academic struggles')
    elif teacher_rating < 2:
        patterns.append('Behavioral concerns in classroom')
    
    return ' | '.join(patterns) if patterns else 'Stable engagement'

def _suggest_action(risk_level, snapshot):
    """Suggest counselor action based on risk level"""
    base_action = ''
    
    if risk_level == 'HIGH':
        base_action = ' URGENT: Schedule immediate meeting with student and parents'
    elif risk_level == 'MEDIUM':
        base_action = ' Close monitoring recommended - Schedule weekly check-ins'
    else:
        base_action = ' Continue regular monitoring'
    
    if snapshot:
        attendance = float(snapshot.attendance) if snapshot.attendance is not None else 0
        teacher_rating = float(snapshot.teacher_rating) if snapshot.teacher_rating is not None else 0
        fee_status = str(snapshot.fee_status).strip() if snapshot.fee_status else ''
        
        if attendance < 75:
            base_action += ' | Implement attendance improvement plan'
        if 'Overdue' in fee_status:
            base_action += ' | Contact parents regarding fee payment'
        if teacher_rating < 2:
            base_action += ' | Behavioral intervention needed'
    
    return base_action

def analyze_student_needs(student_data):
    """Analyze comprehensive student needs"""
    analysis = {}
    
    risk_level = str(student_data.get('risk_level', 'unknown')).lower()
    risk_score = student_data.get('risk_score', 0)
    
    if risk_score >= 70 or risk_level == 'high':
        analysis['risk_status'] = 'HIGH_RISK'
        analysis['urgency'] = ' CRITICAL'
        analysis['risk_description'] = f"Critical concern - Risk score {risk_score}/100"
    elif risk_score >= 40 or risk_level == 'medium':
        analysis['risk_status'] = 'MEDIUM_RISK'
        analysis['urgency'] = ' MODERATE'
        analysis['risk_description'] = f"Moderate concern - Risk score {risk_score}/100"
    else:
        analysis['risk_status'] = 'LOW_RISK'
        analysis['urgency'] = ' LOW'
        analysis['risk_description'] = f"Low concern - Risk score {risk_score}/100"
    
    attendance = student_data.get('attendance_rate', 0)
    if attendance < 75:
        analysis['needs_attendance_support'] = True
        analysis['attendance_issue'] = f"🔴 Poor attendance ({attendance}%) - Below safe level"
    elif attendance < 85:
        analysis['needs_attendance_support'] = True
        analysis['attendance_issue'] = f"🟡 Low attendance ({attendance}%) - Needs monitoring"
    else:
        analysis['needs_attendance_support'] = False
        analysis['attendance_issue'] = f"🟢 Good attendance ({attendance}%)"
    
    teacher_rating = student_data.get('teacher_rating', 0)
    if teacher_rating < 2:
        analysis['teacher_concern'] = f"🔴 Low teacher rating ({teacher_rating}/5) - Behavioral issues likely"
    elif teacher_rating < 3:
        analysis['teacher_concern'] = f"🟡 Below average rating ({teacher_rating}/5) - Performance concerns"
    else:
        analysis['teacher_concern'] = f"🟢 Good teacher rating ({teacher_rating}/5) - Positive relationships"
    
    key_signals = student_data.get('key_signals', [])
    analysis['has_warning_signals'] = len(key_signals) > 0
    analysis['warning_signals'] = key_signals
    
    help_types = []
    if analysis.get('needs_attendance_support'):
        help_types.append(" ATTENDANCE_INTERVENTION")
    if risk_score >= 70:
        help_types.append(" MENTAL_HEALTH_SUPPORT")
    if analysis.get('has_warning_signals'):
        help_types.append(" COUNSELING_SUPPORT")
    if teacher_rating < 3:
        help_types.append(" ACADEMIC_SUPPORT")
    if not help_types:
        help_types.append(" MONITORING")
    
    analysis['help_types'] = help_types
    
    return analysis