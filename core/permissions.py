from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios de un objeto editarlo.
    """

    def has_object_permission(self, request, view, obj):
        # El permiso se concede si el objeto pertenece al usuario que hace la petición.
        return obj.user == request.user
