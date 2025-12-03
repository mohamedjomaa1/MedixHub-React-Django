from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    """Drug categories (e.g., Antibiotics, Pain Relief, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Pharmaceutical manufacturers."""
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Drug(models.Model):
    """Main drug/medicine model."""
    
    DOSAGE_FORMS = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('SYRUP', 'Syrup'),
        ('INJECTION', 'Injection'),
        ('CREAM', 'Cream'),
        ('DROPS', 'Drops'),
        ('INHALER', 'Inhaler'),
        ('OINTMENT', 'Ointment'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, db_index=True)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='drugs')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, related_name='drugs')
    
    # Drug Details
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORMS)
    strength = models.CharField(max_length=50)  # e.g., "500mg", "5ml"
    description = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    usage_instructions = models.TextField(blank=True)
    
    # Inventory Management
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    quantity_in_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=20, validators=[MinValueValidator(0)])
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Regulatory
    prescription_required = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'sku']),
            models.Index(fields=['quantity_in_stock']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level
    
    @property
    def is_out_of_stock(self):
        return self.quantity_in_stock == 0
    
    @property
    def profit_margin(self):
        if self.unit_price > 0:
            return ((self.selling_price - self.unit_price) / self.unit_price) * 100
        return 0


class StockTransaction(models.Model):
    """Track all stock movements (additions and removals)."""
    
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
    ]
    
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    reference_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='stock_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['drug', 'transaction_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.drug.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)