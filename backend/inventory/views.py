from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import models
from .models import Category, Manufacturer, Drug, StockTransaction
from .serializers import (
    CategorySerializer, ManufacturerSerializer,
    DrugListSerializer, DrugDetailSerializer, StockTransactionSerializer
)
from users.permissions import IsAdminOrPharmacist

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for drug categories."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']


class ManufacturerViewSet(viewsets.ModelViewSet):
    """ViewSet for manufacturers."""
    
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']


class DrugViewSet(viewsets.ModelViewSet):
    """ViewSet for drug management."""
    
    queryset = Drug.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'manufacturer', 'dosage_form', 'prescription_required', 'is_active']
    search_fields = ['name', 'generic_name', 'brand_name', 'sku', 'barcode']
    ordering_fields = ['name', 'quantity_in_stock', 'selling_price', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DrugListSerializer
        return DrugDetailSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get drugs with low stock."""
        low_stock_drugs = Drug.objects.filter(
            quantity_in_stock__lte=models.F('reorder_level'),
            is_active=True
        )
        serializer = DrugListSerializer(low_stock_drugs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock drugs."""
        out_of_stock_drugs = Drug.objects.filter(
            quantity_in_stock=0,
            is_active=True
        )
        serializer = DrugListSerializer(out_of_stock_drugs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get drugs expiring within 30 days."""
        from datetime import timedelta
        threshold_date = timezone.now().date() + timedelta(days=30)
        
        expiring_drugs = Drug.objects.filter(
            expiry_date__lte=threshold_date,
            expiry_date__gte=timezone.now().date(),
            is_active=True
        )
        serializer = DrugListSerializer(expiring_drugs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get inventory statistics."""
        from django.db.models import Sum, Count, F
        
        stats = {
            'total_drugs': Drug.objects.filter(is_active=True).count(),
            'low_stock_count': Drug.objects.filter(
                quantity_in_stock__lte=F('reorder_level'),
                is_active=True
            ).count(),
            'out_of_stock_count': Drug.objects.filter(
                quantity_in_stock=0,
                is_active=True
            ).count(),
            'total_value': Drug.objects.aggregate(
                total=Sum(F('quantity_in_stock') * F('unit_price'))
            )['total'] or 0,
            'categories_count': Category.objects.count(),
            'manufacturers_count': Manufacturer.objects.count(),
        }
        
        return Response(stats)


class StockTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for stock transactions."""
    
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['drug', 'transaction_type', 'performed_by']
    search_fields = ['drug__name', 'reference_number', 'batch_number']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_drug(self, request):
        """Get transactions for a specific drug."""
        drug_id = request.query_params.get('drug_id')
        if not drug_id:
            return Response(
                {'error': 'drug_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transactions = self.queryset.filter(drug_id=drug_id)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)