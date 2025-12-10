package servicios_sanitarios

import (
	"testing"
	"time"
)

func TestNewServiciosSanitarios(t *testing.T) {
	servicio := NewServiciosSanitarios("")

	if servicio.Nombre != "ServiciosSanitarios" {
		t.Errorf("Nombre esperado 'ServiciosSanitarios', obtenido '%s'", servicio.Nombre)
	}

	if servicio.ID == "" {
		t.Error("ID no debe estar vacío")
	}

	if len(servicio.Tareas) != 0 {
		t.Errorf("Tareas debe estar vacío, tiene %d elementos", len(servicio.Tareas))
	}

	if !servicio.EstaActivo() {
		t.Error("El módulo debe estar activo por defecto")
	}
}

func TestNewServiciosSanitariosConNombre(t *testing.T) {
	nombreCustom := "MiServicio"
	servicio := NewServiciosSanitarios(nombreCustom)

	if servicio.Nombre != nombreCustom {
		t.Errorf("Nombre esperado '%s', obtenido '%s'", nombreCustom, servicio.Nombre)
	}
}

func TestAgregarTareaBasica(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	tarea, err := servicio.AgregarTarea("Limpiar área común", "", nil)

	if err != nil {
		t.Fatalf("Error al agregar tarea: %v", err)
	}

	if tarea.Descripcion != "Limpiar área común" {
		t.Errorf("Descripción esperada 'Limpiar área común', obtenida '%s'", tarea.Descripcion)
	}

	if tarea.Prioridad != "media" {
		t.Errorf("Prioridad por defecto debe ser 'media', obtenida '%s'", tarea.Prioridad)
	}

	if tarea.Estado != "pendiente" {
		t.Errorf("Estado debe ser 'pendiente', obtenido '%s'", tarea.Estado)
	}

	if tarea.ID == "" {
		t.Error("ID de tarea no debe estar vacío")
	}

	if len(servicio.Tareas) != 1 {
		t.Errorf("Debe haber 1 tarea, hay %d", len(servicio.Tareas))
	}
}

func TestAgregarTareaConPrioridad(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	tarea, err := servicio.AgregarTarea("Emergencia sanitaria", "critica", nil)

	if err != nil {
		t.Fatalf("Error al agregar tarea: %v", err)
	}

	if tarea.Prioridad != "critica" {
		t.Errorf("Prioridad esperada 'critica', obtenida '%s'", tarea.Prioridad)
	}
}

func TestAgregarTareaPrioridadInvalida(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	_, err := servicio.AgregarTarea("Tarea", "urgentisima", nil)

	if err == nil {
		t.Error("Debe generar error con prioridad inválida")
	}
}

func TestAgregarTareaConMetadata(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	metadata := map[string]interface{}{
		"ubicacion":   "Piso 3",
		"responsable": "Juan",
	}

	tarea, err := servicio.AgregarTarea("Revisar sanitarios", "media", metadata)

	if err != nil {
		t.Fatalf("Error al agregar tarea: %v", err)
	}

	if tarea.Metadata["ubicacion"] != "Piso 3" {
		t.Errorf("Metadata ubicacion esperada 'Piso 3', obtenida '%v'", tarea.Metadata["ubicacion"])
	}
}

func TestListarTareas(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	servicio.AgregarTarea("Tarea 1", "", nil)
	servicio.AgregarTarea("Tarea 2", "", nil)
	servicio.AgregarTarea("Tarea 3", "", nil)

	tareas := servicio.ListarTareas("", "")

	if len(tareas) != 3 {
		t.Errorf("Debe haber 3 tareas, hay %d", len(tareas))
	}
}

func TestListarTareasPorEstado(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	tarea1, _ := servicio.AgregarTarea("Tarea 1", "", nil)
	servicio.AgregarTarea("Tarea 2", "", nil)
	servicio.CompletarTarea(tarea1.ID)

	pendientes := servicio.ListarTareas("pendiente", "")
	completadas := servicio.ListarTareas("completado", "")

	if len(pendientes) != 1 {
		t.Errorf("Debe haber 1 tarea pendiente, hay %d", len(pendientes))
	}

	if len(completadas) != 1 {
		t.Errorf("Debe haber 1 tarea completada, hay %d", len(completadas))
	}
}

func TestListarTareasPorPrioridad(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	servicio.AgregarTarea("Tarea baja", "baja", nil)
	servicio.AgregarTarea("Tarea alta", "alta", nil)
	servicio.AgregarTarea("Tarea alta 2", "alta", nil)

	altas := servicio.ListarTareas("", "alta")
	bajas := servicio.ListarTareas("", "baja")

	if len(altas) != 2 {
		t.Errorf("Debe haber 2 tareas altas, hay %d", len(altas))
	}

	if len(bajas) != 1 {
		t.Errorf("Debe haber 1 tarea baja, hay %d", len(bajas))
	}
}

