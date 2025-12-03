from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from users.models import User
from inventory.models import Drug, StockTransaction
from prescriptions.models import Prescription
from sales.models import Sale, SaleItem

class DashboardView(APIView):
    """Main dashboard statistics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Admin and Pharmacist get full dashboard
        if user.is_admin or user.is_pharmacist:
            return Response(self._get_full_dashboard())
        
        # Doctor gets doctor-specific data
        elif user.is_doctor:
            return Response(self._get_doctor_dashboard(user))
        
        # Patient gets patient-specific data
        elif user.is_patient:
            return Response(self._get_patient_dashboard(user))
        
        return Response({'error': 'Invalid role'}, status=status.HTTP_403_FORBIDDEN)
    
    def _get_full_dashboard(self):
        """Full dashboard for admin/pharmacist."""
        today = timezone.now().date()
        last_30_days = timezone.now() - timedelta(days=30)
        
        return {
            'inventory': {
                'total_drugs': Drug.objects.filter(is_active=True).count(),
                'low_stock': Drug.objects.filter(
                    quantity_in_stock__lte=F('reorder_level'),
                    is_active=True
                ).count(),
                'out_of_stock': Drug.objects.filter(
                    quantity_in_stock=0,
                    is_active=True
                ).count(),
                'total_value': Drug.objects.aggregate(
                    total=Sum(F('quantity_in_stock') * F('unit_price'))
                )['total'] or 0,
            },
            'sales': {
                'today': Sale.objects.filter(sale_date__date=today).count(),
                'today_revenue': Sale.objects.filter(
                    sale_date__date=today
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
                'last_30_days': Sale.objects.filter(sale_date__gte=last_30_days).count(),
                'last_30_days_revenue': Sale.objects.filter(
                    sale_date__gte=last_30_days
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
            },
            'prescriptions': {
                'pending': Prescription.objects.filter(status='PENDING').count(),
                'filled_today': Prescription.objects.filter(
                    status='FILLED',
                    filled_date__date=today
                ).count(),
                'total_active': Prescription.objects.filter(
                    status__in=['PENDING', 'PARTIALLY_FILLED']
                ).count(),
            },
            'users': {
                'total': User.objects.filter(is_active=True).count(),
                'patients': User.objects.filter(role='PATIENT', is_active=True).count(),
                'doctors': User.objects.filter(role='DOCTOR', is_active=True).count(),
                'pharmacists': User.objects.filter(role='PHARMACIST', is_active=True).count(),
            },
            'alerts': self._get_alerts(),
        }
    
    def _get_doctor_dashboard(self, user):
        """Dashboard for doctors."""
        today = timezone.now().date()
        
        return {
            'prescriptions': {
                'total_issued': user.issued_prescriptions.count(),
                'pending': user.issued_prescriptions.filter(status='PENDING').count(),
                'filled': user.issued_prescriptions.filter(status='FILLED').count(),
                'recent': user.issued_prescriptions.order_by('-created_at')[:10].values(
                    'id', 'prescription_number', 'patient__first_name',
                    'patient__last_name', 'status', 'created_at'
                ),
            },
            'patients': {
                'total': Prescription.objects.filter(doctor=user).values('patient').distinct().count(),
            },
        }
    
    def _get_patient_dashboard(self, user):
        """Dashboard for patients."""
        return {
            'prescriptions': {
                'total': user.prescriptions.count(),
                'pending': user.prescriptions.filter(status='PENDING').count(),
                'filled': user.prescriptions.filter(status='FILLED').count(),
                'recent': user.prescriptions.order_by('-created_at')[:10].values(
                    'id', 'prescription_number', 'doctor__first_name',
                    'doctor__last_name', 'status', 'created_at'
                ),
            },
            'purchases': {
                'total': user.purchases.count(),
                'total_spent': user.purchases.aggregate(
                    total=Sum('total_amount')
                )['total'] or 0,
            },
        }
    
    def _get_alerts(self):
        """Get system alerts."""
        from datetime import timedelta
        threshold_date = timezone.now().date() + timedelta(days=30)
        
        return {
            'low_stock_drugs': Drug.objects.filter(
                quantity_in_stock__lte=F('reorder_level'),
                is_active=True
            ).count(),
            'expiring_drugs': Drug.objects.filter(
                expiry_date__lte=threshold_date,
                expiry_date__gte=timezone.now().date(),
                is_active=True
            ).count(),
            'pending_prescriptions': Prescription.objects.filter(
                status='PENDING'
            ).count(),
        }


class InventoryReportView(APIView):
    """Inventory analysis and reports."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        report_type = request.query_params.get('type', 'overview')
        
        if report_type == 'overview':
            return Response(self._get_inventory_overview())
        elif report_type == 'valuation':
            return Response(self._get_inventory_valuation())
        elif report_type == 'movement':
            return Response(self._get_stock_movement())
        
        return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_inventory_overview(self):
        """Overview of inventory status."""
        drugs = Drug.objects.filter(is_active=True)
        
        return {
            'total_items': drugs.count(),
            'in_stock': drugs.filter(quantity_in_stock__gt=0).count(),
            'low_stock': drugs.filter(quantity_in_stock__lte=F('reorder_level')).count(),
            'out_of_stock': drugs.filter(quantity_in_stock=0).count(),
            'by_category': list(drugs.values('category__name').annotate(
                count=Count('id'),
                total_value=Sum(F('quantity_in_stock') * F('unit_price'))
            )),
        }
    
    def _get_inventory_valuation(self):
        """Inventory valuation report."""
        drugs = Drug.objects.filter(is_active=True)
        
        return {
            'total_cost_value': drugs.aggregate(
                total=Sum(F('quantity_in_stock') * F('unit_price'))
            )['total'] or 0,
            'total_selling_value': drugs.aggregate(
                total=Sum(F('quantity_in_stock') * F('selling_price'))
            )['total'] or 0,
            'by_category': list(drugs.values('category__name').annotate(
                cost_value=Sum(F('quantity_in_stock') * F('unit_price')),
                selling_value=Sum(F('quantity_in_stock') * F('selling_price'))
            )),
        }
    
    def _get_stock_movement(self):
        """Stock movement analysis."""
        days = int(self.request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        transactions = StockTransaction.objects.filter(created_at__gte=start_date)
        
        return {
            'total_transactions': transactions.count(),
            'by_type': list(transactions.values('transaction_type').annotate(
                count=Count('id'),
                total_quantity=Sum('quantity'),
                total_amount=Sum('total_amount')
            )),
            'recent_transactions': list(transactions.order_by('-created_at')[:20].values(
                'drug__name', 'transaction_type', 'quantity',
                'total_amount', 'created_at'
            )),
        }


class SalesReportView(APIView):
    """Sales analysis and reports."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        sales = Sale.objects.filter(sale_date__gte=start_date)
        
        return Response({
            'summary': self._get_sales_summary(sales),
            'trends': self._get_sales_trends(sales),
            'top_products': self._get_top_products(sales),
        })
    
    def _get_sales_summary(self, sales):
        """Sales summary statistics."""
        return {
            'total_transactions': sales.count(),
            'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_profit': sum(sale.profit for sale in sales),
            'average_transaction': sales.aggregate(avg=Sum('total_amount'))['avg'] or 0,
        }
    
    def _get_sales_trends(self, sales):
        """Daily sales trends."""
        return list(sales.extra(
            select={'date': 'DATE(sale_date)'}
        ).values('date').annotate(
            transactions=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('date'))
    
    def _get_top_products(self, sales):
        """Top selling products."""
        return list(SaleItem.objects.filter(
            sale__in=sales
        ).values('drug__name').annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-quantity_sold')[:10])