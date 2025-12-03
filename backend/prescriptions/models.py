from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from inventory.models import Drug

class Prescription(models.Model):
    """Patient prescriptions created by doctors."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FILLED', 'Filled'),
        ('PARTIALLY_FILLED', 'Partially Filled'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Prescription Info
    prescription_number = models.CharField(max_length=50, unique=True, db_index=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions', limit_choices_to={'role': 'PATIENT'})
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_prescriptions', limit_choices_to={'role': 'DOCTOR'})
    
    # Medical Information
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Dates
    issue_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField()
    filled_date = models.DateTimeField(null=True, blank=True)
    filled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='filled_prescriptions', limit_choices_to={'role__in': ['PHARMACIST', 'ADMIN']})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Prescription {self.prescription_number} - {self.patient.get_full_name()}"
    
    @property
    def is_valid(self):
        from django.utils import timezone
        return self.valid_until >= timezone.now().date() and self.status != 'CANCELLED'


class PrescriptionItem(models.Model):
    """Individual drugs in a prescription."""
    
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='prescription_items')
    
    # Dosage Information
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    dosage = models.CharField(max_length=100)  # e.g., "1 tablet"
    frequency = models.CharField(max_length=100)  # e.g., "3 times daily"
    duration = models.CharField(max_length=100)  # e.g., "7 days"
    instructions = models.TextField(blank=True)
    
    # Fulfillment
    quantity_filled = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.drug.name} - {self.quantity} units"
    
    @property
    def is_fully_filled(self):
        return self.quantity_filled >= self.quantity
    
    @property
    def remaining_quantity(self):
        return max(0, self.quantity - self.quantity_filled)