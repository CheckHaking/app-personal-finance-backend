#!/usr/bin/env python
import json

# Ejemplo de datos que debería enviar el frontend
contribute_data = {
    "amount": 500.00,
    "account_id": 1,  # ID de la cuenta desde la cual se hace la contribución
    "description": "Ahorro mensual"
}

print("El frontend debe enviar estos datos al endpoint POST /api/v1/savings-goals/{id}/contribute/:")
print(json.dumps(contribute_data, indent=2))

print("\nFormato esperado:")
print("- amount: número decimal positivo (requerido)")
print("- account_id: ID de la cuenta origen (requerido)")
print("- description: texto descriptivo (opcional)")

print("\nEjemplo con curl:")
print("""
curl -X POST http://127.0.0.1:8001/api/v1/savings-goals/1/contribute/ \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 500.00,
    "account_id": 1,
    "description": "Ahorro mensual"
  }'
""")