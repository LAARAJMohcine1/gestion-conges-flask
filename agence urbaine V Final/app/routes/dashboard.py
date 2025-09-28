from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.department import Department
from app.models.leave import Leave
from sqlalchemy import desc, func
from datetime import datetime, timedelta, date
import json

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    try:
        # Statistiques de base avec gestion des erreurs
        today = date.today()
        stats = {
            'total_employees': Employee.query.count() or 0,  # Retourne 0 si None
            'total_departments': Department.query.count() or 0,
            'active_leaves': Leave.query.filter(
                Leave.start_date <= today,
                Leave.end_date >= today,
                Leave.status == 'approved'
            ).count() or 0,
            'pending_leaves': Leave.query.filter_by(status='pending').count() or 0,
            'attendance_rate': 95  # Valeur par défaut
        }
        
        # Données pour le graphique
        last_12_months = []
        values = []
        current_date = datetime.now()
        
        for i in range(12):
            date_point = current_date - timedelta(days=30*i)
            last_12_months.append(date_point.strftime('%B %Y'))
            comparison_date = date_point.date()
            try:
                count = Employee.query.filter(
                    Employee.hire_date <= comparison_date
                ).count() or 0
            except Exception:
                count = 0
            values.append(int(count))
        
        last_12_months.reverse()
        values.reverse()
        
        chart_data = {
            'labels': json.dumps(last_12_months),
            'values': json.dumps(values)
        }
        
        # Derniers employés ajoutés
        try:
            recent_employees = Employee.query.order_by(desc(Employee.hire_date)).limit(5).all()
        except Exception:
            recent_employees = []
        
        # Personnes actuellement en congé
        today = date.today()
        try:
            current_leaves = Leave.query.filter(
                Leave.start_date <= today,
                Leave.end_date >= today,
                Leave.status == 'approved'
            ).order_by(Leave.start_date).all()
        except Exception:
            current_leaves = []
        
        # Prochains congés
        try:
            upcoming_leaves = Leave.query.filter(
                Leave.start_date > today,
                Leave.status == 'approved'
            ).order_by(Leave.start_date).limit(5).all()
        except Exception:
            upcoming_leaves = []
        
        return render_template('dashboard/index.html', 
                             title='Tableau de bord',
                             stats=stats,
                             chart_data=chart_data,
                             recent_employees=recent_employees,
                             current_leaves=current_leaves,
                             upcoming_leaves=upcoming_leaves)
                             
    except Exception as e:
        # En cas d'erreur, retourner des valeurs par défaut
        default_stats = {
            'total_employees': 0,
            'total_departments': 0,
            'pending_leaves': 0,
            'attendance_rate': 0
        }
        default_chart_data = {
            'labels': json.dumps([]),
            'values': json.dumps([])
        }
        
        return render_template('dashboard/index.html',
                             title='Tableau de bord',
                             stats=default_stats,
                             chart_data=default_chart_data,
                             recent_employees=[],
                             current_leaves=[],
                             upcoming_leaves=[],
                             error_message="Une erreur est survenue lors du chargement des données.")