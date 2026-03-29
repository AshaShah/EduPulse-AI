from flask import Blueprint, render_template, request, jsonify, session
from app.decorators import login_required
from app.models import db, Student, StudentDataSnapshot, UploadHistory, RiskScore
from app.analytics import calculate_risk_score
from werkzeug.utils import secure_filename
import pandas as pd
import json
from datetime import datetime
import os

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')

@upload_bp.route('/upload')
@login_required
def upload_page():
    """Upload data page"""
    upload_history = UploadHistory.query.order_by(
        UploadHistory.uploaded_at.desc()
    ).limit(20).all()
    
    return render_template('upload.html', history=upload_history)

@upload_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_csv():
    """Handle CSV upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    try:
        df = pd.read_csv(file)
        
        # Validate columns
        required_cols = ['id', 'name']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return jsonify({'error': f'Missing required columns: {", ".join(missing)}'}), 400
        
        processed_count = 0
        error_list = []
        
        for idx, row in df.iterrows():
            try:
                student_id = int(row['id'])
                
                # Create or update student
                student = Student.query.get(student_id)
                if not student:
                    student = Student(
                        id=student_id,
                        name=row.get('name', ''),
                        address=row.get('address', ''),
                        email=row.get('email', ''),
                        grade=int(row.get('grade', 9)),
                        travel_time=float(row.get('tt', 0)),
                        father_occupation=row.get('fo', ''),
                        mother_occupation=row.get('mo', ''),
                        father_education=row.get('fq', ''),
                        mother_education=row.get('mq', '')
                    )
                    db.session.add(student)
                else:
                    if pd.notna(row.get('name')):
                        student.name = row['name']
                    if pd.notna(row.get('address')):
                        student.address = row['address']
                    if pd.notna(row.get('email')):
                        student.email = row['email']
                
                db.session.commit()
                
                # Create snapshot
                snapshot = StudentDataSnapshot(
                    student_id=student.id,
                    ias=float(row.get('ias', 0)),
                    twp=float(row.get('twp', 0)),
                    tnp=float(row.get('tnp', 0)),
                    arr=row.get('arr', 'N'),
                    attendance=float(row.get('attendance', 0)),
                    fee_status=row.get('fee_late', 'Paid'),
                    teacher_rating=float(row.get('teacher_rating', 3)),
                    teacher_notes=row.get('teacher_notes', ''),
                    num_friends=int(row.get('nf', 0)),
                    counseling_visits=int(row.get('previous_visits', 0)),
                    mental_health_summary=row.get('summary_self_check_in', ''),
                    attendance_json=json.dumps([float(row.get('attendance', 0))]),
                    raw_data=row.to_json()
                )
                db.session.add(snapshot)
                db.session.commit()
                
                # Calculate and store risk score
                risk_score = calculate_risk_score(student_id)
                db.session.add(risk_score)
                db.session.commit()
                
                processed_count += 1
            
            except Exception as e:
                error_list.append(f"Row {idx + 1}: {str(e)}")
        
        # Log upload
        upload_record = UploadHistory(
            uploaded_by=session.get('user_email'),
            file_name=secure_filename(file.filename),
            record_count=len(df),
            success_count=processed_count,
            error_count=len(error_list),
            errors=json.dumps(error_list) if error_list else None,
            uploaded_at=datetime.now()
        )
        db.session.add(upload_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed_count}/{len(df)} records',
            'processed': processed_count,
            'failed': len(error_list),
            'errors': error_list[:5]  # Show first 5 errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/delete-student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """Delete a student and all their data"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Delete related data (cascades automatically)
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Deleted {student.name}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/api/delete-all', methods=['DELETE'])
@login_required
def delete_all_data():
    """Delete ALL student data (careful!)"""
    try:
        # Get count before deletion
        count = Student.query.count()
        
        # Delete all
        Student.query.delete()
        RiskScore.query.delete()
        StudentDataSnapshot.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Deleted {count} students and all related data'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/data-management')
@login_required
def data_management():
    """Data management and deletion page"""
    students = Student.query.all()
    upload_history = UploadHistory.query.order_by(
        UploadHistory.uploaded_at.desc()
    ).all()
    
    return render_template('data_management.html', 
                         students=students,
                         history=upload_history)


@upload_bp.route('/api/download-template')
@login_required
def download_template():
    """Download CSV template"""
    import io
    from flask import send_file
    
    # Create template
    template_data = {
        'id': [1, 2, 3],
        'name': ['Sample Student 1', 'Sample Student 2', 'Sample Student 3'],
        'address': ['Kathmandu', 'Pokhara', 'Lalitpur'],
        'email': ['student1@email.com', 'student2@email.com', 'student3@email.com'],
        'grade': [10, 11, 12],
        'tt': [1.5, 2.0, 1.2],
        'fo': ['Business', 'Government', 'Private'],
        'mo': ['Homemaker', 'Teacher', 'Nurse'],
        'fq': ['12', 'Degree', 'PG'],
        'mq': ['10', '12', 'Degree'],
        'ias': [75, 85, 65],
        'twp': [78, 82, 70],
        'tnp': [75, 80, 68],
        'arr': ['N', 'N', 'Y'],
        'attendance': [85, 90, 75],
        'fee_late': ['Paid', 'Paid', 'Overdue'],
        'teacher_rating': [4, 4.5, 2.5],
        'nf': [5, 8, 2],
        'previous_visits': [0, 1, 3],
        'summary_self_check_in': ['Feeling good', 'Happy and confident', 'Stressed']
    }
    
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='student_data_template.csv'
    )