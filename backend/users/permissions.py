from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read access to all, write access only to admins."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_admin


class IsAdminOrPharmacist(permissions.BasePermission):
    """Allow access to admins and pharmacists."""
    
    def has_permission(self, request, view):
        return request.user and (request.user.is_admin or request.user.is_pharmacist)


class IsDoctor(permissions.BasePermission):
    """Allow access only to doctors."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_doctor


class IsPatient(permissions.BasePermission):
    """Allow access only to patients."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_patient


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access to object owner or admin."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is user itself
        if isinstance(obj, request.user.__class__):
            return obj == request.user
        
        return False