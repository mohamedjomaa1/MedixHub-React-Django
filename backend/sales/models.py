from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from users.models import User
from inventory.models import Drug
from prescriptions.models import Prescription

class Sale(models.Model):
    """Sales transactions."""
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('INSURANCE', 'Insurance'),
        ('MOBILE', 'Mobile Payment'),
    ]
    
    # Sale Information
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases', limit_choices_to={'role': 'PATIENT'})
    customer_name = models.CharField(max_length=200, blank=True)  # For walk-in customers
    customer_phone = models.CharField(max_length=17, blank=True)
    
    # Prescription Reference (if applicable)
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Staff
    sold_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales_made', limit_choices_to={'role__in': ['PHARMACIST', 'RECEPTIONIST', 'ADMIN']})
    
    # Additional Information
    notes = models.TextField(blank=True)
    
    # Timestamps
    sale_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['-sale_date']),
            models.Index(fields=['customer']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.total_amount}"
    
    def calculate_totals(self):
        """Calculate subtotal and total based on sale items."""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = self.subtotal - self.discount + self.tax
        self.change_given = max(0, self.amount_paid - self.total_amount)
        self.save()
    
    @property
    def profit(self):
        """Calculate total profit from this sale."""
        return sum(item.profit for item in self.items.all())


class SaleItem(models.Model):
    """Individual items in a sale."""
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='sale_items')
    
    # Quantity and Pricing
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Batch Information
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.drug.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.selling_price
        super().save(*args, **kwargs)
    
    @property
    def profit(self):
        """Calculate profit for this item."""
        return (self.selling_price - self.unit_price) * self.quantity


class PaymentHistory(models.Model):
    """Track payment history for sales (useful for partial payments)."""
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    payment_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name_plural = "Payment Histories"
    
    def __str__(self):
        return f"Payment {self.amount} for {self.sale.invoice_number}"