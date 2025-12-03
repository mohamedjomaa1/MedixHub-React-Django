from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, F
from datetime import timedelta
from django.utils import timezone
from .models import Sale, SaleItem, PaymentHistory
from .serializers import (
    SaleListSerializer, SaleDetailSerializer,
    SaleCreateSerializer, PaymentHistorySerializer
)
from users.permissions import IsAdminOrPharmacist

class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet for sales management."""
    
    queryset = Sale.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer', 'payment_method', 'sold_by']
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']
    ordering = ['-sale_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SaleListSerializer
        elif self.action == 'create':
            return SaleCreateSerializer
        return SaleDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(sold_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's sales."""
        today = timezone.now().date()
        today_sales = Sale.objects.filter(sale_date__date=today)
        serializer = SaleListSerializer(today_sales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get sales statistics."""
        # Get date range from query params (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        sales = Sale.objects.filter(sale_date__gte=start_date)
        
        stats = {
            'total_sales': sales.count(),
            'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_profit': sum(sale.profit for sale in sales),
            'average_sale': sales.aggregate(avg=Sum('total_amount'))['avg'] or 0,
            'by_payment_method': {},
            'top_selling_drugs': []
        }
        
        # Sales by payment method
        for method_code, method_name in Sale.PAYMENT_METHODS:
            count = sales.filter(payment_method=method_code).count()
            amount = sales.filter(payment_method=method_code).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            stats['by_payment_method'][method_name] = {
                'count': count,
                'amount': float(amount)
            }
        
        # Top selling drugs
        from inventory.models import Drug
        top_drugs = SaleItem.objects.filter(
            sale__sale_date__gte=start_date
        ).values('drug__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_quantity')[:10]
        
        stats['top_selling_drugs'] = list(top_drugs)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def daily_report(self, request):
        """Generate daily sales report."""
        date_str = request.query_params.get('date')
        if date_str:
            from datetime import datetime
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = timezone.now().date()
        
        daily_sales = Sale.objects.filter(sale_date__date=report_date)
        
        report = {
            'date': report_date,
            'total_transactions': daily_sales.count(),
            'total_revenue': daily_sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_profit': sum(sale.profit for sale in daily_sales),
            'cash_sales': daily_sales.filter(payment_method='CASH').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'card_sales': daily_sales.filter(payment_method='CARD').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'sales': SaleListSerializer(daily_sales, many=True).data
        }
        
        return Response(report)


class PaymentHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for payment history."""
    
    queryset = PaymentHistory.objects.all()
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['sale', 'payment_method', 'received_by']
    ordering = ['-payment_date']
    
    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)