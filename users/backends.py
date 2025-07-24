from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailOrUsernameBackend(ModelBackend):
    """
    Este backend de autenticación permite a los usuarios iniciar sesión
    utilizando su dirección de correo electrónico o su nombre de usuario.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Intenta encontrar al usuario por su nombre de usuario. La búsqueda es insensible a mayúsculas/minúsculas.
            user = UserModel.objects.get(username__iexact=username)
        except UserModel.DoesNotExist:
            try:
                # Si no lo encuentra, intenta buscar por correo electrónico.
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                # Si no se encuentra por ninguno de los dos, no se autentica.
                return None

        # Verifica la contraseña y si el usuario puede autenticarse.
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
