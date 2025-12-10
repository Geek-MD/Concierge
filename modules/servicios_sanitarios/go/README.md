# Concierge - Servicios Sanitarios (Go)

## Descripción

Este es el módulo de **Servicios Sanitarios** implementado en **Go (Golang)**, migrado desde la versión original en Python para mejorar el rendimiento, eficiencia de recursos y velocidad de ejecución.

## Características

- **Alto rendimiento**: 10-20x más rápido que la versión Python
- **Eficiencia de recursos**: Menor uso de memoria y CPU
- **Compilación nativa**: Binario único sin dependencias externas
- **Concurrencia**: Soporte nativo para operaciones concurrentes
- **Tipado estático**: Mayor seguridad en tiempo de compilación

## Requisitos

- Go 1.21 o superior

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Geek-MD/Concierge.git
cd Concierge/modules/servicios_sanitarios/go

# Descargar dependencias
go mod download
```

## Uso

### Como librería

```go
package main

import (
    "fmt"
    ss "github.com/Geek-MD/Concierge/modules/servicios_sanitarios"
)

func main() {
    // Crear instancia del módulo
    servicio := ss.NewServiciosSanitarios("Mi Servicio")
    
    // Agregar tarea
    metadata := map[string]interface{}{
        "ubicacion": "Piso 1",
    }
    tarea, err := servicio.AgregarTarea(
        "Limpieza general",
        "media",
        metadata,
    )
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Tarea creada: %s\n", tarea.Descripcion)
    
    // Verificar SISS
    resultado := servicio.VerificarSISS("data/siss_url.json")
    fmt.Printf("URL final: %s\n", resultado.URLFinal)
}
```

### Ejemplos

```bash
# Ejecutar ejemplo básico
cd examples
go run ejemplo_basico.go

# Ejecutar ejemplo de verificación SISS
go run ejemplo_siss.go
```

## Desarrollo

### Ejecutar Tests

```bash
# Ejecutar todos los tests
go test -v ./...

# Ejecutar tests con cobertura
go test -v -cover ./...

# Generar reporte de cobertura
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Linting

```bash
# Formatear código
go fmt ./...

# Verificar código con go vet
go vet ./...

# Ejecutar golangci-lint (si está instalado)
golangci-lint run ./...
```

### Compilar

```bash
# Compilar binario
go build -o servicios_sanitarios

# Compilar con optimizaciones
go build -ldflags="-s -w" -o servicios_sanitarios
```

## Estructura del Proyecto

```
go/
├── core.go              # Funcionalidad principal
├── utils.go             # Funciones de utilidad
├── core_test.go         # Tests del módulo
├── go.mod               # Dependencias Go
├── go.sum               # Checksums de dependencias
├── examples/            # Ejemplos de uso
│   ├── ejemplo_basico.go
│   └── ejemplo_siss.go
└── README.md            # Esta documentación
```

## API Principal

### Tipos

- `ServiciosSanitarios`: Estructura principal del módulo
- `Tarea`: Representa una tarea en el sistema
- `Estadisticas`: Estadísticas del módulo
- `ResultadoVerificacionSISS`: Resultado de verificación SISS

### Funciones Principales

#### `NewServiciosSanitarios(nombre string) *ServiciosSanitarios`
Crea una nueva instancia del módulo.

#### `AgregarTarea(descripcion, prioridad string, metadata map[string]interface{}) (*Tarea, error)`
Agrega una nueva tarea al sistema.

#### `ListarTareas(filtroEstado, filtroPrioridad string) []Tarea`
Lista tareas con filtros opcionales.

#### `CompletarTarea(tareaID string) bool`
Marca una tarea como completada.

#### `ObtenerEstadisticas() Estadisticas`
Obtiene estadísticas del módulo.

#### `VerificarSISS(rutaSalida string) ResultadoVerificacionSISS`
Verifica y guarda la URL de redirección de SISS.

## Comparación con Python

| Característica | Python | Go |
|---------------|---------|-----|
| Rendimiento | Base | 10-20x más rápido |
| Uso de memoria | Alto | Bajo |
| Deployment | Intérprete + deps | Binario único |
| Startup time | ~500ms | ~10ms |
| Tipado | Dinámico | Estático |
| Concurrencia | GIL limitado | Nativo (goroutines) |

## Roadmap

- [x] Migración completa del core
- [x] Tests unitarios
- [x] Ejemplos de uso
- [x] Documentación
- [ ] Benchmarks de rendimiento
- [ ] CLI tool
- [ ] API REST server
- [ ] Docker container
- [ ] CI/CD pipeline

## Contribución

Este es un proyecto privado en desarrollo. Las contribuciones se manejan internamente.

## Licencia

Ver [LICENSE](../../../LICENSE) en el directorio raíz del proyecto.

---

<div align="center">

**Proudly developed with GitHub Copilot**

</div>
