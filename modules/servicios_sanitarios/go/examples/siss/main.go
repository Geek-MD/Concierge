package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	ss "github.com/Geek-MD/Concierge/modules/servicios_sanitarios"
)

func main() {
	fmt.Println("=" + repetir("=", 69))
	fmt.Println("Concierge - Verificación SISS (Go)")
	fmt.Println("=" + repetir("=", 69))
	fmt.Println()

	// Crear instancia del módulo
	fmt.Println("1. Creando módulo de servicios sanitarios...")
	servicio := ss.NewServiciosSanitarios("Verificador SISS")
	fmt.Printf("   ✓ Módulo creado: %s\n", servicio.ObtenerInfo().Nombre)
	fmt.Println()

	// Verificar SISS
	fmt.Println("2. Verificando URL de SISS...")
	fmt.Println("   URL a verificar: https://www.siss.gob.cl")
	fmt.Println("   • Detectando redirección...")
	fmt.Println("   • Extrayendo URL de 'Tarifas vigentes'...")
	fmt.Println()

	resultado := servicio.VerificarSISS("data/siss_url.json")

	if resultado.Exito {
		fmt.Println("   ✓ Verificación exitosa!")
		fmt.Printf("   • URL Original: %s\n", resultado.URLOriginal)
		fmt.Printf("   • URL Final: %s\n", resultado.URLFinal)
		if resultado.URLTarifasVigentes != "" {
			fmt.Printf("   • URL Tarifas Vigentes: %s\n", resultado.URLTarifasVigentes)
		}
		fmt.Printf("   • Timestamp: %s\n", resultado.Timestamp)
		fmt.Printf("   • Archivo: %s\n", resultado.Archivo)
		fmt.Printf("   • Estado: %s\n", resultado.Mensaje)
		
		if resultado.Guardado {
			fmt.Println("   • ✓ Datos guardados exitosamente")
			if resultado.EsPrimeraVez {
				fmt.Println("   • Esta es la primera verificación")
			} else {
				if resultado.Cambios["url_final"] {
					fmt.Println("   • ⚠ La URL final cambió")
				}
				if resultado.Cambios["url_tarifas_vigentes"] {
					fmt.Println("   • ⚠ La URL de Tarifas vigentes cambió")
				}
			}
		} else {
			fmt.Println("   • ℹ No se guardaron cambios (URLs sin modificar)")
		}
	} else {
		fmt.Println("   ✗ Error en la verificación")
		fmt.Printf("   • Error: %s\n", resultado.Error)
	}
	fmt.Println()

	// Leer el archivo JSON guardado
	if resultado.Exito && resultado.Guardado {
		fmt.Println("3. Leyendo datos guardados del archivo JSON...")
		var datos ss.DatosVerificacionSISS
		if err := ss.CargarJSON("data/siss_url.json", &datos); err == nil {
			fmt.Println("   ✓ Archivo cargado correctamente:")
			fmt.Printf("   • URL Original: %s\n", datos.URLOriginal)
			fmt.Printf("   • URL Final: %s\n", datos.URLFinal)
			if datos.URLTarifasVigentes != "" {
				fmt.Printf("   • URL Tarifas Vigentes: %s\n", datos.URLTarifasVigentes)
			}
			fmt.Printf("   • Timestamp: %s\n", datos.Timestamp)
			fmt.Printf("   • Verificado: %v\n", datos.Verificado)
			if len(datos.Historial) > 0 {
				fmt.Printf("   • Historial de cambios: %d entrada(s)\n", len(datos.Historial))
			}
			
			// Mostrar el JSON completo formateado
			fmt.Println()
			fmt.Println("   JSON guardado:")
			jsonData, err := json.MarshalIndent(datos, "   ", "  ")
			if err != nil {
				log.Printf("   Error al formatear JSON: %v\n", err)
			} else {
				fmt.Println(string(jsonData))
			}
		} else {
			fmt.Printf("   ✗ No se pudo leer el archivo: %v\n", err)
		}
		fmt.Println()
	}

	fmt.Println("=" + repetir("=", 69))
	fmt.Println("Demo completada")
	fmt.Println("=" + repetir("=", 69))
	fmt.Println()
	fmt.Println("Nota: Ejecuta este programa múltiples veces para ver cómo")
	fmt.Println("      solo guarda cuando hay cambios en las URLs.")
}

func repetir(s string, n int) string {
	return strings.Repeat(s, n)
}
