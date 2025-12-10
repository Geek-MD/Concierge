package servicios_sanitarios

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
	"golang.org/x/net/html"
)

// GenerateID genera un ID único para identificar elementos del sistema
func GenerateID() string {
	return uuid.New().String()
}

// FormatTimestamp formatea un timestamp en formato ISO 8601
func FormatTimestamp(t time.Time) string {
	return t.Format(time.RFC3339)
}

// ValidarPrioridad valida que una prioridad sea válida
func ValidarPrioridad(prioridad string) bool {
	prioridades := []string{"baja", "media", "alta", "critica"}
	for _, p := range prioridades {
		if p == prioridad {
			return true
		}
	}
	return false
}

// ObtenerFechaActual obtiene la fecha y hora actuales
func ObtenerFechaActual() time.Time {
	return time.Now()
}

// FormatearDuracion calcula y formatea la duración entre dos fechas
func FormatearDuracion(inicio time.Time, fin *time.Time) string {
	finTime := time.Now()
	if fin != nil {
		finTime = *fin
	}

	duracion := finTime.Sub(inicio)
	dias := int(duracion.Hours() / 24)
	horas := int(duracion.Hours()) % 24
	minutos := int(duracion.Minutes()) % 60
	segundos := int(duracion.Seconds()) % 60

	var partes []string
	if dias > 0 {
		partes = append(partes, fmt.Sprintf("%dd", dias))
	}
	if horas > 0 {
		partes = append(partes, fmt.Sprintf("%dh", horas))
	}
	if minutos > 0 {
		partes = append(partes, fmt.Sprintf("%dm", minutos))
	}
	if segundos > 0 || len(partes) == 0 {
		partes = append(partes, fmt.Sprintf("%ds", segundos))
	}

	return strings.Join(partes, " ")
}

// VerificarRedireccionURL verifica la URL a la que redirecciona una página web
func VerificarRedireccionURL(url string, timeout int) (string, error) {
	client := &http.Client{
		Timeout: time.Duration(timeout) * time.Second,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return nil // Permitir redirecciones
		},
	}

	resp, err := client.Get(url)
	if err != nil {
		return "", fmt.Errorf("error al verificar redirección: %w", err)
	}
	defer resp.Body.Close()

	return resp.Request.URL.String(), nil
}

// GuardarJSON guarda datos en un archivo JSON
func GuardarJSON(datos interface{}, rutaArchivo string) error {
	// Crear directorios si no existen
	dir := filepath.Dir(rutaArchivo)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("error al crear directorios: %w", err)
	}

	// Convertir datos a JSON con indentación
	jsonData, err := json.MarshalIndent(datos, "", "  ")
	if err != nil {
		return fmt.Errorf("error al serializar JSON: %w", err)
	}

	// Escribir archivo
	if err := os.WriteFile(rutaArchivo, jsonData, 0644); err != nil {
		return fmt.Errorf("error al escribir archivo: %w", err)
	}

	return nil
}

// CargarJSON carga datos desde un archivo JSON
func CargarJSON(rutaArchivo string, datos interface{}) error {
	// Leer archivo
	file, err := os.ReadFile(rutaArchivo)
	if err != nil {
		return fmt.Errorf("error al leer archivo: %w", err)
	}

	// Deserializar JSON
	if err := json.Unmarshal(file, datos); err != nil {
		return fmt.Errorf("error al deserializar JSON: %w", err)
	}

	return nil
}

// ExtraerURLPorTexto extrae la URL de un enlace en una página HTML buscando por el texto del enlace
func ExtraerURLPorTexto(url, textoBuscar string, timeout int) (string, error) {
	client := &http.Client{
		Timeout: time.Duration(timeout) * time.Second,
	}

	resp, err := client.Get(url)
	if err != nil {
		return "", fmt.Errorf("error al obtener página: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("código de estado HTTP: %d", resp.StatusCode)
	}

	// Parsear HTML
	doc, err := html.Parse(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error al parsear HTML: %w", err)
	}

	// Buscar enlace recursivamente
	var resultado string
	var buscarEnlace func(*html.Node)
	buscarEnlace = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "a" {
			// Obtener el texto del enlace
			var textoEnlace string
			var obtenerTexto func(*html.Node)
			obtenerTexto = func(node *html.Node) {
				if node.Type == html.TextNode {
					textoEnlace += node.Data
				}
				for c := node.FirstChild; c != nil; c = c.NextSibling {
					obtenerTexto(c)
				}
			}
			obtenerTexto(n)

			// Verificar si contiene el texto buscado (case insensitive)
			if strings.Contains(strings.ToLower(textoEnlace), strings.ToLower(textoBuscar)) {
				// Obtener el atributo href
				for _, attr := range n.Attr {
					if attr.Key == "href" {
						resultado = resolverURLAbsoluta(url, attr.Val)
						return
					}
				}
			}
		}

		// Continuar búsqueda recursiva
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			if resultado != "" {
				return
			}
			buscarEnlace(c)
		}
	}

	buscarEnlace(doc)

	if resultado == "" {
		return "", fmt.Errorf("no se encontró enlace con el texto: %s", textoBuscar)
	}

	return resultado, nil
}

// resolverURLAbsoluta convierte una URL relativa en absoluta
func resolverURLAbsoluta(baseURL, href string) string {
	// Si ya es absoluta, retornarla
	if strings.HasPrefix(href, "http://") || strings.HasPrefix(href, "https://") {
		return href
	}

	// Si comienza con /, es relativa a la raíz del dominio
	if strings.HasPrefix(href, "/") {
		// Extraer el dominio base
		parts := strings.Split(baseURL, "/")
		if len(parts) >= 3 {
			return parts[0] + "//" + parts[2] + href
		}
	}

	// Caso relativo al path actual
	lastSlash := strings.LastIndex(baseURL, "/")
	if lastSlash != -1 {
		return baseURL[:lastSlash+1] + href
	}

	return baseURL + "/" + href
}
