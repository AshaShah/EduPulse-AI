import os
from dotenv import load_dotenv
import json
import re
from app.analytics import analyze_student_needs

load_dotenv()

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

client = None
if COHERE_AVAILABLE:
    try:
        api_key = os.getenv("COHERE_API_KEY")
        if api_key:
            client = cohere.Client(api_key=api_key)
            print("✓ Cohere client initialized")
    except Exception as e:
        print(f"⚠ Cohere initialization warning: {e}")


def is_general_question(text: str) -> bool:
    """Check if text is a general question (not a student search)"""
    text_lower = text.lower().strip()
    
    # General education/counseling questions
    general_patterns = [
        'how to', 'how can i', 'how do i',
        'what is', 'what are', 'explain',
        'tell me about', 'best practices', 'tips for',
        'strategies for', 'ways to', 'methods for',
        'help with', 'support for', 'signs of',
        'depression', 'anxiety', 'stress', 'mental health',
        'attendance', 'intervention', 'counseling',
        'behavior', 'engagement', 'academic',
        'why', 'when', 'where', 'which'
    ]
    
    # If text contains these patterns AND it's longer than 2 words, it's a general question
    # Short texts like "aayush" should be treated as names
    if len(text_lower.split()) > 2:
        for pattern in general_patterns:
            if pattern in text_lower:
                return True
    
    return False


def is_pure_number(text: str) -> bool:
    """Check if text is just a number (student ID)"""
    text = text.strip()
    if re.match(r'^\d+$', text):
        return True
    if re.match(r'^id\s*\d+$', text, re.IGNORECASE):
        return True
    return False


