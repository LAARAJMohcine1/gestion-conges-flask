from app import db
from datetime import datetime, date

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    position = db.Column(db.String(100), nullable=False)
    is_manager = db.Column(db.Boolean, default=False)
    annual_leave_days = db.Column(db.Integer, default=22, nullable=False)  # Jours de congés annuels accordés
    
    # Relations
    leaves = db.relationship('Leave', backref='employee', lazy=True)
    
    def calculate_leave_balance(self):
        """Calcule le solde de congés de l'employé"""
        # Utiliser le solde personnalisé de l'employé
        annual_leaves = self.annual_leave_days
        
        # Calculer les congés pris cette année
        current_year = datetime.now().year
        from app.models.leave import Leave
        taken_leaves = Leave.query.filter(
            Leave.employee_id == self.id,
            Leave.status == 'approved',
            db.func.extract('year', Leave.start_date) == current_year
        ).all()
        
        total_taken = sum(
            (leave.end_date - leave.start_date).days + 1 
            for leave in taken_leaves
        )
        
        balance = annual_leaves - total_taken
        return {
            'annual': annual_leaves,
            'taken': total_taken,
            'balance': max(0, balance)
        }
    
    def calculate_seniority_years(self):
        """Calcule l'ancienneté en années"""
        today = date.today()
        hire_date = self.hire_date
        return today.year - hire_date.year - ((today.month, today.day) < (hire_date.month, hire_date.day))
    
    @property
    def leave_balance(self):
        """Propriété pour accéder facilement au solde de congés"""
        return self.calculate_leave_balance()
    
    @property
    def seniority_years(self):
        """Propriété pour accéder facilement à l'ancienneté"""
        return self.calculate_seniority_years()

    def __repr__(self):
        return f'<Employee {self.first_name} {self.last_name}>' 