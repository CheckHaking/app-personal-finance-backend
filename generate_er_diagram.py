#!/usr/bin/env python
"""
Script para generar diagrama ER del modelo de datos en formato Mermaid
Este diagrama puede ser convertido a imagen usando https://mermaid.live o herramientas similares
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps

def generate_mermaid_er():
    """Genera diagrama ER en formato Mermaid"""

    output = ["erDiagram"]

    # Modelos principales
    models = {
        'users.User': 'User',
        'users.Profile': 'Profile',
        'core.Category': 'Category',
        'core.Account': 'Account',
        'core.Transaction': 'Transaction',
        'core.Transfer': 'Transfer',
        'core.Budget': 'Budget',
        'core.BudgetLine': 'BudgetLine',
        'core.SavingsGoal': 'SavingsGoal',
        'core.Tag': 'Tag',
        'core.RecurringTransaction': 'RecurringTransaction',
        'core.TransactionReceipt': 'TransactionReceipt',
        'core.SharedExpense': 'SharedExpense',
        'core.SharedExpenseParticipant': 'SharedExpenseParticipant',
        'core.Alert': 'Alert',
        'core.UserOnboarding': 'UserOnboarding',
    }

    # Definir entidades con atributos clave
    entities = {
        'User': [
            'int id PK',
            'string username',
            'string email',
            'string password',
            'datetime date_joined',
        ],
        'Profile': [
            'int id PK',
            'int user_id FK',
            'image profile_picture',
            'string default_currency',
        ],
        'Category': [
            'int id PK',
            'int user_id FK',
            'string name',
            'string type',
            'string color',
        ],
        'Account': [
            'int id PK',
            'int user_id FK',
            'string name',
            'string type',
            'decimal balance',
            'string currency',
            'decimal credit_limit',
        ],
        'Transaction': [
            'int id PK',
            'int user_id FK',
            'int account_id FK',
            'int category_id FK',
            'string transaction_type',
            'decimal amount',
            'date date',
        ],
        'Transfer': [
            'int id PK',
            'int user_id FK',
            'int from_account_id FK',
            'int to_account_id FK',
            'decimal amount',
            'date date',
        ],
        'Budget': [
            'int id PK',
            'int user_id FK',
            'string name',
            'string period_type',
            'date start_date',
            'date end_date',
        ],
        'BudgetLine': [
            'int id PK',
            'int budget_id FK',
            'int category_id FK',
            'decimal amount',
        ],
        'SavingsGoal': [
            'int id PK',
            'int user_id FK',
            'int linked_account_id FK',
            'string name',
            'decimal target_amount',
            'date target_date',
        ],
        'RecurringTransaction': [
            'int id PK',
            'int user_id FK',
            'int account_id FK',
            'int category_id FK',
            'string frequency',
            'date next_date',
        ],
        'UserOnboarding': [
            'int id PK',
            'int user_id FK',
            'int current_step',
            'boolean completed',
        ],
    }

    # Generar definiciones de entidades
    for entity, fields in entities.items():
        output.append(f"\n    {entity} {{")
        for field in fields:
            output.append(f"        {field}")
        output.append("    }")

    # Definir relaciones
    relationships = [
        # User relationships
        ('User', '||--||', 'Profile', 'has'),
        ('User', '||--o{', 'Category', 'owns'),
        ('User', '||--o{', 'Account', 'owns'),
        ('User', '||--o{', 'Transaction', 'creates'),
        ('User', '||--o{', 'Transfer', 'makes'),
        ('User', '||--o{', 'Budget', 'creates'),
        ('User', '||--o{', 'SavingsGoal', 'sets'),
        ('User', '||--||', 'UserOnboarding', 'has'),

        # Account relationships
        ('Account', '||--o{', 'Transaction', 'contains'),
        ('Account', '||--o{', 'Transfer', 'receives'),
        ('Account', '||--o{', 'Transfer', 'sends'),

        # Category relationships
        ('Category', '||--o{', 'Transaction', 'categorizes'),
        ('Category', '||--o{', 'BudgetLine', 'limits'),

        # Budget relationships
        ('Budget', '||--o{', 'BudgetLine', 'contains'),

        # Transaction relationships
        ('Transaction', '||--o{', 'TransactionReceipt', 'has'),

        # RecurringTransaction relationships
        ('RecurringTransaction', '||--o{', 'Transaction', 'generates'),
    ]

    output.append("\n    %% Relationships")
    for left, rel, right, label in relationships:
        output.append(f"    {left} {rel} {right} : {label}")

    return "\n".join(output)

def generate_text_er():
    """Genera diagrama ER en formato texto plano"""

    output = []
    output.append("=" * 80)
    output.append("DIAGRAMA ENTIDAD-RELACIÓN - PERSONAL FINANCE APP")
    output.append("=" * 80)
    output.append("\n")

    # Entidades principales
    output.append("ENTIDADES PRINCIPALES:")
    output.append("-" * 80)

    entities = {
        'User': {
            'desc': 'Usuario del sistema',
            'attrs': ['id (PK)', 'username', 'email', 'password', 'date_joined'],
        },
        'Profile': {
            'desc': 'Perfil de usuario con configuración personal',
            'attrs': ['id (PK)', 'user_id (FK)', 'profile_picture', 'default_currency'],
        },
        'Account': {
            'desc': 'Cuentas financieras (efectivo, banco, crédito, inversión)',
            'attrs': ['id (PK)', 'user_id (FK)', 'name', 'type', 'balance', 'currency', 'credit_limit'],
        },
        'Transaction': {
            'desc': 'Transacciones (ingresos, gastos)',
            'attrs': ['id (PK)', 'user_id (FK)', 'account_id (FK)', 'category_id (FK)', 'amount', 'date'],
        },
        'Category': {
            'desc': 'Categorías para clasificar transacciones',
            'attrs': ['id (PK)', 'user_id (FK)', 'name', 'type', 'color'],
        },
        'Budget': {
            'desc': 'Presupuestos por periodo',
            'attrs': ['id (PK)', 'user_id (FK)', 'name', 'period_type', 'start_date', 'end_date'],
        },
        'SavingsGoal': {
            'desc': 'Metas de ahorro',
            'attrs': ['id (PK)', 'user_id (FK)', 'name', 'target_amount', 'target_date'],
        },
        'RecurringTransaction': {
            'desc': 'Plantillas para transacciones recurrentes',
            'attrs': ['id (PK)', 'user_id (FK)', 'frequency', 'next_date', 'amount'],
        },
    }

    for entity, info in entities.items():
        output.append(f"\n{entity}")
        output.append(f"  Descripción: {info['desc']}")
        output.append(f"  Atributos:")
        for attr in info['attrs']:
            output.append(f"    - {attr}")

    output.append("\n" + "=" * 80)
    output.append("RELACIONES:")
    output.append("-" * 80)

    relationships = [
        ('User', 'Profile', '1:1', 'Un usuario tiene un perfil'),
        ('User', 'Account', '1:N', 'Un usuario tiene múltiples cuentas'),
        ('User', 'Transaction', '1:N', 'Un usuario crea múltiples transacciones'),
        ('User', 'Category', '1:N', 'Un usuario define múltiples categorías'),
        ('User', 'Budget', '1:N', 'Un usuario crea múltiples presupuestos'),
        ('User', 'SavingsGoal', '1:N', 'Un usuario establece múltiples metas'),
        ('Account', 'Transaction', '1:N', 'Una cuenta contiene múltiples transacciones'),
        ('Category', 'Transaction', '1:N', 'Una categoría clasifica múltiples transacciones'),
        ('Budget', 'BudgetLine', '1:N', 'Un presupuesto tiene múltiples líneas'),
        ('Category', 'BudgetLine', '1:N', 'Una categoría puede estar en múltiples líneas'),
    ]

    for left, right, card, desc in relationships:
        output.append(f"\n{left} --[{card}]-- {right}")
        output.append(f"  {desc}")

    output.append("\n" + "=" * 80)

    return "\n".join(output)

if __name__ == '__main__':
    print("Generando diagramas ER...\n")

    # Generar Mermaid
    mermaid_output = generate_mermaid_er()
    mermaid_file = os.path.join(os.path.dirname(__file__), '..', 'docs', 'er_diagram.mmd')
    os.makedirs(os.path.dirname(mermaid_file), exist_ok=True)

    with open(mermaid_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_output)

    print(f"✅ Diagrama Mermaid generado: {mermaid_file}")
    print("   Puedes visualizarlo en: https://mermaid.live")

    # Generar texto plano
    text_output = generate_text_er()
    text_file = os.path.join(os.path.dirname(__file__), '..', 'docs', 'er_diagram.txt')

    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_output)

    print(f"✅ Diagrama texto generado: {text_file}")

    print("\n" + "=" * 80)
    print("DIAGRAMA MERMAID:")
    print("=" * 80)
    print(mermaid_output)
