from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from io import BytesIO
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.department import Department
from app import db

class PDFExportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        # Style pour les informations personnelles
        self.styles.add(ParagraphStyle(
            name='InfoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=20
        ))
    
    def calculate_leave_balance(self, employee):
        """Calcule le solde de congés d'un employé"""
        # Utiliser le solde personnalisé de l'employé
        annual_leaves = employee.annual_leave_days
        
        # Calculer les congés pris cette année
        current_year = datetime.now().year
        taken_leaves = Leave.query.filter(
            Leave.employee_id == employee.id,
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
    
    def generate_employee_pdf(self, employee_id):
        """Génère un PDF pour un employé spécifique"""
        employee = Employee.query.get_or_404(employee_id)
        leave_balance = self.calculate_leave_balance(employee)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # En-tête
        story.append(Paragraph("AGENCE URBAINE DE TAZA-TAOUNATE", self.styles['CustomTitle']))
        story.append(Paragraph("Rapport Personnel - Informations Employé", self.styles['CustomHeading']))
        story.append(Spacer(1, 20))
        
        # Informations personnelles
        story.append(Paragraph("INFORMATIONS PERSONNELLES", self.styles['CustomHeading']))
        
        personal_info = [
            ["Nom complet:", f"{employee.first_name} {employee.last_name}"],
            ["Date de naissance:", employee.date_of_birth.strftime("%d/%m/%Y")],
            ["Genre:", employee.gender],
            ["Adresse:", employee.address or "Non renseignée"],
            ["Téléphone:", employee.phone or "Non renseigné"],
            ["Date d'embauche:", employee.hire_date.strftime("%d/%m/%Y")],
            ["Poste:", employee.position],
            ["Département:", employee.department.name if employee.department else "Non assigné"]
        ]
        
        personal_table = Table(personal_info, colWidths=[2*inch, 3*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(personal_table)
        story.append(Spacer(1, 20))
        
        # Solde de congés
        story.append(Paragraph("SOLDE DE CONGÉS", self.styles['CustomHeading']))
        
        leave_info = [
            ["Congés annuels accordés:", f"{leave_balance['annual']} jours"],
            ["Congés pris cette année:", f"{leave_balance['taken']} jours"],
            ["Solde restant:", f"{leave_balance['balance']} jours"]
        ]
        
        leave_table = Table(leave_info, colWidths=[2.5*inch, 2.5*inch])
        leave_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightcyan),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(leave_table)
        story.append(Spacer(1, 20))
        
        # Historique des congés récents
        recent_leaves = Leave.query.filter(
            Leave.employee_id == employee.id,
            Leave.status == 'approved'
        ).order_by(Leave.start_date.desc()).limit(5).all()
        
        if recent_leaves:
            story.append(Paragraph("HISTORIQUE DES CONGÉS RÉCENTS", self.styles['CustomHeading']))
            
            leave_history = [["Date début", "Date fin", "Type", "Durée", "Statut"]]
            for leave in recent_leaves:
                duration = (leave.end_date - leave.start_date).days + 1
                leave_history.append([
                    leave.start_date.strftime("%d/%m/%Y"),
                    leave.end_date.strftime("%d/%m/%Y"),
                    leave.leave_type.title(),
                    f"{duration} jour(s)",
                    leave.status.title()
                ])
            
            history_table = Table(leave_history, colWidths=[1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch])
            history_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(history_table)
        
        # Pied de page
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
                              self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_all_employees_pdf(self):
        """Génère un PDF avec tous les employés"""
        employees = Employee.query.all()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # En-tête
        story.append(Paragraph("AGENCE URBAINE DE TAZA-TAOUNATE", self.styles['CustomTitle']))
        story.append(Paragraph("Rapport Global - Tous les Employés", self.styles['CustomHeading']))
        story.append(Spacer(1, 20))
        
        # Tableau récapitulatif
        story.append(Paragraph("RÉCAPITULATIF GÉNÉRAL", self.styles['CustomHeading']))
        
        summary_data = [["Nom", "Poste", "Département", "Congés pris", "Solde restant"]]
        
        for employee in employees:
            leave_balance = self.calculate_leave_balance(employee)
            summary_data.append([
                f"{employee.first_name} {employee.last_name}",
                employee.position,
                employee.department.name if employee.department else "Non assigné",
                f"{leave_balance['taken']} jours",
                f"{leave_balance['balance']} jours"
            ])
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Détails par employé
        for employee in employees:
            story.append(Paragraph(f"DÉTAILS - {employee.first_name.upper()} {employee.last_name.upper()}", 
                                  self.styles['CustomHeading']))
            
            leave_balance = self.calculate_leave_balance(employee)
            
            employee_details = [
                ["Date d'embauche:", employee.hire_date.strftime("%d/%m/%Y")],
                ["Téléphone:", employee.phone or "Non renseigné"],
                ["Congés annuels:", f"{leave_balance['annual']} jours"],
                ["Congés pris:", f"{leave_balance['taken']} jours"],
                ["Solde restant:", f"{leave_balance['balance']} jours"]
            ]
            
            details_table = Table(employee_details, colWidths=[2*inch, 2*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, -1), colors.lightcyan),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 15))
        
        # Pied de page
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
                              self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
