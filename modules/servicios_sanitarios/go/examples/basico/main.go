package main

import (
	"fmt"
	"log"
	"strings"

	ss "github.com/Geek-MD/Concierge/modules/servicios_sanitarios"
)

func main() {
	fmt.Println("=" + repetir("=", 59))
	fmt.Println("Concierge - Servicios Sanitarios - Ejemplo de Uso (Go)")
	fmt.Println("=" + repetir("=", 59))
	fmt.Println()

	// Crear instancia del módulo
	fmt.Println("1. Creando módulo de servicios sanitarios...")
	servicio := ss.NewServiciosSanitarios("Servicio Demo")
	info := servicio.ObtenerInfo()
	fmt.Printf("   ✓ Módulo creado: %s\n", info.Nombre)
	fmt.Printf("   ✓ ID: %s\n", info.ID)
	fmt.Println()

	// Agregar tareas
	fmt.Println("2. Agregando tareas...")
	metadata1 := map[string]interface{}{
		"ubicacion":        "Planta baja",
		"tiempo_estimado":  "30min",
	}
	tarea1, err := servicio.AgregarTarea(
		"Limpieza general del área común",
		"media",
		metadata1,
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("   ✓ Tarea 1: %s (Prioridad: %s)\n", tarea1.Descripcion, tarea1.Prioridad)

	metadata2 := map[string]interface{}{
		"ubicacion": "Piso 2",
		"urgente":   true,
	}
	tarea2, err := servicio.AgregarTarea(
		"Revisión urgente de fugas en baño principal",
		"critica",
		metadata2,
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("   ✓ Tarea 2: %s (Prioridad: %s)\n", tarea2.Descripcion, tarea2.Prioridad)

	tarea3, err := servicio.AgregarTarea(
		"Reposición de suministros de limpieza",
		"baja",
		nil,
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("   ✓ Tarea 3: %s (Prioridad: %s)\n", tarea3.Descripcion, tarea3.Prioridad)
	fmt.Println()

	// Listar tareas
	fmt.Println("3. Listando todas las tareas...")
	tareas := servicio.ListarTareas("", "")
	fmt.Printf("   Total de tareas: %d\n", len(tareas))
	fmt.Println()

	// Filtrar por prioridad
	fmt.Println("4. Filtrando tareas críticas...")
	criticas := servicio.ListarTareas("", "critica")
	for _, tarea := range criticas {
		fmt.Printf("   - %s\n", tarea.Descripcion)
	}
	fmt.Println()

	// Completar una tarea
	fmt.Println("5. Completando tarea...")
	resultado := servicio.CompletarTarea(tarea1.ID)
	if resultado {
		fmt.Printf("   ✓ Tarea completada: %s\n", tarea1.Descripcion)
	}
	fmt.Println()

	// Obtener estadísticas
	fmt.Println("6. Estadísticas del módulo:")
	stats := servicio.ObtenerEstadisticas()
	fmt.Printf("   Total de tareas: %d\n", stats.Total)
	fmt.Printf("   Pendientes: %d\n", stats.Pendientes)
	fmt.Printf("   Completadas: %d\n", stats.Completadas)
	fmt.Println("   Por prioridad:")
	if stats.PorPrioridad.Baja > 0 {
		fmt.Printf("     - Baja: %d\n", stats.PorPrioridad.Baja)
	}
	if stats.PorPrioridad.Media > 0 {
		fmt.Printf("     - Media: %d\n", stats.PorPrioridad.Media)
	}
	if stats.PorPrioridad.Alta > 0 {
		fmt.Printf("     - Alta: %d\n", stats.PorPrioridad.Alta)
	}
	if stats.PorPrioridad.Critica > 0 {
		fmt.Printf("     - Crítica: %d\n", stats.PorPrioridad.Critica)
	}
	fmt.Println()

	// Estado del módulo
	fmt.Println("7. Estado del módulo:")
	activo := "No"
	if servicio.EstaActivo() {
		activo = "Sí"
	}
	fmt.Printf("   Activo: %s\n", activo)
	fmt.Println()

	fmt.Println("=" + repetir("=", 59))
	fmt.Println("Demo completada exitosamente")
	fmt.Println("=" + repetir("=", 59))
}

func repetir(s string, n int) string {
	return strings.Repeat(s, n)
}
