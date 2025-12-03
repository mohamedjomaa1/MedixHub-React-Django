from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from .models import Prescription, PrescriptionItem
from .serializers import (
    PrescriptionListSerializer, PrescriptionDetailSerializer,
    PrescriptionCreateSerializer, FillPrescriptionSerializer
)
from users.permissions import IsDoctor, IsAdminOrPharmacist

class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for prescription management."""
    
    queryset = Prescription.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'status']
    search_fields = ['prescription_number', 'patient__first_name', 'patient__last_name', 'diagnosis']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PrescriptionListSerializer
        elif self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin or user.is_pharmacist:
            return Prescription.objects.all()
        elif user.is_doctor:
            return Prescription.objects.filter(doctor=user)
        elif user.is_patient:
            return Prescription.objects.filter(patient=user)
        
        return Prescription.objects.none()
    
    def perform_create(self, serializer):
        # Doctors create prescriptions
        if not self.request.user.is_doctor:
            raise permissions.PermissionDenied("Only doctors can create prescriptions")
        
        serializer.save(doctor=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrPharmacist])
    def fill(self, request, pk=None):
        """Fill a prescription (pharmacist action)."""
        prescription = self.get_object()
        
        if prescription.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot fill cancelled prescription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not prescription.is_valid:
            return Response(
                {'error': 'Prescription is expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = FillPrescriptionSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Update prescription items
        for item_data in serializer.validated_data:
            item = PrescriptionItem.objects.get(id=item_data['item_id'])
            item.quantity_filled += item_data['quantity_to_fill']
            item.save()
        
        # Update prescription status
        all_filled = all(item.is_fully_filled for item in prescription.items.all())
        if all_filled:
            prescription.status = 'FILLED'
            prescription.filled_date = timezone.now()
            prescription.filled_by = request.user
        else:
            prescription.status = 'PARTIALLY_FILLED'
        
        prescription.save()
        
        return Response({
            'message': 'Prescription filled successfully',
            'status': prescription.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a prescription."""
        prescription = self.get_object()
        
        # Only doctor who issued it or admin can cancel
        if not (request.user.is_admin or request.user == prescription.doctor):
            return Response(
                {'error': 'You do not have permission to cancel this prescription'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if prescription.status == 'FILLED':
            return Response(
                {'error': 'Cannot cancel filled prescription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.status = 'CANCELLED'
        prescription.save()
        
        return Response({'message': 'Prescription cancelled successfully'})
    
    @action(detail=False, methods=['get'])
    def my_prescriptions(self, request):
        """Get prescriptions for current user (patient view)."""
        if request.user.is_patient:
            prescriptions = Prescription.objects.filter(patient=request.user)
        elif request.user.is_doctor:
            prescriptions = Prescription.objects.filter(doctor=request.user)
        else:
            return Response(
                {'error': 'This endpoint is for patients and doctors only'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PrescriptionListSerializer(prescriptions, many=True)
        return Response(serializer.data)