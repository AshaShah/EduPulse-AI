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

def search_students_by_name(name, db_session):
    """Search for students by name and return matches"""
    if not db_session or not name:
        return []
    
    try:
        from app.models import Student, RiskScore, StudentDataSnapshot
        
        name_clean = name.strip()
        
        # Try exact match first
        students = db_session.query(Student).filter(
            Student.name.ilike(name_clean)
        ).all()
        
        # Try partial match
        if not students:
            students = db_session.query(Student).filter(
                Student.name.ilike(f"%{name_clean}%")
            ).all()
        
        results = []
        for student in students[:5]:  # Limit to 5 results
            latest_score = db_session.query(RiskScore).filter_by(
                student_id=student.id
            ).order_by(RiskScore.scored_at.desc()).first()
            
            latest_snapshot = db_session.query(StudentDataSnapshot).filter_by(
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
    except Exception as e:
        print(f"Error searching students: {e}")
        return []

def extract_name_from_message(message: str):
    """Extract student name from natural language message"""
    message = message.strip().lower()
    
    # Remove common phrases
    phrases_to_remove = [
        "tell me about", "tell about", "how can i help", "how can i support",
        "how to help", "what about", "show me", "info about", "information about",
        "details about", "who is", "who's", "get me", "get info on",
        "can you tell me about", "can you show me", "i want to know about",
        "please tell me about", "help with", "help me", "details", "about", "info",
        "student", "students", "named", "called", "name"
    ]
    
    processed = message
    for phrase in sorted(phrases_to_remove, key=len, reverse=True):
        if processed.startswith(phrase):
            processed = processed[len(phrase):].strip()
            break
    
    # Extract quoted names
    quoted = re.findall(r'"([^"]+)"', processed)
    if quoted:
        return quoted[0]
    
    # Extract name-like words (capitalized or known names)
    words = processed.split()
    name_words = []
    stop_words = {'and', 'or', 'the', 'a', 'to', 'for', 'with', 'by', 'is', 'has', 'have'}
    
    for word in words:
        clean_word = word.rstrip('.,!?;:').strip()
        if not clean_word or clean_word.lower() in stop_words:
            if name_words:
                break
            continue
        name_words.append(clean_word)
    
    return ' '.join(name_words) if name_words else None

def get_chatbot_response(user_message: str, db_session=None):
    """Main chatbot response function with student search"""
    
    # Search for student names
    student_name = extract_name_from_message(user_message)
    matching_students = []
    
    if student_name and db_session:
        matching_students = search_students_by_name(student_name, db_session)
    
    # If multiple students found, ask for clarification
    if len(matching_students) > 1:
        response = f"🔍 **Found {len(matching_students)} students matching '{student_name}':**\n\n"
        for i, student in enumerate(matching_students, 1):
            response += f"{i}. **{student['name']}** (Grade {student['grade']}) - {student['risk_level']} Risk\n"
        response += f"\nPlease specify which student by ID or ask again with more details."
        return response
    
    # If exactly one student found, generate detailed response
    elif len(matching_students) == 1:
        student = matching_students[0]
        return generate_student_response_detailed(user_message, student, db_session)
    
    # No student found, provide general guidance
    else:
        return generate_general_response(user_message)

def generate_student_response_detailed(user_message: str, student: dict, db_session) -> str:
    """Generate detailed response for a specific student"""
    try:
        from app.models import Student, RiskScore, StudentDataSnapshot
        
        # Get full student data
        student_obj = Student.query.get(student['id'])
        latest_snapshot = StudentDataSnapshot.query.filter_by(
            student_id=student['id']
        ).order_by(StudentDataSnapshot.created_at.desc()).first()
        
        if not student_obj or not latest_snapshot:
            return f"📚 **{student['name']}** (Grade {student['grade']})\n⏳ Insufficient data available."
        
        # Create analysis data
        student_data = {
            'name': student['name'],
            'grade': student['grade'],
            'risk_level': student['risk_level'],
            'risk_score': student['risk_score'],
            'attendance_rate': student['attendance'],
            'teacher_rating': student['teacher_rating'],
            'num_friends': latest_snapshot.num_friends,
            'ias': latest_snapshot.ias,
            'fee_status': latest_snapshot.fee_status,
        }
        
        analysis = analyze_student_needs(student_data)
        
        # Build response
        response = f"📚 **{student['name']}** (Grade {student['grade']})\n"
        response += f"{'='*50}\n\n"
        
        response += f"**Risk Status**: {analysis['urgency']}\n"
        response += f"**Risk Score**: {student['risk_score']}/100\n"
        response += f"**Attendance**: {student['attendance']}%\n"
        response += f"**Teacher Rating**: {student['teacher_rating']}/5.0\n"
        response += f"**Close Friends**: {student_data['num_friends']}\n"
        response += f"**IAS Score**: {student_data['ias']}/100\n\n"
        
        response += f"**Analysis**:\n"
        response += f"{analysis['risk_description']}\n"
        response += f"{analysis['attendance_issue']}\n"
        response += f"{analysis['teacher_concern']}\n\n"
        
        if analysis['has_warning_signals']:
            response += "**⚠️ Warning Signals**:\n"
            for signal in analysis['warning_signals'][:5]:
                response += f"  • {signal}\n"
            response += "\n"
        
        response += "**💡 Recommended Actions**:\n"
        for help_type in analysis['help_types']:
            response += f"  • {help_type}\n"
        
        return response
    
    except Exception as e:
        return f"❌ Error analyzing student: {str(e)}"

def generate_general_response(user_message: str) -> str:
    """Generate response for general educational questions"""
    try:
        if not COHERE_AVAILABLE or not client:
            return "👋 **EduPulse AI Assistant**\n\nI can help with:\n" \
                   "✅ Student performance analysis\n" \
                   "📊 Risk assessment guidance\n" \
                   "💬 Mental health support strategies\n" \
                   "📚 Academic improvement tips\n" \
                   "🎯 Intervention recommendations\n\n" \
                   "**Try asking:**\n" \
                   "- 'Tell me about [student name]'\n" \
                   "- 'How do I detect depression in students?'\n" \
                   "- 'Best practices for counseling?'"
        
        prompt = f"""You are EduPulse AI, an expert school counselor assistant.
Provide practical, actionable advice for educators.

Question: {user_message}

Keep response concise (3-4 sentences max) and educational."""
        
        response = client.chat(
            message=prompt,
            max_tokens=400,
            temperature=0.7,
        )
        return response.text
    
    except Exception as e:
        return "👋 **EduPulse AI Assistant**\n\nHow can I help you today?\n\n" \
               "Try asking about specific students or get general counseling guidance."