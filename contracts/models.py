from django.db import models
from django.conf import settings
from clauses.models import Clause

class Contract(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
    ]
    RISK_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    id = models.CharField(primary_key=True, max_length=16)
    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255)
    expiry = models.DateField()
    redlines = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=16, default='v1.0')
    risk = models.CharField(max_length=8, choices=RISK_CHOICES, default='Medium')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Active')
    uploaded = models.DateField(auto_now_add=True)
    clauses = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to='contracts/', null=True, blank=True)
    ai_summary = models.TextField(blank=True, default='')
    ai_extracted_text = models.TextField(blank=True, default='')
    ai_source_file = models.CharField(max_length=500, blank=True, default='')
    ai_analyzed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name



class RedlineSuggestion(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    RISK_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='redline_suggestions')
    clause = models.ForeignKey(Clause, on_delete=models.SET_NULL, null=True, blank=True)
    issue = models.CharField(max_length=255)
    recommendation = models.TextField()
    reviewer_comment = models.TextField(blank=True)
    risk = models.CharField(max_length=8, choices=RISK_CHOICES, default='Medium')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for clause details
    standard_rule = models.TextField(blank=True, default='')
    restricted_terms = models.TextField(blank=True, default='')
    deviation_rule = models.TextField(blank=True, default='')
    ai_recommendation = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.contract_id} - {self.issue}"


class ContractComparison(models.Model):
    title = models.CharField(max_length=255)
    contract_left = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='left_comparisons')
    contract_right = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='right_comparisons')
    external_document = models.CharField(max_length=255, blank=True)
    external_file = models.FileField(upload_to='comparisons/', null=True, blank=True)
    summary = models.TextField(blank=True)
    comparison_detail = models.TextField(blank=True)  # JSON clause-by-clause diff
    exported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    exported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
