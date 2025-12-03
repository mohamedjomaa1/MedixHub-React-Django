from rest_framework import serializers
from .models import Prescription, PrescriptionItem
from users.serializers import UserSerializer
from inventory.serializers import DrugListSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Serializer for prescription items."""
    
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_details = DrugListSerializer(source='drug', read_only=True)
    remaining_quantity = serializers.ReadOnlyField()
    is_fully_filled = serializers.ReadOnlyField()
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'drug', 'drug_name', 'drug_details', 'quantity',
            'dosage', 'frequency', 'duration', 'instructions',
            'quantity_filled', 'remaining_quantity', 'is_fully_filled'
        ]
        read_only_fields = ['id', 'quantity_filled']


class PrescriptionListSerializer(serializers.ModelSerializer):
    """Serializer for prescription list view."""
    
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_number', 'patient', 'patient_name',
            'doctor', 'doctor_name', 'diagnosis', 'status',
            'items_count', 'issue_date', 'valid_until',
            'is_valid', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """Detailed prescription serializer."""
    
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)
    filled_by = UserSerializer(read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    is_valid = serializers.ReadOnlyField()
    
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='PATIENT'),
        source='patient',
        write_only=True
    )
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='DOCTOR'),
        source='doctor',
        write_only=True
    )
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_number', 'patient', 'patient_id',
            'doctor', 'doctor_id', 'diagnosis', 'notes', 'status',
            'issue_date', 'valid_until', 'filled_date', 'filled_by',
            'items', 'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'prescription_number', 'issue_date', 'filled_date', 'filled_by', 'created_at', 'updated_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescriptions with items."""
    
    items = PrescriptionItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'patient', 'doctor', 'diagnosis', 'notes',
            'valid_until', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Generate prescription number
        import uuid
        prescription_number = f"RX-{uuid.uuid4().hex[:8].upper()}"
        
        prescription = Prescription.objects.create(
            prescription_number=prescription_number,
            **validated_data
        )
        
        # Create prescription items
        for item_data in items_data:
            PrescriptionItem.objects.create(
                prescription=prescription,
                **item_data
            )
        
        return prescription


class FillPrescriptionSerializer(serializers.Serializer):
    """Serializer for filling prescriptions."""
    
    item_id = serializers.IntegerField()
    quantity_to_fill = serializers.IntegerField(min_value=1)
    
    def validate(self, attrs):
        try:
            item = PrescriptionItem.objects.get(id=attrs['item_id'])
            if item.quantity_filled + attrs['quantity_to_fill'] > item.quantity:
                raise serializers.ValidationError("Cannot fill more than prescribed quantity")
        except PrescriptionItem.DoesNotExist:
            raise serializers.ValidationError("Prescription item not found")
        return attrs