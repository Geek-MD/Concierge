package servicios_sanitarios

import (
	"fmt"
	"time"
)

// Tarea representa una tarea en el sistema
type Tarea struct {
	ID              string                 `json:"id"`
	Descripcion     string                 `json:"descripcion"`
	Prioridad       string                 `json:"prioridad"`
	Estado          string                 `json:"estado"`
	FechaCreacion   time.Time              `json:"fecha_creacion"`
	FechaCompletado *time.Time             `json:"fecha_completado,omitempty"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// ServiciosSanitarios es la clase principal para el manejo de servicios sanitarios
type ServiciosSanitarios struct {
	Nombre        string    `json:"nombre"`
	ID            string    `json:"id"`
	FechaCreacion time.Time `json:"fecha_creacion"`
	Tareas        []Tarea   `json:"tareas"`
	activo        bool
}

// NewServiciosSanitarios crea una nueva instancia de ServiciosSanitarios
func NewServiciosSanitarios(nombre string) *ServiciosSanitarios {
	if nombre == "" {
		nombre = "ServiciosSanitarios"
	}
	return &ServiciosSanitarios{
		Nombre:        nombre,
		ID:            GenerateID(),
		FechaCreacion: time.Now(),
		Tareas:        []Tarea{},
		activo:        true,
	}
}

// AgregarTarea agrega una nueva tarea al sistema
func (s *ServiciosSanitarios) AgregarTarea(descripcion, prioridad string, metadata map[string]interface{}) (*Tarea, error) {
	if prioridad == "" {
		prioridad = "media"
	}

	if !ValidarPrioridad(prioridad) {
		return nil, fmt.Errorf("prioridad debe ser una de: baja, media, alta, critica")
	}

	if metadata == nil {
		metadata = make(map[string]interface{})
	}

	tarea := Tarea{
		ID:              GenerateID(),
		Descripcion:     descripcion,
		Prioridad:       prioridad,
		Estado:          "pendiente",
		FechaCreacion:   time.Now(),
		FechaCompletado: nil,
		Metadata:        metadata,
	}

	s.Tareas = append(s.Tareas, tarea)
	return &tarea, nil
}

// ListarTareas lista las tareas registradas, opcionalmente filtradas
func (s *ServiciosSanitarios) ListarTareas(filtroEstado, filtroPrioridad string) []Tarea {
	var tareasFiltradas []Tarea

	for _, tarea := range s.Tareas {
		if filtroEstado != "" && tarea.Estado != filtroEstado {
			continue
		}
		if filtroPrioridad != "" && tarea.Prioridad != filtroPrioridad {
			continue
		}
		tareasFiltradas = append(tareasFiltradas, tarea)
	}

	return tareasFiltradas
}

// CompletarTarea marca una tarea como completada
func (s *ServiciosSanitarios) CompletarTarea(tareaID string) bool {
	for i := range s.Tareas {
		if s.Tareas[i].ID == tareaID {
			s.Tareas[i].Estado = "completado"
			now := time.Now()
			s.Tareas[i].FechaCompletado = &now
			return true
		}
	}
	return false
}

// PorPrioridad representa el conteo de tareas por prioridad
type PorPrioridad struct {
	Baja    int `json:"baja"`
	Media   int `json:"media"`
	Alta    int `json:"alta"`
	Critica int `json:"critica"`
}

// Estadisticas representa las estadísticas del módulo
type Estadisticas struct {
	Total               int          `json:"total"`
	Pendientes          int          `json:"pendientes"`
	Completadas         int          `json:"completadas"`
	PorPrioridad        PorPrioridad `json:"por_prioridad"`
	ModuloActivo        bool         `json:"modulo_activo"`
	FechaCreacionModulo string       `json:"fecha_creacion_modulo"`
}

// ObtenerEstadisticas obtiene estadísticas sobre las tareas del módulo
func (s *ServiciosSanitarios) ObtenerEstadisticas() Estadisticas {
	stats := Estadisticas{
		Total:               len(s.Tareas),
		Pendientes:          0,
		Completadas:         0,
		ModuloActivo:        s.activo,
		FechaCreacionModulo: FormatTimestamp(s.FechaCreacion),
		PorPrioridad: PorPrioridad{
			Baja:    0,
			Media:   0,
			Alta:    0,
			Critica: 0,
		},
	}

	for _, tarea := range s.Tareas {
		if tarea.Estado == "pendiente" {
			stats.Pendientes++
		} else if tarea.Estado == "completado" {
			stats.Completadas++
		}

		switch tarea.Prioridad {
		case "baja":
			stats.PorPrioridad.Baja++
		case "media":
			stats.PorPrioridad.Media++
		case "alta":
			stats.PorPrioridad.Alta++
		case "critica":
			stats.PorPrioridad.Critica++
		}
	}

	return stats
}

// Info representa la información del módulo
type Info struct {
	Nombre        string `json:"nombre"`
	ID            string `json:"id"`
	FechaCreacion string `json:"fecha_creacion"`
	Activo        bool   `json:"activo"`
	TotalTareas   int    `json:"total_tareas"`
}

// ObtenerInfo obtiene información general del módulo
func (s *ServiciosSanitarios) ObtenerInfo() Info {
	return Info{
		Nombre:        s.Nombre,
		ID:            s.ID,
		FechaCreacion: FormatTimestamp(s.FechaCreacion),
		Activo:        s.activo,
		TotalTareas:   len(s.Tareas),
	}
}

// Activar activa el módulo
func (s *ServiciosSanitarios) Activar() {
	s.activo = true
}

// Desactivar desactiva el módulo
func (s *ServiciosSanitarios) Desactivar() {
	s.activo = false
}

// EstaActivo verifica si el módulo está activo
func (s *ServiciosSanitarios) EstaActivo() bool {
	return s.activo
}

// EntradaHistorial representa una entrada en el historial de cambios
type EntradaHistorial struct {
	URLFinal           string `json:"url_final"`
	URLTarifasVigentes string `json:"url_tarifas_vigentes"`
	Timestamp          string `json:"timestamp"`
}

// DatosVerificacionSISS representa los datos guardados de verificación SISS
type DatosVerificacionSISS struct {
	URLOriginal        string             `json:"url_original"`
	URLFinal           string             `json:"url_final"`
	URLTarifasVigentes string             `json:"url_tarifas_vigentes"`
	Timestamp          string             `json:"timestamp"`
	Verificado         bool               `json:"verificado"`
	Historial          []EntradaHistorial `json:"historial"`
}

// ResultadoVerificacionSISS representa el resultado de una verificación SISS
type ResultadoVerificacionSISS struct {
	Exito              bool            `json:"exito"`
	URLOriginal        string          `json:"url_original"`
	URLFinal           string          `json:"url_final,omitempty"`
	URLTarifasVigentes string          `json:"url_tarifas_vigentes,omitempty"`
	Timestamp          string          `json:"timestamp"`
	Archivo            string          `json:"archivo,omitempty"`
	Guardado           bool            `json:"guardado"`
	EsPrimeraVez       bool            `json:"es_primera_vez"`
	Cambios            map[string]bool `json:"cambios,omitempty"`
	Mensaje            string          `json:"mensaje"`
	Error              string          `json:"error,omitempty"`
}

// VerificarSISS verifica la URL de redirección de la web de SISS y la guarda en JSON
func (s *ServiciosSanitarios) VerificarSISS(rutaSalida string) ResultadoVerificacionSISS {
	if rutaSalida == "" {
		rutaSalida = "data/siss_url.json"
	}

	urlSISS := "https://www.siss.gob.cl"
	timestamp := time.Now()

	// Verificar redirección
	urlFinal, err := VerificarRedireccionURL(urlSISS, 10)
	if err != nil {
		return ResultadoVerificacionSISS{
			Exito:       false,
			URLOriginal: urlSISS,
			Timestamp:   FormatTimestamp(timestamp),
			Error:       fmt.Sprintf("No se pudo obtener la URL de redirección: %v", err),
		}
	}

	// Extraer URL de "Tarifas vigentes"
	urlTarifas, err := ExtraerURLPorTexto(urlFinal, "Tarifas vigentes", 10)
	if err != nil {
		// No es un error fatal, continuamos sin la URL de tarifas
		urlTarifas = ""
	}

	// Cargar datos previos si existen
	var datosPrevios DatosVerificacionSISS
	errCarga := CargarJSON(rutaSalida, &datosPrevios)
	esPrimeraVez := errCarga != nil

	// Verificar si hay cambios
	urlFinalCambio := false
	urlTarifasCambio := false

	if !esPrimeraVez {
		urlFinalCambio = datosPrevios.URLFinal != urlFinal
		urlTarifasCambio = datosPrevios.URLTarifasVigentes != urlTarifas
	}

	hayCambios := esPrimeraVez || urlFinalCambio || urlTarifasCambio

	// Solo guardar si hay cambios
	guardado := false
	if hayCambios {
		// Preparar historial
		historial := []EntradaHistorial{}
		if !esPrimeraVez && datosPrevios.Historial != nil {
			historial = datosPrevios.Historial
		}

		// Agregar entrada actual al historial si no es la primera vez
		if !esPrimeraVez {
			entradaHistorial := EntradaHistorial{
				URLFinal:           datosPrevios.URLFinal,
				URLTarifasVigentes: datosPrevios.URLTarifasVigentes,
				Timestamp:          datosPrevios.Timestamp,
			}
			historial = append(historial, entradaHistorial)
		}

		// Preparar datos para guardar
		datos := DatosVerificacionSISS{
			URLOriginal:        urlSISS,
			URLFinal:           urlFinal,
			URLTarifasVigentes: urlTarifas,
			Timestamp:          FormatTimestamp(timestamp),
			Verificado:         true,
			Historial:          historial,
		}

		// Guardar en JSON
		if err := GuardarJSON(datos, rutaSalida); err == nil {
			guardado = true
		}
	}

	mensaje := "Sin cambios, no se guardó"
	if esPrimeraVez {
		mensaje = "Primera verificación guardada"
	} else if hayCambios {
		mensaje = "Cambios detectados y guardados"
	}

	return ResultadoVerificacionSISS{
		Exito:              true,
		URLOriginal:        urlSISS,
		URLFinal:           urlFinal,
		URLTarifasVigentes: urlTarifas,
		Timestamp:          FormatTimestamp(timestamp),
		Archivo:            rutaSalida,
		Guardado:           guardado,
		EsPrimeraVez:       esPrimeraVez,
		Cambios: map[string]bool{
			"url_final":            urlFinalCambio,
			"url_tarifas_vigentes": urlTarifasCambio,
		},
		Mensaje: mensaje,
	}
}
