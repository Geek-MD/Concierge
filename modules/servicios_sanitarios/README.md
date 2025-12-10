# Concierge - Servicios Sanitarios

## Descripción

El módulo de **Servicios Sanitarios** es el primer componente del sistema Concierge. Este módulo está diseñado para automatizar y gestionar tareas relacionadas con servicios sanitarios.

## Estado Actual

🚧 **Proof of Concept (PoC)** - Versión inicial en Python

Este es un prototipo funcional desarrollado para validar la arquitectura y funcionalidad del módulo. Dependiendo de los resultados y requisitos futuros, el lenguaje de programación podría ser migrado a tecnologías más actuales.

## Características Principales

- **Modularidad**: Funciona de manera independiente dentro del ecosistema Concierge
- **Extensibilidad**: Diseñado para agregar nuevas funcionalidades fácilmente
- **Simplicidad**: API clara y directa para integración con otros módulos

## Estructura del Módulo

```
servicios_sanitarios/
├── README.md                    # Este archivo
├── requirements.txt             # Dependencias del módulo
├── src/                         # Código fuente
│   ├── __init__.py             # Inicialización del módulo
│   ├── core.py                 # Funcionalidad principal
│   └── utils.py                # Utilidades y funciones auxiliares
└── tests/                       # Pruebas unitarias
    ├── __init__.py
    └── test_core.py            # Tests del módulo principal
```

## Instalación

```bash
# Desde el directorio del módulo
cd modules/servicios_sanitarios
pip install -r requirements.txt
```

## Uso

```python
from modules.servicios_sanitarios.src import core

# Ejemplo de uso básico
# (Los ejemplos específicos se agregarán según la implementación)
```

## Desarrollo

### Requisitos de Desarrollo

- Python 3.8+
- pytest (para pruebas)

### Ejecutar Pruebas

```bash
# Desde el directorio raíz del proyecto
python -m pytest modules/servicios_sanitarios/tests/

# O desde el directorio del módulo
cd modules/servicios_sanitarios
python -m pytest tests/
```

## Roadmap

### Versión Actual (v0.1.0 - PoC)
- [x] Estructura básica del módulo
- [ ] Implementación de funcionalidad core
- [ ] Pruebas unitarias básicas
- [ ] Documentación de API

### Versión Futura
- [ ] Evaluar migración a lenguaje moderno (Rust, Go, TypeScript, etc.)
- [ ] Implementar funcionalidades avanzadas
- [ ] Integración con otros módulos de Concierge
- [ ] API REST para exposición de servicios

## Contribución

Este es un proyecto privado en desarrollo. Las contribuciones se manejan internamente.

## Licencia

Ver [LICENSE](../../LICENSE) en el directorio raíz del proyecto.

## Notas Técnicas

### Decisiones de Diseño

1. **Python como PoC**: Se eligió Python para el prototipo inicial por su rapidez de desarrollo y facilidad para validar conceptos
2. **Arquitectura modular**: Cada componente está separado para facilitar el mantenimiento y la evolución
3. **Testing desde el inicio**: Se incluye infraestructura de testing para asegurar calidad desde la primera versión

### Consideraciones Futuras

- Evaluar lenguajes compilados para mejor rendimiento
- Considerar containerización (Docker) para deployment
- Analizar necesidades de persistencia de datos
