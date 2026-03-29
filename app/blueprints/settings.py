from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from functools import wraps
import os

settings_bp = Blueprint('settings', __name__)

# Helper: login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = User.query.get(session['user_id'])
    storage_used = get_storage_usage()
    if request.method == 'POST':
        # Profile update
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        if name:
            user.name = name
        if email and email != user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already in use.', 'danger')
            else:
                user.email = email
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('settings.settings'))
    return render_template('settings.html', user=user, storage_used=storage_used)

@settings_bp.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session.get('user_id'))
    if user is None:
        session.clear()
        flash('Session expired or user not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    if not check_password_hash(user.password_hash, old_password):
        flash('Old password is incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    elif len(new_password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
    else:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    return redirect(url_for('settings.settings'))

def get_storage_usage():
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    total = 0
    for root, dirs, files in os.walk(uploads_dir):
        for f in files:
            fp = os.path.join(root, f)
            total += os.path.getsize(fp)
    # Return in MB
    return round(total / (1024 * 1024), 2)
