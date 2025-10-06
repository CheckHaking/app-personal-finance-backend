from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Alert
from core.views import AlertViewSet
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Check and process all active alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Check alerts for a specific user (username or email)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending notifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_filter = options.get('user')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No notifications will be sent'))
        
        # Obtener usuarios a verificar
        if user_filter:
            users = User.objects.filter(username=user_filter) | User.objects.filter(email=user_filter)
        else:
            users = User.objects.filter(is_active=True)
        
        self.stdout.write(f'Checking alerts for {users.count()} users')
        
        total_alerts_triggered = 0
        alert_viewset = AlertViewSet()
        
        for user in users:
            # Obtener alertas activas del usuario
            alerts = Alert.objects.filter(user=user, is_active=True)
            
            if not alerts.exists():
                continue
            
            self.stdout.write(f'\nChecking {alerts.count()} alerts for {user.username}')
            
            for alert in alerts:
                # Usar el método interno del ViewSet para verificar si debe dispararse
                if alert_viewset._should_trigger(alert):
                    message = alert_viewset._get_alert_message(alert)
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'  - Would trigger: {message}')
                        )
                    else:
                        # Aquí se enviarían las notificaciones reales
                        # Por ahora solo registramos
                        self.stdout.write(
                            self.style.SUCCESS(f'  - Triggered: {message}')
                        )
                        logger.info(f'Alert triggered for user {user.username}: {message}')
                        
                    total_alerts_triggered += 1
        
        # Resumen
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal alerts triggered: {total_alerts_triggered}'
            )
        )