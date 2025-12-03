from rest_framework import serializers
from .models import Category, Manufacturer, Drug, StockTransaction
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for drug categories."""
    
    total_drugs = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'total_drugs', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_total_drugs(self, obj):
        return obj.drugs.count()


class ManufacturerSerializer(serializers.ModelSerializer):
    """Serializer for manufacturers."""
    
    total_drugs = serializers.SerializerMethodField()
    
    class Meta:
        model = Manufacturer
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone',
            'address', 'total_drugs', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_drugs(self, obj):
        return obj.drugs.count()


class DrugListSerializer(serializers.ModelSerializer):
    """Serializer for drug list view."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'sku',
            'category_name', 'manufacturer_name', 'dosage_form',
            'strength', 'quantity_in_stock', 'reorder_level',
            'unit_price', 'selling_price', 'stock_status',
            'prescription_required', 'expiry_date', 'is_active'
        ]
    
    def get_stock_status(self, obj):
        if obj.is_out_of_stock:
            return 'OUT_OF_STOCK'
        elif obj.is_low_stock:
            return 'LOW_STOCK'
        return 'IN_STOCK'


class DrugDetailSerializer(serializers.ModelSerializer):
    """Detailed drug serializer."""
    
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(),
        source='manufacturer',
        write_only=True,
        required=False
    )
    stock_status = serializers.SerializerMethodField()
    profit_margin = serializers.ReadOnlyField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'sku', 'barcode',
            'category', 'category_id', 'manufacturer', 'manufacturer_id',
            'dosage_form', 'strength', 'description', 'side_effects',
            'usage_instructions', 'quantity_in_stock', 'reorder_level',
            'unit_price', 'selling_price', 'profit_margin', 'stock_status',
            'prescription_required', 'expiry_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_stock_status(self, obj):
        if obj.is_out_of_stock:
            return 'OUT_OF_STOCK'
        elif obj.is_low_stock:
            return 'LOW_STOCK'
        return 'IN_STOCK'


class StockTransactionSerializer(serializers.ModelSerializer):
    """Serializer for stock transactions."""
    
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    drug_id = serializers.PrimaryKeyRelatedField(
        queryset=Drug.objects.all(),
        source='drug',
        write_only=True
    )
    
    class Meta:
        model = StockTransaction
        fields = [
            'id', 'drug', 'drug_id', 'drug_name', 'transaction_type',
            'quantity', 'unit_price', 'total_amount', 'batch_number',
            'expiry_date', 'reference_number', 'notes', 'performed_by',
            'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'total_amount', 'performed_by', 'created_at']
    
    def create(self, validated_data):
        # Automatically update drug stock based on transaction type
        transaction = super().create(validated_data)
        drug = transaction.drug
        
        if transaction.transaction_type in ['PURCHASE', 'RETURN', 'ADJUSTMENT']:
            drug.quantity_in_stock += transaction.quantity
        elif transaction.transaction_type in ['SALE', 'EXPIRED', 'DAMAGED']:
            drug.quantity_in_stock = max(0, drug.quantity_in_stock - transaction.quantity)
        
        drug.save()
        return transaction