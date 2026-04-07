#!/usr/bin/env python3
"""
Commute Analysis - Analiza los datos recolectados y genera gráficos.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CSV_FILE = Path(__file__).parent / "commute_data.csv"
OUTPUT_DIR = Path(__file__).parent / "graphs"

DAYS_ORDER = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
HOUR_ORDER = [f"{h:02d}:00" for h in range(24)]


def load_data(direction: str = None) -> pd.DataFrame:
    if not CSV_FILE.exists():
        print(f"ERROR: No se encontró {CSV_FILE}. Ejecutá commute_tracker.py primero.")
        sys.exit(1)

    df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    if df.empty:
        print("ERROR: El CSV está vacío.")
        sys.exit(1)

    df["hour_block"] = df["hour"].str[:2] + ":00"
    df["traffic_minutes"] = df["duration_in_traffic_seconds"] / 60
    df["normal_minutes"] = df["duration_seconds"] / 60

    if direction:
        df = df[df["direction"] == direction]
        if df.empty:
            print(f"ERROR: No hay datos para dirección '{direction}'.")
            sys.exit(1)

    return df


def plot_avg_by_hour(df: pd.DataFrame, direction: str):
    """Duración promedio por hora del día."""
    fig, ax = plt.subplots(figsize=(14, 6))
    hourly = df.groupby("hour_block")["traffic_minutes"].agg(["mean", "std"]).reindex(HOUR_ORDER).dropna()

    ax.bar(hourly.index, hourly["mean"], yerr=hourly["std"], capsize=3, color="#4285F4", alpha=0.8)
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Minutos")
    ax.set_title(f"Duración promedio con tráfico por hora ({direction})")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    path = OUTPUT_DIR / f"avg_by_hour_{direction}.png"
    fig.savefig(path, dpi=150)
    print(f"  Guardado: {path}")
    return fig


def plot_avg_by_day(df: pd.DataFrame, direction: str):
    """Duración promedio por día de la semana."""
    fig, ax = plt.subplots(figsize=(10, 6))
    daily = df.groupby("day_of_week")["traffic_minutes"].mean().reindex(DAYS_ORDER).dropna()

    colors = ["#EA4335" if v == daily.max() else "#34A853" if v == daily.min() else "#4285F4" for v in daily.values]
    ax.bar(daily.index, daily.values, color=colors, alpha=0.8)
    ax.set_xlabel("Día de la semana")
    ax.set_ylabel("Minutos")
    ax.set_title(f"Duración promedio con tráfico por día ({direction})")
    plt.tight_layout()

    path = OUTPUT_DIR / f"avg_by_day_{direction}.png"
    fig.savefig(path, dpi=150)
    print(f"  Guardado: {path}")
    return fig


def plot_heatmap(df: pd.DataFrame, direction: str):
    """Heatmap: día de la semana × hora del día."""
    fig, ax = plt.subplots(figsize=(16, 6))
    pivot = df.pivot_table(
        values="traffic_minutes",
        index="day_of_week",
        columns="hour_block",
        aggfunc="mean",
    )
    # Reordenar ejes
    pivot = pivot.reindex(index=DAYS_ORDER, columns=HOUR_ORDER).dropna(axis=1, how="all")

    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="RdYlGn_r", ax=ax, linewidths=0.5)
    ax.set_title(f"Heatmap: minutos con tráfico por día y hora ({direction})")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Día")
    plt.tight_layout()

    path = OUTPUT_DIR / f"heatmap_{direction}.png"
    fig.savefig(path, dpi=150)
    print(f"  Guardado: {path}")
    return fig


def print_best_worst(df: pd.DataFrame, direction: str):
    """Mejor y peor horario para salir."""
    hourly = df.groupby("hour_block")["traffic_minutes"].mean()
    best = hourly.idxmin()
    worst = hourly.idxmax()

    print(f"\n{'='*50}")
    print(f"  MEJOR Y PEOR HORARIO ({direction.upper()})")
    print(f"{'='*50}")
    print(f"  Mejor horario:  {best} ({hourly[best]:.0f} min promedio)")
    print(f"  Peor horario:   {worst} ({hourly[worst]:.0f} min promedio)")
    print(f"  Diferencia:     {hourly[worst] - hourly[best]:.0f} min")


def print_percentiles(df: pd.DataFrame, direction: str):
    """Percentiles por franja horaria."""
    print(f"\n{'='*50}")
    print(f"  PERCENTILES POR HORA ({direction.upper()})")
    print(f"{'='*50}")
    print(f"  {'Hora':<8} {'p50':>6} {'p75':>6} {'p95':>6} {'count':>6}")
    print(f"  {'-'*34}")

    for hour in HOUR_ORDER:
        subset = df[df["hour_block"] == hour]["traffic_minutes"]
        if len(subset) < 1:
            continue
        p50 = subset.quantile(0.50)
        p75 = subset.quantile(0.75)
        p95 = subset.quantile(0.95)
        print(f"  {hour:<8} {p50:>5.0f}m {p75:>5.0f}m {p95:>5.0f}m {len(subset):>6}")


def print_summary(df: pd.DataFrame, direction: str):
    """Resumen general."""
    print(f"\n{'='*50}")
    print(f"  RESUMEN ({direction.upper()})")
    print(f"{'='*50}")
    print(f"  Total mediciones:  {len(df)}")
    print(f"  Rango de fechas:   {df['timestamp'].min().date()} a {df['timestamp'].max().date()}")
    print(f"  Promedio general:  {df['traffic_minutes'].mean():.0f} min")
    print(f"  Mínimo registrado: {df['traffic_minutes'].min():.0f} min")
    print(f"  Máximo registrado: {df['traffic_minutes'].max():.0f} min")


def analyze(direction: str):
    """Corre el análisis completo para una dirección."""
    df = load_data(direction)

    print_summary(df, direction)
    print_best_worst(df, direction)
    print_percentiles(df, direction)

    print(f"\nGenerando gráficos para '{direction}'...")
    figs = []
    figs.append(plot_avg_by_hour(df, direction))
    figs.append(plot_avg_by_day(df, direction))
    figs.append(plot_heatmap(df, direction))

    return figs


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Se puede filtrar por dirección: ida, vuelta, o ambas (default)
    directions = ["ida", "vuelta"]
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("ida", "vuelta"):
            directions = [arg]
        elif arg != "ambas":
            print(f"Uso: {sys.argv[0]} [ida|vuelta|ambas]")
            sys.exit(1)

    all_figs = []
    for direction in directions:
        try:
            figs = analyze(direction)
            all_figs.extend(figs)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Error analizando '{direction}': {e}")

    if all_figs:
        print("\nMostrando gráficos...")
        plt.show()


if __name__ == "__main__":
    main()