def extract_student_id(text: str):
    """Extract student ID from text"""
    text = text.strip()
    
    # Priority 1: Just a number
    match = re.match(r'^(\d+)$', text)
    if match:
        return int(match.group(1))
    
    # Priority 2: ID patterns
    id_patterns = [
        r'(?:ID|id|student id|student_id)[:\s]*(\d+)',
        r'#(\d+)',
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    return None


def extract_student_name(text: str):
    """
    Extract student name from text (only if not a general question)
    Prioritizes name extraction for short inputs
    """
    if is_pure_number(text):
        return None
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # For short inputs (1-3 words), assume it's a name unless it contains general patterns
    words = text_clean.split()
    if len(words) <= 3:
        # Check if it contains strong general question indicators
        general_indicators = ['how', 'what', 'tell', 'when', 'where', 'why', 'which']
        if not any(indicator in text_lower for indicator in general_indicators):
            # Likely a name
            return text_clean
    
    # Remove common question phrases
    phrases_to_remove = [
        "tell me about", "tell about", "who is", "info about", "information about",
        "details about", "about", "student", "show me", "can you tell me",
        "i want to know", "please tell me", "what about", "student named",
        "student called", "help with", "details on", "info on", "get me"
    ]
    
    processed = text_lower
    for phrase in sorted(phrases_to_remove, key=len, reverse=True):
        if phrase in processed:
            processed = processed.replace(phrase, "").strip()
    
    if not processed or len(processed) < 2:
        return None
    
    # Extract quoted names
    quoted = re.findall(r'"([^"]+)"', processed)
    if quoted:
        return quoted[0].strip()
    
    # For remaining text, use original capitalization
    # Extract capitalized words as potential names
    name_words = []
    stop_words = {'and', 'or', 'the', 'a', 'to', 'for', 'with', 'is', 'are', 'by', 'about', 'me', 'you', 'how', 'can', 'i', 'in', 'on', 'of', 'at'}
    
    for word in text_clean.split():
        clean_word = word.rstrip('.,!?;:').strip()
        
        if clean_word and clean_word[0].isupper() and clean_word.lower() not in stop_words:
            name_words.append(clean_word)
        elif name_words:
            break
    
    return ' '.join(name_words) if name_words else processed.title()


def validate_student_data(student: dict) -> dict:
    """Validate and clean student data"""
    
    attendance = student.get('attendance', 0)
    if attendance is None or attendance > 100:
        attendance = 0
    elif attendance < 0:
        attendance = 0
    
    risk_score = student.get('risk_score', 0)
    if risk_score is None or risk_score > 100:
        risk_score = 100
    elif risk_score < 0:
        risk_score = 0
    
    teacher_rating = student.get('teacher_rating', 0)
    if teacher_rating is None or teacher_rating > 5:
        teacher_rating = 0
    elif teacher_rating < 0:
        teacher_rating = 0
    
    student['attendance'] = attendance
    student['risk_score'] = risk_score
    student['teacher_rating'] = teacher_rating
    
    return student


def search_students(db_session, student_id=None, student_name=None):
    """Search for students by ID or name (case-insensitive)"""
    if not db_session:
        return []
    
    try:
        from app.models import Student, RiskScore, StudentDataSnapshot
        
        # Priority 1: Search by ID
        if student_id:
            student = Student.query.get(student_id)
            if student:
                latest_score = RiskScore.query.filter_by(
                    student_id=student.id
                ).order_by(RiskScore.scored_at.desc()).first()
                
                latest_snapshot = StudentDataSnapshot.query.filter_by(
                    student_id=student.id
                ).order_by(StudentDataSnapshot.created_at.desc()).first()
                
                return [{
                    "id": student.id,
                    "name": student.name,
                    "grade": student.grade,
                    "email": student.email,
                    "risk_level": latest_score.risk_level if latest_score else "UNKNOWN",
                    "risk_score": latest_score.risk_score if latest_score else 0,
                    "attendance": latest_snapshot.attendance if latest_snapshot else 0,
                    "teacher_rating": latest_snapshot.teacher_rating if latest_snapshot else 0,
                }]
        
        # Priority 2: Search by name (case-insensitive)
        if student_name:
            name_clean = student_name.strip()
            
            # Try exact match first (case-insensitive)
            students = Student.query.filter(
                Student.name.ilike(name_clean)
            ).all()
            
            # Try partial match (case-insensitive)
            if not students:
                students = Student.query.filter(
                    Student.name.ilike(f"%{name_clean}%")
                ).all()
            
            results = []
            for student in students[:10]:
                latest_score = RiskScore.query.filter_by(
                    student_id=student.id
                ).order_by(RiskScore.scored_at.desc()).first()
                
                latest_snapshot = StudentDataSnapshot.query.filter_by(
                    student_id=student.id
                ).order_by(StudentDataSnapshot.created_at.desc()).first()
                
                results.append({
                    "id": student.id,
                    "name": student.name,
                    "grade": student.grade,
                    "email": student.email,
                    "risk_level": latest_score.risk_level if latest_score else "UNKNOWN",
                    "risk_score": latest_score.risk_score if latest_score else 0,
                    "attendance": latest_snapshot.attendance if latest_snapshot else 0,
                    "teacher_rating": latest_snapshot.teacher_rating if latest_snapshot else 0,
                })
            
            return results
        
        return []
    
    except Exception as e:
        print(f"Error searching students: {e}")
        return []


def format_student_info(student: dict) -> str:
    """Format student information in a clean way"""
    risk_icon = "🔴" if student['risk_level'] == 'HIGH' else "🟡" if student['risk_level'] == 'MEDIUM' else "🟢"
    
    info = f"""
{student['name']} (Grade {student['grade']}) - ID: {student['id']}
{'─' * 60}
Status: {risk_icon} {student['risk_level']} RISK ({student['risk_score']}/100)
Attendance: {student['attendance']}%
Teacher Rating: {student['teacher_rating']}/5.0
Email: {student['email'] or 'N/A'}
"""
    return info.strip()


def show_student_selector(students: list) -> str:
    """Show list of students for selection"""
    response = f"Found {len(students)} student(s). Which one are you asking about?\n\n"
    
    for student in students:
        risk_icon = "🔴" if student['risk_level'] == 'HIGH' else "🟡" if student['risk_level'] == 'MEDIUM' else "🟢"
        response += f"ID {student['id']}: {student['name']} (Grade {student['grade']}) {risk_icon} {student['risk_level']}\n"
    
    response += "\nYou can reply with:\n"
    response += "- Just the ID number (e.g., '1013' or '1054')\n"
    response += "- Full name (e.g., 'Aayush Khatiwada')\n"
    response += "- A more specific question\n"
    
    return response


def generate_student_response(user_message: str, student: dict, db_session) -> str:
    """Generate response for a specific student"""
    try:
        from app.models import Student, StudentDataSnapshot
        
        student = validate_student_data(student)
        
        student_obj = Student.query.get(student['id'])
        latest_snapshot = StudentDataSnapshot.query.filter_by(
            student_id=student['id']
        ).order_by(StudentDataSnapshot.created_at.desc()).first()
        
        if not student_obj or not latest_snapshot:
            return f"Student {student['name']} found but insufficient data available."
        
        student_data = {
            'name': student['name'],
            'grade': student['grade'],
            'risk_level': student['risk_level'],
            'risk_score': int(student['risk_score']),
            'attendance_rate': float(student['attendance']),
            'teacher_rating': float(student['teacher_rating']),
            'num_friends': int(latest_snapshot.num_friends) if latest_snapshot.num_friends else 0,
            'ias': float(latest_snapshot.ias) if latest_snapshot.ias else 0,
            'fee_status': latest_snapshot.fee_status or 'Unknown',
            'counseling_visits': int(latest_snapshot.counseling_visits) if latest_snapshot.counseling_visits else 0,
        }
        
        analysis = analyze_student_needs(student_data)
        
        response = f"\n{format_student_info(student)}\n\n"
        
        response += "ANALYSIS\n"
        response += "─" * 60 + "\n"
        response += f"Risk Status: {analysis['urgency']}\n"
        response += f"Attendance: {analysis['attendance_issue']}\n"
        response += f"Behavior: {analysis['teacher_concern']}\n\n"
        
        if analysis['has_warning_signals']:
            response += "WARNING SIGNALS\n"
            response += "─" * 60 + "\n"
            for signal in analysis['warning_signals'][:5]:
                response += f"• {signal}\n"
            response += "\n"
        
        response += "RECOMMENDED SUPPORT\n"
        response += "─" * 60 + "\n"
        for help_type in analysis['help_types']:
            response += f"• {help_type}\n"
        
        if analysis.get('mental_health_recommendations'):
            response += "\nMENTAL HEALTH SUPPORT\n"
            response += "─" * 60 + "\n"
            for rec in analysis['mental_health_recommendations'][:5]:
                response += f"• {rec}\n"
        
        if analysis.get('administrative_actions'):
            response += "\nADMINISTRATIVE ACTIONS\n"
            response += "─" * 60 + "\n"
            for action in analysis['administrative_actions'][:5]:
                response += f"• {action}\n"
        
        return response.strip()
    
    except Exception as e:
        print(f"Error analyzing student: {e}")
        return f"Error analyzing student {student.get('name', 'Unknown')}: {str(e)}"


def generate_general_response(user_message: str) -> str:
    """Generate response for general educational questions"""
    if not COHERE_AVAILABLE or not client:
        fallback_responses = {
            'attendance': """
ATTENDANCE INTERVENTION STRATEGIES

Set Clear Expectations:
• Communicate attendance policies to parents
• Track patterns and address early
• Celebrate perfect attendance records

Identify Root Causes:
• Health issues
• Family problems
• Lack of engagement
• Transportation issues

Intervention Actions:
• Contact parents/guardians
• Adjust class schedule if possible
• Provide academic support
• Refer to counselor for underlying issues

Monitoring:
• Weekly check-ins
• Academic performance tracking
• Parent communication logs
""",
            'depression': """
SIGNS OF DEPRESSION IN STUDENTS

Behavioral Signs:
• Withdrawal from friends/activities
• Changes in sleep patterns
• Loss of interest in school
• Increased irritability
• Poor concentration
• Academic decline

Physical Signs:
• Fatigue or low energy
• Changes in appetite
• Neglect of personal hygiene
• Frequent complaints of pain

Recommended Actions:
• Document observed behaviors
• Refer to school counselor
• Communicate with parents
• Provide supportive environment
• Monitor progress regularly
""",
            'anxiety': """
MANAGING STUDENT ANXIETY

Recognition:
• Excessive worry about school
• Physical symptoms (headaches, stomachaches)
• Avoidance behaviors
• Perfectionism
• Difficulty concentrating

Support Strategies:
• Create predictable routines
• Reduce pressure/workload when needed
• Teach relaxation techniques
• Encourage physical activity
• Provide quiet spaces

When to Refer:
• Anxiety interfering with learning
• Physical symptoms
• Social withdrawal
• Persistent over multiple weeks
""",
            'engagement': """
IMPROVING STUDENT ENGAGEMENT

Assess Current Level:
• Classroom participation
• Assignment completion
• Attendance
• Social interaction
• Interest in subjects

Strategies to Boost Engagement:
• Make content relevant to student interests
• Use varied teaching methods
• Provide choice in assignments
• Celebrate small victories
• Build positive relationships
• Create collaborative opportunities
"""
        }
        
        question_lower = user_message.lower()
        for key, response in fallback_responses.items():
            if key in question_lower:
                return response.strip()
        
        return """
EduPulse AI Assistant - How I Can Help

Ask About Students:
• Just type the student ID (e.g., '1013')
• Type a first or last name (e.g., 'Aayush')
• "Tell me about Aayush Khatiwada"

General Guidance:
• "How to improve attendance?"
• "Signs of depression in students?"
• "Best practices for counseling?"
• "Strategies for student engagement?"
• "How to manage anxiety?"

I'm here to help with:
Academic performance analysis
Mental health support strategies
Risk assessment guidance
Intervention recommendations
Student engagement tips
"""
    
    try:
        prompt = f"""You are EduPulse AI, an expert school counselor assistant for educators.
Provide practical, actionable advice for helping students succeed academically and emotionally.

Question from educator: {user_message}

Give concise, helpful advice in 3-4 sentences. Focus on:
- Practical strategies
- Real-world applications
- Student-centered approaches
- Evidence-based practices
"""
        
        response = client.chat(
            message=prompt,
            max_tokens=300,
            temperature=0.7,
        )
        return response.text.strip()
    
    except Exception as e:
        print(f"Cohere API error: {e}")
        return "I'm experiencing technical difficulties. Please try a simpler question or ask about a specific student using their ID or name."


def get_chatbot_response(user_message: str, db_session=None):
    """Main chatbot response function with smart student search"""
    
    # Extract student ID first (highest priority)
    student_id = extract_student_id(user_message)
    
    if student_id:
        results = search_students(db_session, student_id=student_id)
        if results:
            student = results[0]
            return generate_student_response(user_message, student, db_session)
        else:
            return f"No student found with ID {student_id}.\n\nTry:\n- Using correct ID number\n- Student's full name\n- General counseling question"
    
    # Extract student name (second priority)
    student_name = extract_student_name(user_message)
    
    if student_name:
        results = search_students(db_session, student_name=student_name)
        
        if len(results) == 1:
            return generate_student_response(user_message, results[0], db_session)
        
        elif len(results) > 1:
            return show_student_selector(results)
        
        else:
            return f"No student found with name '{student_name}'.\n\nTry:\n- Using student ID number\n- Full name spelling\n- General counseling question"
    
    # Check if it's a general question
    if is_general_question(user_message):
        return generate_general_response(user_message)
    
    # Default: provide general guidance
    return generate_general_response(user_message)