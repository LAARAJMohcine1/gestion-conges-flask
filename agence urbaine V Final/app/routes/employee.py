from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.department import Department
from app.models.department_manager import DepartmentManager
from app.models.user import User
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, EmailField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo
from datetime import datetime
from app.services.pdf_export import PDFExportService

bp = Blueprint('employee', __name__, url_prefix='/employees')

class EmployeeForm(FlaskForm):
    first_name = StringField('Prénom', validators=[DataRequired()])
    last_name = StringField('Nom', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    date_of_birth = DateField('Date de naissance', validators=[DataRequired()])
    gender = SelectField('Genre', choices=[('M', 'Masculin'), ('F', 'Féminin')], validators=[DataRequired()])
    address = StringField('Adresse')
    phone = StringField('Téléphone')
    department_id = SelectField('Département', coerce=int)
    position = StringField('Poste', validators=[DataRequired()])
    annual_leave_days = IntegerField('Jours de congés annuels', default=22, validators=[DataRequired()])
    role = SelectField('Rôle', choices=[('employee', 'Employé'), ('manager', 'Manager'), ('admin', 'Administrateur')], default='employee', validators=[DataRequired()])
    password = PasswordField('Mot de passe')
    confirm_password = PasswordField('Confirmer le mot de passe')

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
    
    def validate_password(self, field):
        # Le mot de passe est requis seulement si c'est un nouvel employé
        if not self.is_edit:
            if not field.data:
                raise ValidationError('Le mot de passe est requis pour un nouvel employé')
        # Si un mot de passe est fourni, vérifier sa longueur
        if field.data and len(field.data) < 6:
            raise ValidationError('Le mot de passe doit contenir au moins 6 caractères')
    
    def validate_confirm_password(self, field):
        # La confirmation est requise seulement si un mot de passe est fourni
        if self.password.data and not field.data:
            raise ValidationError('Veuillez confirmer le mot de passe')

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.paginate(page=page, per_page=10)
    departments = Department.query.all()
    return render_template('employees/list.html', 
                         title='Liste des Employés',
                         employees=employees,
                         departments=departments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = EmployeeForm()
    form.is_edit = False  # Indique que c'est un nouvel employé
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Un utilisateur avec cet email existe déjà', 'error')
            return render_template('employees/add.html', 
                                 title='Ajouter un Employé',
                                 form=form)
        
        # Créer l'utilisateur avec le mot de passe personnalisé
        username = form.email.data.split('@')[0]
        user = User(
            email=form.email.data,
            username=username,
            role=form.role.data  # Utiliser le rôle choisi dans le formulaire
        )
        user.password_hash = form.password.data  # Mot de passe en clair
        db.session.add(user)
        db.session.flush()  # Pour obtenir l'ID de l'utilisateur

        # Créer l'employé
        employee = Employee(
            user_id=user.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            phone=form.phone.data,
            department_id=form.department_id.data,
            position=form.position.data,
            annual_leave_days=form.annual_leave_days.data,
            hire_date=datetime.utcnow().date()
        )
        db.session.add(employee)
        db.session.commit()
        
        # flash(f'Employé {form.first_name.data} {form.last_name.data} ajouté avec succès ! Identifiants de connexion : Email: {form.email.data}, Mot de passe: {form.password.data}', 'success')  # Masqué pour environnement professionnel
        return redirect(url_for('employee.index'))
    
    return render_template('employees/add.html', 
                         title='Ajouter un Employé',
                         form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/view.html',
                         title=f'Profil de {employee.first_name} {employee.last_name}',
                         employee=employee) 

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee, is_edit=True)  # Indique que c'est une édition
    
    # Initialiser le rôle avec la valeur actuelle de l'utilisateur
    if request.method == 'GET':
        form.role.data = employee.user.role
    
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà (sauf pour cet employé)
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != employee.user.id:
            flash('Un utilisateur avec cet email existe déjà', 'error')
            return render_template('employees/edit.html',
                                 title=f'Modifier {employee.first_name} {employee.last_name}',
                                 form=form,
                                 employee=employee)
        
        # Mise à jour des informations de l'employé
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.date_of_birth = form.date_of_birth.data
        employee.gender = form.gender.data
        employee.address = form.address.data
        employee.phone = form.phone.data
        employee.department_id = form.department_id.data
        employee.position = form.position.data
        employee.annual_leave_days = form.annual_leave_days.data
        
        # Mise à jour de l'email et du rôle de l'utilisateur
        employee.user.email = form.email.data
        employee.user.role = form.role.data
        
        # Mise à jour du mot de passe si fourni
        if form.password.data:
            employee.user.password_hash = form.password.data  # Mot de passe en clair
            # flash(f'Employé modifié avec succès. Nouveau mot de passe : {form.password.data}', 'success')  # Masqué pour environnement professionnel
        # else:
        #     flash('Employé modifié avec succès', 'success')  # Masqué pour environnement professionnel
        
        db.session.commit()
        return redirect(url_for('employee.view', id=employee.id))
    
    # Pré-remplir le formulaire avec les données actuelles
    form.email.data = employee.user.email
    
    return render_template('employees/edit.html',
                         title=f'Modifier {employee.first_name} {employee.last_name}',
                         form=form,
                         employee=employee)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    print(f"Tentative de suppression de l'employé ID: {id}")
    employee = Employee.query.get_or_404(id)
    print(f"Employé trouvé: {employee.first_name} {employee.last_name}")
    
    # Empêcher la suppression de l'administrateur principal
    if employee.user.role == 'admin' and employee.user.email == 'admin@agence-urbaine.com':
        print("Tentative de suppression de l'admin principal - bloquée")
        flash('Impossible de supprimer l\'administrateur principal du système.', 'error')
        return redirect(url_for('employee.index'))
    
    # Vérifier s'il y a des congés associés (pour information seulement)
    leaves_count = len(employee.leaves) if employee.leaves else 0
    print(f"Nombre de congés associés: {leaves_count}")
    
    # Vérifier s'il est manager d'un département
    print(f"Est manager: {employee.is_manager}")
    if employee.is_manager:
        managed_departments = DepartmentManager.query.filter_by(employee_id=employee.id).all()
        print(f"Nombre de départements gérés: {len(managed_departments)}")
        if managed_departments:
            # Vérifier si l'utilisateur actuel est admin ou manager (directeur)
            current_user_role = current_user.role
            print(f"Rôle de l'utilisateur actuel: {current_user_role}")
            if current_user_role not in ['admin', 'manager']:
                print("Employé est manager - suppression bloquée pour utilisateur non autorisé")
                flash(f'Impossible de supprimer l\'employé "{employee.first_name} {employee.last_name}" car il est manager d\'un département. Seuls les administrateurs et directeurs peuvent supprimer des managers.', 'error')
                return redirect(url_for('employee.index'))
            else:
                print("Suppression autorisée - utilisateur est admin ou manager")
    
    try:
        print("Début de la suppression...")
        employee_name = f"{employee.first_name} {employee.last_name}"
        
        # Supprimer d'abord les congés associés
        from app.models.leave import Leave
        deleted_leaves = Leave.query.filter_by(employee_id=employee.id).delete()
        print(f"Congés supprimés: {deleted_leaves}")
        
        # Supprimer les relations de management de département
        deleted_managers = DepartmentManager.query.filter_by(employee_id=employee.id).delete()
        print(f"Relations de management supprimées: {deleted_managers}")
        
        # Supprimer l'employé et l'utilisateur associé
        user = employee.user
        db.session.delete(employee)
        db.session.delete(user)
        db.session.commit()
        print(f"Suppression réussie pour: {employee_name}")
        # flash(f'Employé "{employee_name}" supprimé avec succès', 'success')  # Masqué pour environnement professionnel
    except Exception as e:
        print(f"Erreur lors de la suppression: {str(e)}")
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'employé: {str(e)}', 'error')
    
    return redirect(url_for('employee.index'))

