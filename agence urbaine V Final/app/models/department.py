from app import db
from datetime import datetime

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employees = db.relationship('Employee', backref='department', lazy=True)
    manager = db.relationship('Employee',
                            secondary='department_managers',
                            primaryjoin='Department.id==DepartmentManager.department_id',
                            secondaryjoin='DepartmentManager.employee_id==Employee.id',
                            uselist=False,
                            backref=db.backref('managed_department', uselist=False))

    def __repr__(self):
        return f'<Department {self.name}>' 