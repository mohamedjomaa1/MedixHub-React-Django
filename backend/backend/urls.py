from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import ViewSets
from users.views import UserViewSet
from inventory.views import CategoryViewSet, ManufacturerViewSet, DrugViewSet, StockTransactionViewSet
from prescriptions.views import PrescriptionViewSet
from sales.views import SaleViewSet, PaymentHistoryViewSet
from reports.views import DashboardView, InventoryReportView, SalesReportView

# Create router
router = DefaultRouter()

# Register routes
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'manufacturers', ManufacturerViewSet, basename='manufacturer')
router.register(r'drugs', DrugViewSet, basename='drug')
router.register(r'stock-transactions', StockTransactionViewSet, basename='stock-transaction')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'payment-history', PaymentHistoryViewSet, basename='payment-history')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Reports
    path('api/reports/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/reports/inventory/', InventoryReportView.as_view(), name='inventory-report'),
    path('api/reports/sales/', SalesReportView.as_view(), name='sales-report'),
    
    # API routes
    path('api/', include(router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)