@bp.route('/<int:id>/export-pdf')
@login_required
def export_employee_pdf(id):
    """Exporte les informations d'un employé en PDF"""
    # Vérifier les permissions (seuls les admins et managers peuvent exporter)
    if current_user.role not in ['admin', 'manager']:
        # flash('Vous n\'avez pas les permissions pour exporter des rapports', 'error')  # Masqué pour environnement professionnel
        return redirect(url_for('employee.index'))
    
    try:
        pdf_service = PDFExportService()
        pdf_buffer = pdf_service.generate_employee_pdf(id)
        
        employee = Employee.query.get_or_404(id)
        filename = f"rapport_{employee.first_name}_{employee.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        # flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')  # Masqué pour environnement professionnel
        return redirect(url_for('employee.view', id=id))

@bp.route('/export-all-pdf')
@login_required
def export_all_employees_pdf():
    """Exporte tous les employés en PDF"""
    # Vérifier les permissions (seuls les admins et managers peuvent exporter)
    if current_user.role not in ['admin', 'manager']:
        # flash('Vous n\'avez pas les permissions pour exporter des rapports', 'error')  # Masqué pour environnement professionnel
        return redirect(url_for('employee.index'))
    
    try:
        pdf_service = PDFExportService()
        pdf_buffer = pdf_service.generate_all_employees_pdf()
        
        filename = f"rapport_tous_employes_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        # flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')  # Masqué pour environnement professionnel
        return redirect(url_for('employee.index'))