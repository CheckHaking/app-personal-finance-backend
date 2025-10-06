# 🧪 Guía de Testing - Personal Finance Backend

## 📋 Índice
1. [Configuración Inicial](#configuración-inicial)
2. [Ejecutar Pruebas](#ejecutar-pruebas)
3. [Estructura de Pruebas](#estructura-de-pruebas)
4. [Escribir Nuevas Pruebas](#escribir-nuevas-pruebas)
5. [Mejores Prácticas](#mejores-prácticas)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Configuración Inicial

### 1. Instalar Dependencias de Testing

```bash
# Instalar dependencias de testing
pip install -r requirements-test.txt
```

### 2. Configuración de Pytest

El archivo `pytest.ini` ya está configurado con:
- Configuración de Django
- Reporte de cobertura
- Marcadores personalizados

---

## 🏃 Ejecutar Pruebas

### Método Rápido (Script)

```bash
# Ejecutar todas las pruebas
./run_tests.sh

# Con reporte de cobertura
./run_tests.sh coverage

# Solo pruebas rápidas (excluye las lentas)
./run_tests.sh fast

# En paralelo (más rápido)
./run_tests.sh parallel
```

### Método Manual (Pytest)

```bash
# Ejecutar todas las pruebas
pytest

# Con más detalle
pytest -v

# Un archivo específico
pytest core/tests/test_models_complete.py

# Una clase específica
pytest core/tests/test_models_complete.py::TestAccountModel

# Un test específico
pytest core/tests/test_models_complete.py::TestAccountModel::test_credit_card_properties

# Con cobertura
pytest --cov=core --cov=users --cov-report=html

# En paralelo
pytest -n auto
```

### Filtrar por Marcadores

```bash
# Solo pruebas unitarias
pytest -m unit

# Solo pruebas de integración
pytest -m integration

# Excluir pruebas lentas
pytest -m "not slow"
```

---

## 📁 Estructura de Pruebas

```
backend/
├── conftest.py                    # Configuración global de pytest
├── pytest.ini                     # Configuración de pytest
├── requirements-test.txt          # Dependencias de testing
│
├── tests/
│   └── fixtures/
│       ├── __init__.py
│       └── model_factories.py     # Factory Boy factories
│
├── core/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py         # Tests básicos (existentes)
│       ├── test_models_complete.py # Tests completos de modelos
│       ├── test_views.py          # Tests básicos (existentes)
│       └── test_views_complete.py  # Tests completos de vistas
│
└── users/
    └── tests/
        └── test_auth.py           # Tests de autenticación
```

---

## ✍️ Escribir Nuevas Pruebas

### 1. Estructura Básica de un Test

```python
import pytest
from decimal import Decimal

pytestmark = pytest.mark.django_db  # Marca todas las pruebas para usar DB


class TestMiModelo:
    """Tests para MiModelo."""
    
    def test_crear_instancia(self, user):
        """Test crear una instancia básica."""
        # Arrange
        data = {"campo": "valor"}
        
        # Act
        instancia = MiModelo.objects.create(user=user, **data)
        
        # Assert
        assert instancia.campo == "valor"
```

### 2. Usar Factories

```python
def test_con_factory(self, account_factory):
    """Test usando factory."""
    # La factory crea automáticamente todas las relaciones necesarias
    account = account_factory(
        name="Mi Cuenta",
        balance=Decimal("1000.00")
    )
    assert account.balance == Decimal("1000.00")
```

### 3. Tests de API/ViewSets

```python
def test_api_endpoint(self, auth_client, account_factory):
    """Test endpoint de API."""
    account = account_factory(user=auth_client.user)
    
    url = reverse('account-detail', kwargs={'pk': account.id})
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == account.id
```

### 4. Tests con Fechas

```python
from freezegun import freeze_time

@freeze_time("2024-01-15")
def test_con_fecha_fija(self):
    """Test con fecha congelada."""
    assert date.today() == date(2024, 1, 15)
```

---

## 📏 Mejores Prácticas

### 1. **Naming Convention**
- Test files: `test_*.py`
- Test classes: `TestNombreModelo`
- Test methods: `test_descripcion_comportamiento`

### 2. **Arrange-Act-Assert**
```python
def test_ejemplo(self):
    # Arrange: Preparar datos
    data = {"key": "value"}
    
    # Act: Ejecutar acción
    result = mi_funcion(data)
    
    # Assert: Verificar resultado
    assert result == expected
```

### 3. **Un Concepto por Test**
- Cada test debe probar una sola cosa
- Mejor tener múltiples tests pequeños que uno grande

### 4. **Tests Aislados**
- Cada test debe ser independiente
- No depender del orden de ejecución
- Limpiar datos si es necesario

### 5. **Usar Fixtures**
- Para datos compartidos entre tests
- Para configuración común
- Para autenticación

### 6. **Mocking Externo**
```python
from unittest.mock import patch

@patch('requests.get')
def test_api_externa(self, mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    # Tu test aquí
```

---

## 🐛 Troubleshooting

### Error: "No module named 'pytest'"
```bash
pip install -r requirements-test.txt
```

### Error: "Database access not allowed"
Asegúrate de usar el decorador `@pytest.mark.django_db`:
```python
@pytest.mark.django_db
def test_database():
    # Tu test
```

### Tests Lentos
1. Usa `pytest -n auto` para ejecutar en paralelo
2. Marca tests lentos con `@pytest.mark.slow`
3. Ejecuta sin tests lentos: `pytest -m "not slow"`

### Error de Migraciones
```bash
python manage.py migrate --run-syncdb
```

### Ver Output de Print
```bash
pytest -s  # No captura stdout
```

---

## 📊 Cobertura de Código

### Ver Reporte en Terminal
```bash
pytest --cov --cov-report=term-missing
```

### Generar Reporte HTML
```bash
pytest --cov --cov-report=html
open htmlcov/index.html  # En Mac
```

### Objetivos de Cobertura
- Mínimo: 70%
- Recomendado: 85%
- Ideal: 95%+

---

## 🎯 Checklist de Testing

Antes de hacer commit:
- [ ] Ejecutar todas las pruebas: `./run_tests.sh`
- [ ] Verificar cobertura: `./run_tests.sh coverage`
- [ ] Ejecutar linter: `flake8`
- [ ] Verificar tipos: `mypy .` (si está configurado)

---

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Pytest-Django](https://pytest-django.readthedocs.io/)