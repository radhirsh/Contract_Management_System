from django.db import models

class Clause(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
    ]
    RISK_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    CATEGORY_CHOICES = [
        ('Legal', 'Legal'),
        ('Finance', 'Finance'),
        ('Liability', 'Liability'),
        ('Operational', 'Operational'),
    ]
    id = models.CharField(primary_key=True, max_length=16)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='Legal')
    risk = models.CharField(max_length=8, choices=RISK_CHOICES, default='Medium')
    version = models.CharField(max_length=16, default='v1.0')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Pending')
    document = models.FileField(upload_to='clauses/', null=True, blank=True)
    mandatory = models.BooleanField(default=True)
    standard_rule = models.TextField(null=True, blank=True)
    restricted_terms = models.TextField(null=True, blank=True)
    deviation_rule = models.TextField(null=True, blank=True)
    ai_recommendation = models.TextField(null=True, blank=True)
    escalation_required = models.BooleanField(default=False)
    clause_category = models.CharField(max_length=255, choices=[
        ('Confidentiality', 'Confidentiality'),
        ('Payment Terms', 'Payment Terms'),
        ('Liability', 'Liability'),
        ('Indemnity', 'Indemnity'),
        ('Governing Law', 'Governing Law'),
        ('Termination', 'Termination'),
        ('Data Privacy', 'Data Privacy'),
        ('Intellectual Property', 'Intellectual Property'),
        ('Renewal', 'Renewal'),
        ('Service Levels', 'Service Levels'),
        ('Audit Rights', 'Audit Rights'),
        ('Insurance', 'Insurance'),
        ('Compliance', 'Compliance'),
        ('Security', 'Security'),
        ('Force Majeure', 'Force Majeure'),
        ('Assignment', 'Assignment'),
        ('Subcontracting', 'Subcontracting')
    ], default='Confidentiality')
    clause_name = models.CharField(max_length=255, default='')
    risk_level = models.CharField(max_length=255, choices=[
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    ], default='Medium')
    standard_rule_value = models.TextField(default='No standard rule provided')
    restricted_terms_conditions = models.TextField(default='No restricted terms provided')
    deviation_rule = models.TextField(default='No deviation rule provided')
    ai_recommendation = models.TextField(default='No AI recommendation provided')
    escalation_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name
