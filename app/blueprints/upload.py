from flask import Blueprint, render_template, request, jsonify, session, send_file
from app.decorators import login_required
from app.models import db, Student, StudentDataSnapshot, UploadHistory, RiskScore
from app.analytics import calculate_risk_score
from werkzeug.utils import secure_filename
import pandas as pd
import json
from datetime import datetime
import os
import io

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
    """Handle CSV upload with proper error handling and detailed reporting"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files allowed', 'success': False}), 400
        
        # Read CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}', 'success': False}), 400
        
        if df.empty:
            return jsonify({'error': 'CSV file is empty', 'success': False}), 400
        
        # Validate required columns
        required_cols = ['id', 'name']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing)}',
                'success': False
            }), 400
        
        # Debug: Print column names
        print(f"CSV Columns: {list(df.columns)}")
        print(f"First row:\n{df.iloc[0]}")
        
        # Track statistics
        new_count = 0
        updated_count = 0
        error_count = 0
        error_list = []
        total_records = len(df)
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # ===== STEP 1: Validate student ID =====
                try:
                    student_id = int(row['id'])
                    if student_id <= 0:
                        raise ValueError("Student ID must be positive")
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid student ID: {str(e)}")
                
                # ===== STEP 2: Get or create student =====
                student = Student.query.get(student_id)
                
                if not student:
                    # CREATE new student
                    student = Student(
                        id=student_id,
                        name=str(row.get('name', 'Unknown')).strip(),
                        address=str(row.get('address', '')).strip() if pd.notna(row.get('address')) else '',
                        email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
                        grade=int(row.get('grade', 9)) if pd.notna(row.get('grade')) else 9,
                        travel_time=float(row.get('tt', 0)) if pd.notna(row.get('tt')) else 0,
                        father_occupation=str(row.get('fo', '')).strip() if pd.notna(row.get('fo')) else '',
                        mother_occupation=str(row.get('mo', '')).strip() if pd.notna(row.get('mo')) else '',
                        father_education=str(row.get('fq', '')).strip() if pd.notna(row.get('fq')) else '',
                        mother_education=str(row.get('mq', '')).strip() if pd.notna(row.get('mq')) else ''
                    )
                    db.session.add(student)
                    db.session.flush()
                    new_count += 1
                
                else:
                    # UPDATE existing student
                    if pd.notna(row.get('name')):
                        student.name = str(row['name']).strip()
                    if pd.notna(row.get('address')):
                        student.address = str(row['address']).strip()
                    if pd.notna(row.get('email')):
                        student.email = str(row['email']).strip()
                    if pd.notna(row.get('grade')):
                        try:
                            student.grade = int(row['grade'])
                        except (ValueError, TypeError):
                            pass
                    if pd.notna(row.get('tt')):
                        try:
                            student.travel_time = float(row['tt'])
                        except (ValueError, TypeError):
                            pass
                    
                    updated_count += 1
                
                db.session.flush()
                
                # ===== STEP 3: Create snapshot =====
                # Handle different column names for attendance
                attendance_col = None
                if 'attendance' in df.columns:
                    attendance_col = 'attendance'
                elif 'attendance%' in df.columns:
                    attendance_col = 'attendance%'
                elif 'attendance %' in df.columns:
                    attendance_col = 'attendance %'
                
                attendance_value = 0
                if attendance_col and pd.notna(row.get(attendance_col)):
                    try:
                        attendance_value = float(row[attendance_col])
                    except (ValueError, TypeError):
                        attendance_value = 0
                
                snapshot = StudentDataSnapshot(
                    student_id=student.id,
                    ias=float(row.get('ias', 0)) if pd.notna(row.get('ias')) else 0,
                    twp=float(row.get('twp', 0)) if pd.notna(row.get('twp')) else 0,
                    tnp=float(row.get('tnp', 0)) if pd.notna(row.get('tnp')) else 0,
                    arr=str(row.get('arr', 'N')).upper() if pd.notna(row.get('arr')) else 'N',
                    attendance=attendance_value,
                    fee_status=str(row.get('fee_late', 'Unknown')).strip() if pd.notna(row.get('fee_late')) else 'Unknown',
                    teacher_rating=float(row.get('teacher_rating', 0)) if pd.notna(row.get('teacher_rating')) else 0,
                    teacher_notes=str(row.get('teacher_notes', '')).strip() if pd.notna(row.get('teacher_notes')) else '',
                    num_friends=int(row.get('nf', 0)) if pd.notna(row.get('nf')) else 0,
                    counseling_visits=int(row.get('previous_visits', 0)) if pd.notna(row.get('previous_visits')) else 0,
                    mental_health_summary=str(row.get('summary_self_check_in', '')).strip() if pd.notna(row.get('summary_self_check_in')) else '',
                    raw_data=row.to_json()
                )
                db.session.add(snapshot)
                db.session.flush()
                
                # ===== STEP 4: Calculate risk score =====
                try:
                    risk_data = calculate_risk_score(snapshot)
                    
                    risk_score = RiskScore(
                        student_id=student.id,
                        risk_score=risk_data['risk_score'],
                        risk_level=risk_data['risk_level'],
                        signals=json.dumps(risk_data.get('signals', [])),
                        pattern=risk_data.get('pattern', ''),
                        notes=risk_data.get('notes', ''),
                        scored_at=datetime.now()
                    )
                    db.session.add(risk_score)
                except Exception as risk_error:
                    print(f"Risk calculation error for row {idx + 1}: {risk_error}")
                    # Continue without risk score if calculation fails
                    pass
                
                db.session.commit()
            
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                error_list.append(f"Row {idx + 1}: {error_msg}")
                db.session.rollback()
                print(f"Error processing row {idx + 1}: {error_msg}")
        
        # Log upload
        try:
            upload_record = UploadHistory(
                uploaded_by=session.get('user_email', 'Unknown'),
                file_name=secure_filename(file.filename),
                record_count=total_records,
                success_count=new_count + updated_count,
                error_count=error_count,
                new_students=new_count,
                updated_students=updated_count,
                errors=json.dumps(error_list[:10]) if error_list else None,
                uploaded_at=datetime.now()
            )
            db.session.add(upload_record)
            db.session.commit()
        except Exception as e:
            print(f"Error logging upload: {e}")
        
        # Return success/error response
        if error_count > 0:
            return jsonify({
                'success': error_count < total_records,  # Success if some processed
                'message': f'Processed {new_count + updated_count}/{total_records} records with {error_count} errors',
                'new_students': new_count,
                'updated_students': updated_count,
                'errors': error_count,
                'error_details': error_list[:10]  # Show first 10 errors
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Successfully processed {new_count + updated_count}/{total_records} records',
                'new_students': new_count,
                'updated_students': updated_count,
                'errors': 0,
                'error_details': []
            })
    
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@upload_bp.route('/api/delete-student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """Delete a single student and all their data"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found', 'success': False}), 404
        
        student_name = student.name
        
        # Delete cascades should handle this, but be explicit
        StudentDataSnapshot.query.filter_by(student_id=student_id).delete()
        RiskScore.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {student_name}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Delete error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@upload_bp.route('/api/delete-all', methods=['DELETE'])
