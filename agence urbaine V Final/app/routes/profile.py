from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.models.user import User

bp = Blueprint('profile', __name__, url_prefix='/profile')

class ProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    current_password = PasswordField('Mot de passe actuel')
    new_password = PasswordField('Nouveau mot de passe', 
                               validators=[Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères")])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                   validators=[EqualTo('new_password', message='Les mots de passe doivent correspondre')])

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.current_password.data:
            if not current_user.check_password(form.current_password.data):
                flash('Mot de passe actuel incorrect', 'error')
                return render_template('profile/index.html', form=form)
            
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
        
        current_user.email = form.email.data
        current_user.username = form.username.data
        db.session.commit()
        # flash('Profil mis à jour avec succès', 'success')  # Masqué pour environnement professionnel
        return redirect(url_for('profile.index'))
    
    return render_template('profile/index.html', 
                         title='Mon Profil',
                         form=form) 