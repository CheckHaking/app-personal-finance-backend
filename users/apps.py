"""
En este archivo se indentifica la app "Hola yo soy la app users

Ejecutar codigo al iniciar la app

"""


from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        #Importa las señales 
        import users.signals
        return super().ready()
