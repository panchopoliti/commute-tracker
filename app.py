#!/usr/bin/env python3
"""
Commute Dashboard - Dashboard interactivo con Streamlit.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from zoneinfo import ZoneInfo

CSV_FILE = Path(__file__).parent / "commute_data.csv"
TZ = ZoneInfo("America/Argentina/Buenos_Aires")

DAYS_ORDER = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DAYS_EN_TO_ES = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}

st.set_page_config(
    page_title="Commute Tracker",
    page_icon="🚗",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    if not CSV_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    df["hour_block"] = df["hour"].str[:2].astype(int)
    df["traffic_min"] = df["duration_in_traffic_seconds"] / 60
    df["normal_min"] = df["duration_seconds"] / 60
    df["extra_min"] = df["traffic_min"] - df["normal_min"]
    df["date"] = df["timestamp"].dt.date
    return df


def current_day_es() -> str:
    now = datetime.now(TZ)
    return DAYS_EN_TO_ES[now.strftime("%A")]


def current_hour() -> int:
    return datetime.now(TZ).hour


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_data()

if df.empty:
    st.error("No hay datos todavía. Ejecutá `python commute_tracker.py` primero.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("Filtros")

direction = st.sidebar.radio(
    "Dirección",
    ["ida", "vuelta"],
    format_func=lambda x: "🏢 Ida (Escobar → CABA)" if x == "ida" else "🏠 Vuelta (CABA → Escobar)",
)

available_days = [d for d in DAYS_ORDER if d in df["day_of_week"].unique()]
selected_days = st.sidebar.multiselect(
    "Días de la semana",
    available_days,
    default=available_days,
)

hour_range = st.sidebar.slider(
    "Rango horario",
    min_value=0,
    max_value=23,
    value=(6, 22),
)

# Apply filters
mask = (
    (df["direction"] == direction)
    & (df["day_of_week"].isin(selected_days))
    & (df["hour_block"] >= hour_range[0])
    & (df["hour_block"] <= hour_range[1])
)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ---------------------------------------------------------------------------
# Header + live estimate
# ---------------------------------------------------------------------------
st.title("🚗 Commute Dashboard")
st.caption(f"Escobar ↔ Puerto Retiro  ·  {len(df)} mediciones totales  ·  Última: {df['timestamp'].max().strftime('%d/%m %H:%M')}")

# "Si salgo ahora" card
today = current_day_es()
now_hour = current_hour()
now_data = df[(df["direction"] == direction) & (df["hour_block"] == now_hour)]

col_now, col_avg, col_best, col_worst = st.columns(4)

with col_now:
    if not now_data.empty:
        est = now_data["traffic_min"].mean()
        st.metric("Si salgo ahora", f"{est:.0f} min", help=f"Promedio a las {now_hour}:00 ({len(now_data)} mediciones)")
    else:
        st.metric("Si salgo ahora", "Sin datos", help="No hay mediciones para esta hora")

with col_avg:
    avg = filtered["traffic_min"].mean()
    st.metric("Promedio", f"{avg:.0f} min")

with col_best:
    best_hour = filtered.groupby("hour_block")["traffic_min"].mean().idxmin()
    best_val = filtered.groupby("hour_block")["traffic_min"].mean().min()
    st.metric("Mejor horario", f"{best_hour:02d}:00", f"{best_val:.0f} min")

with col_worst:
    worst_hour = filtered.groupby("hour_block")["traffic_min"].mean().idxmax()
    worst_val = filtered.groupby("hour_block")["traffic_min"].mean().max()
    st.metric("Peor horario", f"{worst_hour:02d}:00", f"{worst_val:.0f} min")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
tab_hour, tab_day, tab_heatmap, tab_timeline, tab_data = st.tabs(
    ["📊 Por hora", "📅 Por día", "🔥 Heatmap", "📈 Timeline", "🗂 Datos"]
)

# -- By hour --
with tab_hour:
    hourly = (
        filtered.groupby("hour_block")["traffic_min"]
        .agg(["mean", "min", "max", "count"])
        .reset_index()
    )
    hourly.columns = ["Hora", "Promedio", "Mínimo", "Máximo", "Mediciones"]
    hourly["Hora_label"] = hourly["Hora"].apply(lambda h: f"{h:02d}:00")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hourly["Hora_label"],
        y=hourly["Promedio"],
        name="Promedio",
        marker_color="#4285F4",
        text=hourly["Promedio"].round(0).astype(int),
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=hourly["Hora_label"],
        y=hourly["Mínimo"],
        mode="markers",
        name="Mínimo",
        marker=dict(color="#34A853", size=8),
    ))
    fig.add_trace(go.Scatter(
        x=hourly["Hora_label"],
        y=hourly["Máximo"],
        mode="markers",
        name="Máximo",
        marker=dict(color="#EA4335", size=8),
    ))
    fig.update_layout(
        title="Duración con tráfico por hora",
        xaxis_title="Hora",
        yaxis_title="Minutos",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

# -- By day --
with tab_day:
    daily = (
        filtered.groupby("day_of_week")["traffic_min"]
        .agg(["mean", "count"])
        .reindex(DAYS_ORDER)
        .dropna()
        .reset_index()
    )
    daily.columns = ["Día", "Promedio", "Mediciones"]

    colors = [
        "#EA4335" if v == daily["Promedio"].max()
        else "#34A853" if v == daily["Promedio"].min()
        else "#4285F4"
        for v in daily["Promedio"]
    ]
    fig = go.Figure(go.Bar(
        x=daily["Día"],
        y=daily["Promedio"],
        marker_color=colors,
        text=daily["Promedio"].round(0).astype(int),
        textposition="outside",
    ))
    fig.update_layout(
        title="Duración promedio por día de la semana",
        xaxis_title="Día",
        yaxis_title="Minutos",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Heatmap --
with tab_heatmap:
    pivot = filtered.pivot_table(
        values="traffic_min",
        index="day_of_week",
        columns="hour_block",
        aggfunc="mean",
    )
    # Reorder
    pivot = pivot.reindex(index=[d for d in DAYS_ORDER if d in pivot.index])
    pivot.columns = [f"{h:02d}:00" for h in pivot.columns]

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        text_auto=".0f",
        aspect="auto",
        labels=dict(x="Hora", y="Día", color="Minutos"),
        title="Minutos con tráfico por día y hora",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# -- Timeline --
with tab_timeline:
    timeline = filtered.sort_values("timestamp")
    fig = px.scatter(
        timeline,
        x="timestamp",
        y="traffic_min",
        color="day_of_week",
        category_orders={"day_of_week": DAYS_ORDER},
        hover_data=["hour", "normal_min"],
        labels={"traffic_min": "Minutos", "timestamp": "Fecha/hora", "day_of_week": "Día"},
        title="Evolución temporal",
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# -- Raw data --
with tab_data:
    show_cols = ["timestamp", "day_of_week", "hour", "traffic_min", "normal_min", "extra_min", "distance_meters"]
    display_df = filtered[show_cols].copy()
    display_df.columns = ["Timestamp", "Día", "Hora", "Con tráfico (min)", "Sin tráfico (min)", "Extra (min)", "Distancia (m)"]
    display_df = display_df.sort_values("Timestamp", ascending=False)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False)
    st.download_button("Descargar CSV filtrado", csv, "commute_filtered.csv", "text/csv")
