from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.department import Department
from app.models.employee import Employee
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, ValidationError

bp = Blueprint('department', __name__, url_prefix='/departments')

class DepartmentForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    description = TextAreaField('Description')
    manager_id = SelectField('Manager', coerce=int)

    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.manager_id.choices = [(0, 'Aucun')] + [
            (e.id, f"{e.first_name} {e.last_name}") 
            for e in Employee.query.filter_by(is_manager=True).all()
        ]

@bp.route('/')
@login_required
def index():
    departments = Department.query.all()
    return render_template('departments/list.html',
                         title='Départements',
                         departments=departments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            description=form.description.data
        )
        if form.manager_id.data != 0:
            manager = Employee.query.get(form.manager_id.data)
            department.manager = manager
        
        db.session.add(department)
        db.session.commit()
        flash('Département ajouté avec succès')
        return redirect(url_for('department.index'))
    
    return render_template('departments/add.html',
                         title='Ajouter un département',
                         form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    department = Department.query.get_or_404(id)
    return render_template('departments/view.html',
                         title=f'Département {department.name}',
                         department=department)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.description = form.description.data
        if form.manager_id.data != 0:
            manager = Employee.query.get(form.manager_id.data)
            department.manager = manager
        else:
            department.manager = None
            
        db.session.commit()
        flash('Département modifié avec succès')
        return redirect(url_for('department.view', id=department.id))
    
    if department.manager:
        form.manager_id.data = department.manager.id
    
    return render_template('departments/edit.html',
                         title=f'Modifier {department.name}',
                         form=form,
                         department=department)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    department = Department.query.get_or_404(id)
    
    # Vérifier s'il y a des employés dans ce département
    if department.employees:
        flash(f'Impossible de supprimer le département "{department.name}" car il contient des employés.', 'error')
        return redirect(url_for('department.index'))
    
    # Vérifier si c'est le manager d'autres départements
    if department.manager:
        managed_departments = Department.query.filter_by(manager_id=department.manager.id).all()
        if len(managed_departments) > 1:  # Plus que le département actuel
            flash(f'Impossible de supprimer le département "{department.name}" car son manager gère d\'autres départements.', 'error')
            return redirect(url_for('department.index'))
    
    try:
        db.session.delete(department)
        db.session.commit()
        flash(f'Département "{department.name}" supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du département: {str(e)}', 'error')
    
    return redirect(url_for('department.index')) 