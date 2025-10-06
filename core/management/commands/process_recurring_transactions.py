from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import RecurringTransaction
from datetime import datetime


class Command(BaseCommand):
    help = 'Process recurring transactions that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry mode without creating actual transactions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        
        # Obtener transacciones recurrentes activas con fecha próxima igual o anterior a hoy
        due_transactions = RecurringTransaction.objects.filter(
            is_active=True,
            auto_create=True,
            next_date__lte=today
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN MODE - No transactions will be created'))
        
        self.stdout.write(f'Found {due_transactions.count()} recurring transactions to process')
        
        success_count = 0
        error_count = 0
        
        for recurring in due_transactions:
            try:
                # Verificar si no hay fecha de fin o si aún no se ha alcanzado
                if recurring.end_date and recurring.next_date > recurring.end_date:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {recurring.name} - End date reached'
                        )
                    )
                    recurring.is_active = False
                    recurring.save()
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f'Would create transaction: {recurring.name} for {recurring.amount}'
                    )
                else:
                    transaction = recurring.create_transaction()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created transaction: {recurring.name} for {recurring.amount}'
                        )
                    )
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {recurring.name}: {str(e)}'
                    )
                )
        
        # Resumen
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nProcessed {success_count} transactions successfully'
                )
            )
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'{error_count} transactions failed')
                )