@login_required
def delete_all_data():
    """Delete ALL student data"""
    try:
        # Get count before deletion
        count = Student.query.count()
        
        # Delete in order
        StudentDataSnapshot.query.delete()
        RiskScore.query.delete()
        Student.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {count} students and all related data'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Delete all error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@upload_bp.route('/api/delete-all-data', methods=['DELETE'])
@login_required
def delete_all_data_extended():
    """Delete ALL data including upload history"""
    try:
        # Get counts
        student_count = Student.query.count()
        upload_count = UploadHistory.query.count()
        
        # Delete everything
        UploadHistory.query.delete()
        StudentDataSnapshot.query.delete()
        RiskScore.query.delete()
        Student.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {student_count} students, {upload_count} uploads, and all related data'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Delete all error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


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
    
    # Create template
    template_data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Aayush Sharma', 'Priya Singh', 'Rohan Patel', 'Meera Verma', 'Arjun Kumar'],
        'address': ['Kathmandu', 'Pokhara', 'Lalitpur', 'Bhaktapur', 'Kathmandu'],
        'email': ['aayush@school.edu', 'priya@school.edu', 'rohan@school.edu', 'meera@school.edu', 'arjun@school.edu'],
        'grade': [10, 11, 9, 12, 10],
        'tt': [1.5, 2.0, 1.2, 0.8, 1.0],
        'fo': ['Business', 'Government', 'Private', 'Self-employed', 'Business'],
        'mo': ['Homemaker', 'Teacher', 'Nurse', 'Business', 'Private'],
        'fq': ['12', 'Degree', 'PG', '12', 'Degree'],
        'mq': ['10', '12', 'Degree', '12', '12'],
        'ias': [75, 85, 65, 88, 72],
        'twp': [78, 82, 70, 90, 75],
        'tnp': [75, 80, 68, 88, 73],
        'arr': ['N', 'N', 'Y', 'N', 'N'],
        'attendance': [85, 90, 75, 92, 80],
        'fee_late': ['Paid', 'Paid', 'Overdue', 'Paid', 'Paid'],
        'teacher_rating': [4.0, 4.5, 2.5, 4.8, 3.5],
        'nf': [5, 8, 2, 7, 4],
        'previous_visits': [0, 1, 3, 0, 1],
        'summary_self_check_in': ['Feeling good', 'Happy and confident', 'Stressed', 'Excellent', 'Good'],
        'teacher_notes': ['Good student', 'Top performer', 'Needs support', 'Excellent progress', 'Average student']
    }
    
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='EduPulse_Student_Template.csv'
    )