from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

# Demo credentials
DEMO_CREDENTIALS = {
    'counselor@school.edu': 'password123',
    'admin@school.edu': 'admin123'
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Demo login
        if email in DEMO_CREDENTIALS and DEMO_CREDENTIALS[email] == password:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=email.split('@')[0].title(),
                    role='counselor'
                )
                db.session.add(user)
                db.session.commit()
            
            session.permanent = True
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            return redirect(url_for('dashboard.index'))
        
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))