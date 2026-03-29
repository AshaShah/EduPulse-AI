from flask import Blueprint, render_template, session
from app.decorators import login_required
from app.analytics import calculate_dashboard_stats
from app.models import RiskScore

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def analytics():
    """Advanced analytics page"""
    stats = calculate_dashboard_stats()
    
    return render_template('analytics.html', stats=stats)