"""
Snap Seed Reconciliation and Purge Utility

Este script automatiza la deasignación de almacenamiento de bloque consumido por
binarios de paquetes snap en el directorio seed (`/var/lib/snapd/seed/snaps`) 
que ya no se encuentran instalados en el runtime del sistema.

Arquitectura:
El demonio `snapd` utiliza el directorio seed para inicializar el estado del 
sistema. Modificar este directorio invalida la paridad de instalación OEM y 
puede afectar las rutinas de recuperación del sistema (`snap unseed`).

Operaciones:
1. Consulta el estado activo del demonio (paquetes instalados).
2. Parsea el manifiesto inmutable (`seed.yaml`).
3. Calcula la diferencia de conjuntos para identificar binarios huérfanos.
4. Detiene el servicio `snapd.seeded.service`.
5. Elimina los binarios físicos huérfanos (.snap).
6. Reescribe la estructura de metadatos YAML.
7. Reinicia el servicio `snapd.seeded.service`.

Uso:
    Ejecución estándar:
        sudo ./purge_seed.py

    Ejecución simulada (sin mutación de estado):
        sudo ./purge_seed.py --dry-run

Dependencias:
    - python3-yaml (Instalación: `sudo apt install python3-yaml`)
"""

import subprocess
import yaml
import os
import sys
import argparse

# Rutas de directorio del demonio core
SEED_DIR = "/var/lib/snapd/seed/"
YAML_PATH = os.path.join(SEED_DIR, "seed.yaml")
SNAPS_DIR = os.path.join(SEED_DIR, "snaps")


def parse_arguments():
    """Configura y procesa los argumentos de la interfaz de línea de comandos."""
    parser = argparse.ArgumentParser(description="Purga paquetes snap huérfanos del directorio seed.")
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help="Simula el proceso de purga sin ejecutar modificaciones en el sistema de archivos ni en el estado del demonio."
    )
    return parser.parse_args()


def execute_subprocess(command):
    """Ejecuta un comando de shell y retorna la salida estándar."""
    try:
        return subprocess.check_output(command, shell=True, text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"Error de subproceso al ejecutar '{command}': {e}")
        sys.exit(1)


def query_installed_snaps():
    """Consulta el demonio snapd para obtener instalaciones activas y deshabilitadas."""
    output = execute_subprocess("snap list | awk 'NR>1 {print $1}'")
    return set(output.split('\n'))


def main():
    args = parse_arguments()

    if os.geteuid() != 0:
        print("FATAL: Se requiere escalada de privilegios. Ejecute mediante sudo.")
        sys.exit(1)

    print("Parseando manifiesto seed...")
    try:
        with open(YAML_PATH, 'r') as file:
            seed_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"FATAL: No se encontró el manifiesto seed en {YAML_PATH}")
        sys.exit(1)

    installed_snaps = query_installed_snaps()
    seeded_snaps = seed_data.get('snaps', [])
    
    # Computar binarios huérfanos
    orphaned_snaps = [s for s in seeded_snaps if s['name'] not in installed_snaps]
    
    if not orphaned_snaps:
        print("Estado sincronizado. No se detectaron snaps huérfanos en el seed.")
        sys.exit(0)

    print(f"Se detectaron {len(orphaned_snaps)} paquetes huérfanos.")

    if args.dry_run:
        print("\n[DRY-RUN] Iniciando ejecución simulada...")
        print("[DRY-RUN] Omitiendo: systemctl stop snapd.seeded.service")
    else:
        print("Deteniendo snapd.seeded.service...")
        execute_subprocess("systemctl stop snapd.seeded.service")

    valid_snaps = []
    bytes_freed = 0

    for snap_info in seeded_snaps:
        name = snap_info['name']
        if name in installed_snaps:
            valid_snaps.append(snap_info)
        else:
            filename = snap_info.get('file')
            filepath = os.path.join(SNAPS_DIR, filename)
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if args.dry_run:
                    print(f"[DRY-RUN] Se eliminaría el binario: {filepath} ({file_size / (1024*1024):.2f} MB)")
                else:
                    print(f"Deasignando almacenamiento del binario: {filepath}")
                    os.remove(filepath)
                bytes_freed += file_size
            else:
                print(f"WARN: Binario no encontrado en almacenamiento de bloque: {filepath}")

    # Reconstruir estructura de metadatos
    seed_data['snaps'] = valid_snaps

    if args.dry_run:
        print(f"[DRY-RUN] Se reescribiría el manifiesto: {YAML_PATH} (Nuevas entradas: {len(valid_snaps)})")
        print("[DRY-RUN] Omitiendo: systemctl start snapd.seeded.service")
    else:
        print(f"Haciendo commit de las modificaciones al manifiesto: {YAML_PATH}")
        with open(YAML_PATH, 'w') as file:
            yaml.dump(seed_data, file, default_flow_style=False)

        print("Reinicializando snapd.seeded.service...")
        execute_subprocess("systemctl start snapd.seeded.service")
    
    print(f"\nEjecución completada. Almacenamiento total {'que sería ' if args.dry_run else ''}liberado: {bytes_freed / (1024*1024):.2f} MB.")

if __name__ == "__main__":
    main()