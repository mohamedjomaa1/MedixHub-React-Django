from rest_framework import serializers
from .models import Sale, SaleItem, PaymentHistory
from users.serializers import UserSerializer
from inventory.models import Drug
from prescriptions.models import Prescription

from django.contrib.auth import get_user_model

User = get_user_model()

class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for sale items."""
    
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    profit = serializers.ReadOnlyField()
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'drug', 'drug_name', 'quantity', 'unit_price',
            'selling_price', 'total_price', 'batch_number',
            'expiry_date', 'profit'
        ]
        read_only_fields = ['id', 'total_price']


class SaleListSerializer(serializers.ModelSerializer):
    """Serializer for sale list view."""
    
    customer_display = serializers.SerializerMethodField()
    sold_by_name = serializers.CharField(source='sold_by.get_full_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    profit = serializers.ReadOnlyField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'customer', 'customer_display',
            'sold_by_name', 'items_count', 'total_amount', 'profit',
            'payment_method', 'sale_date'
        ]
    
    def get_customer_display(self, obj):
        if obj.customer:
            return obj.customer.get_full_name()
        return obj.customer_name or 'Walk-in Customer'
    
    def get_items_count(self, obj):
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    """Detailed sale serializer."""
    
    customer = UserSerializer(read_only=True)
    sold_by = UserSerializer(read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    profit = serializers.ReadOnlyField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'customer', 'customer_name',
            'customer_phone', 'prescription', 'subtotal', 'discount',
            'tax', 'total_amount', 'amount_paid', 'change_given',
            'payment_method', 'payment_reference', 'sold_by',
            'notes', 'items', 'profit', 'sale_date', 'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'total_amount', 'change_given', 'sold_by', 'created_at']


class SaleCreateSerializer(serializers.Serializer):
    """Serializer for creating sales."""
    
    customer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='PATIENT'),
        required=False,
        allow_null=True
    )
    customer_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=17, required=False, allow_blank=True)
    prescription = serializers.PrimaryKeyRelatedField(
        queryset=Prescription.objects.all(),
        required=False,
        allow_null=True
    )
    
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Sale.PAYMENT_METHODS)
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required")
        
        for item in items:
            if 'drug_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Each item must have drug_id and quantity")
            
            try:
                drug = Drug.objects.get(id=item['drug_id'])
                if drug.quantity_in_stock < item['quantity']:
                    raise serializers.ValidationError(f"Insufficient stock for {drug.name}")
            except Drug.DoesNotExist:
                raise serializers.ValidationError(f"Drug with id {item['drug_id']} not found")
        
        return items
    
    def create(self, validated_data):
        from inventory.models import StockTransaction
        import uuid
        
        items_data = validated_data.pop('items')
        
        # Generate invoice number
        invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        # Create sale
        sale = Sale.objects.create(
            invoice_number=invoice_number,
            **validated_data
        )
        
        # Create sale items and update stock
        for item_data in items_data:
            drug = Drug.objects.get(id=item_data['drug_id'])
            
            # Create sale item
            sale_item = SaleItem.objects.create(
                sale=sale,
                drug=drug,
                quantity=item_data['quantity'],
                unit_price=drug.unit_price,
                selling_price=drug.selling_price
            )
            
            # Update drug stock
            drug.quantity_in_stock -= item_data['quantity']
            drug.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                drug=drug,
                transaction_type='SALE',
                quantity=item_data['quantity'],
                unit_price=drug.unit_price,
                reference_number=invoice_number,
                performed_by=validated_data.get('sold_by')
            )
        
        # Calculate totals
        sale.calculate_totals()
        
        return sale


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history."""
    
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'sale', 'amount', 'payment_method',
            'payment_reference', 'notes', 'received_by',
            'received_by_name', 'payment_date'
        ]
        read_only_fields = ['id', 'received_by', 'payment_date']