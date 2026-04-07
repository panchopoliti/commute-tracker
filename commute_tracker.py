#!/usr/bin/env python3
"""
Commute Tracker - Consulta Google Maps Routes API cada ejecución
y guarda el tiempo de viaje con tráfico en un CSV.
"""

import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from zoneinfo import ZoneInfo

# Configuración
TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
CSV_FILE = Path(__file__).parent / "commute_data.csv"

ORIGIN = "Asia 2055, Belén de Escobar, Provincia de Buenos Aires"
DESTINATION = "Almarena Puerto Retiro, Mayor Arturo Luisoni 2510, C1104, Buenos Aires"

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

CSV_HEADERS = [
    "timestamp",
    "day_of_week",
    "hour",
    "direction",
    "duration_seconds",
    "duration_in_traffic_seconds",
    "distance_meters",
]

DAYS_ES = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}


def get_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        print("ERROR: Variable de entorno GOOGLE_MAPS_API_KEY no configurada")
        sys.exit(1)
    return key


def parse_duration(duration_str: str) -> int:
    """Parsea duración de la Routes API (ej: '1234s') a segundos."""
    return int(duration_str.rstrip("s"))


def query_routes(api_key: str, origin: str, destination: str) -> dict:
    """Consulta la Routes API (nueva) con tráfico en tiempo real."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters",
    }
    body = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
    }

    resp = requests.post(ROUTES_URL, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"API error: {data['error'].get('message', data['error'])}")

    if not data.get("routes"):
        raise RuntimeError(f"No se encontraron rutas. Respuesta: {data}")

    route = data["routes"][0]
    return {
        "duration_seconds": parse_duration(route["staticDuration"]),
        "duration_in_traffic_seconds": parse_duration(route["duration"]),
        "distance_meters": route["distanceMeters"],
    }


def ensure_csv():
    """Crea el CSV con headers si no existe."""
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_row(row: dict):
    """Agrega una fila al CSV."""
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row)


def track_once(api_key: str, direction: str = "ida"):
    """Ejecuta una medición y la guarda."""
    now = datetime.now(TIMEZONE)

    if direction == "ida":
        origin, destination = ORIGIN, DESTINATION
    else:
        origin, destination = DESTINATION, ORIGIN

    result = query_routes(api_key, origin, destination)

    row = {
        "timestamp": now.isoformat(),
        "day_of_week": DAYS_ES[now.strftime("%A")],
        "hour": now.strftime("%H:%M"),
        "direction": direction,
        "duration_seconds": result["duration_seconds"],
        "duration_in_traffic_seconds": result["duration_in_traffic_seconds"],
        "distance_meters": result["distance_meters"],
    }

    ensure_csv()
    append_row(row)

    traffic_min = result["duration_in_traffic_seconds"] / 60
    normal_min = result["duration_seconds"] / 60
    print(
        f"[{now.isoformat()}] {direction.upper()}: "
        f"{traffic_min:.0f} min (tráfico) / {normal_min:.0f} min (normal) / "
        f"{result['distance_meters'] / 1000:.1f} km"
    )


def main():
    api_key = get_api_key()

    # Por defecto mide ambas direcciones, o se puede pasar "ida" o "vuelta"
    directions = ["ida", "vuelta"]
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("ida", "vuelta"):
            directions = [arg]
        elif arg == "ambas":
            directions = ["ida", "vuelta"]
        else:
            print(f"Uso: {sys.argv[0]} [ida|vuelta|ambas]")
            sys.exit(1)

    for direction in directions:
        try:
            track_once(api_key, direction)
        except requests.RequestException as e:
            now = datetime.now(TIMEZONE)
            print(f"[{now.isoformat()}] ERROR de red ({direction}): {e}")
        except RuntimeError as e:
            now = datetime.now(TIMEZONE)
            print(f"[{now.isoformat()}] ERROR de API ({direction}): {e}")
        except Exception as e:
            now = datetime.now(TIMEZONE)
            print(f"[{now.isoformat()}] ERROR inesperado ({direction}): {e}")

        # Pequeña pausa entre requests para no abusar
        if len(directions) > 1:
            time.sleep(1)


if __name__ == "__main__":
    main()