func TestCompletarTarea(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	tarea, _ := servicio.AgregarTarea("Tarea a completar", "", nil)

	resultado := servicio.CompletarTarea(tarea.ID)

	if !resultado {
		t.Error("CompletarTarea debe retornar true")
	}

	// Buscar la tarea en el slice
	var tareaCompletada *Tarea
	for i := range servicio.Tareas {
		if servicio.Tareas[i].ID == tarea.ID {
			tareaCompletada = &servicio.Tareas[i]
			break
		}
	}

	if tareaCompletada == nil {
		t.Fatal("No se encontró la tarea completada")
	}

	if tareaCompletada.Estado != "completado" {
		t.Errorf("Estado debe ser 'completado', es '%s'", tareaCompletada.Estado)
	}

	if tareaCompletada.FechaCompletado == nil {
		t.Error("FechaCompletado no debe ser nil")
	}
}

func TestCompletarTareaInexistente(t *testing.T) {
	servicio := NewServiciosSanitarios("")

	resultado := servicio.CompletarTarea("id-inexistente")

	if resultado {
		t.Error("CompletarTarea con ID inexistente debe retornar false")
	}
}

func TestObtenerEstadisticas(t *testing.T) {
	servicio := NewServiciosSanitarios("")
	servicio.AgregarTarea("Tarea 1", "alta", nil)
	servicio.AgregarTarea("Tarea 2", "baja", nil)
	tarea3, _ := servicio.AgregarTarea("Tarea 3", "alta", nil)
	servicio.CompletarTarea(tarea3.ID)

	stats := servicio.ObtenerEstadisticas()

	if stats.Total != 3 {
		t.Errorf("Total debe ser 3, es %d", stats.Total)
	}

	if stats.Pendientes != 2 {
		t.Errorf("Pendientes debe ser 2, es %d", stats.Pendientes)
	}

	if stats.Completadas != 1 {
		t.Errorf("Completadas debe ser 1, es %d", stats.Completadas)
	}

	if stats.PorPrioridad.Alta != 2 {
		t.Errorf("Prioridad alta debe ser 2, es %d", stats.PorPrioridad.Alta)
	}

	if stats.PorPrioridad.Baja != 1 {
		t.Errorf("Prioridad baja debe ser 1, es %d", stats.PorPrioridad.Baja)
	}

	if !stats.ModuloActivo {
		t.Error("ModuloActivo debe ser true")
	}
}

func TestObtenerInfo(t *testing.T) {
	servicio := NewServiciosSanitarios("TestServicio")
	servicio.AgregarTarea("Tarea 1", "", nil)

	info := servicio.ObtenerInfo()

	if info.Nombre != "TestServicio" {
		t.Errorf("Nombre esperado 'TestServicio', obtenido '%s'", info.Nombre)
	}

	if info.ID == "" {
		t.Error("ID no debe estar vacío")
	}

	if !info.Activo {
		t.Error("Activo debe ser true")
	}

	if info.TotalTareas != 1 {
		t.Errorf("TotalTareas debe ser 1, es %d", info.TotalTareas)
	}
}

func TestActivarDesactivar(t *testing.T) {
	servicio := NewServiciosSanitarios("")

	if !servicio.EstaActivo() {
		t.Error("Debe estar activo por defecto")
	}

	servicio.Desactivar()
	if servicio.EstaActivo() {
		t.Error("Debe estar desactivado")
	}

	servicio.Activar()
	if !servicio.EstaActivo() {
		t.Error("Debe estar activo nuevamente")
	}
}

func TestGenerateID(t *testing.T) {
	id1 := GenerateID()
	id2 := GenerateID()

	if id1 == "" {
		t.Error("ID no debe estar vacío")
	}

	if id1 == id2 {
		t.Error("IDs deben ser únicos")
	}
}

func TestFormatTimestamp(t *testing.T) {
	now := time.Now()
	formatted := FormatTimestamp(now)

	if formatted == "" {
		t.Error("Timestamp formateado no debe estar vacío")
	}

	// Verificar que es un formato ISO 8601 válido
	_, err := time.Parse(time.RFC3339, formatted)
	if err != nil {
		t.Errorf("Timestamp no está en formato RFC3339: %v", err)
	}
}

func TestValidarPrioridad(t *testing.T) {
	tests := []struct {
		prioridad string
		esperado  bool
	}{
		{"baja", true},
		{"media", true},
		{"alta", true},
		{"critica", true},
		{"invalida", false},
		{"", false},
	}

	for _, test := range tests {
		resultado := ValidarPrioridad(test.prioridad)
		if resultado != test.esperado {
			t.Errorf("ValidarPrioridad('%s') = %v, esperado %v", test.prioridad, resultado, test.esperado)
		}
	}
}
