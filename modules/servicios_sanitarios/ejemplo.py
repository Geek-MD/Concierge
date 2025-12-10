#!/usr/bin/env python3
"""
Ejemplo de uso del módulo Servicios Sanitarios.

Este script demuestra las funcionalidades básicas del módulo.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios


def main():
    """Función principal del ejemplo."""
    print("=" * 60)
    print("Concierge - Servicios Sanitarios - Ejemplo de Uso")
    print("=" * 60)
    print()
    
    # Crear instancia del módulo
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Servicio Demo")
    info = servicio.obtener_info()
    print(f"   ✓ Módulo creado: {info['nombre']}")
    print(f"   ✓ ID: {info['id']}")
    print()
    
    # Agregar tareas
    print("2. Agregando tareas...")
    tarea1 = servicio.agregar_tarea(
        "Limpieza general del área común",
        prioridad="media",
        metadata={"ubicacion": "Planta baja", "tiempo_estimado": "30min"}
    )
    print(f"   ✓ Tarea 1: {tarea1['descripcion']} (Prioridad: {tarea1['prioridad']})")
    
    tarea2 = servicio.agregar_tarea(
        "Revisión urgente de fugas en baño principal",
        prioridad="critica",
        metadata={"ubicacion": "Piso 2", "urgente": True}
    )
    print(f"   ✓ Tarea 2: {tarea2['descripcion']} (Prioridad: {tarea2['prioridad']})")
    
    tarea3 = servicio.agregar_tarea(
        "Reposición de suministros de limpieza",
        prioridad="baja"
    )
    print(f"   ✓ Tarea 3: {tarea3['descripcion']} (Prioridad: {tarea3['prioridad']})")
    print()
    
    # Listar tareas
    print("3. Listando todas las tareas...")
    tareas = servicio.listar_tareas()
    print(f"   Total de tareas: {len(tareas)}")
    print()
    
    # Filtrar por prioridad
    print("4. Filtrando tareas críticas...")
    criticas = servicio.listar_tareas(filtro_prioridad="critica")
    for tarea in criticas:
        print(f"   - {tarea['descripcion']}")
    print()
    
    # Completar una tarea
    print("5. Completando tarea...")
    resultado = servicio.completar_tarea(tarea1['id'])
    if resultado:
        print(f"   ✓ Tarea completada: {tarea1['descripcion']}")
    print()
    
    # Obtener estadísticas
    print("6. Estadísticas del módulo:")
    stats = servicio.obtener_estadisticas()
    print(f"   Total de tareas: {stats['total']}")
    print(f"   Pendientes: {stats['pendientes']}")
    print(f"   Completadas: {stats['completadas']}")
    print(f"   Por prioridad:")
    for prioridad, cantidad in stats['por_prioridad'].items():
        if cantidad > 0:
            print(f"     - {prioridad.capitalize()}: {cantidad}")
    print()
    
    # Estado del módulo
    print("7. Estado del módulo:")
    print(f"   Activo: {'Sí' if servicio.esta_activo() else 'No'}")
    print()
    
    print("=" * 60)
    print("Demo completada exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    main()
