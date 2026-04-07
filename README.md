# Commute Tracker

Monitor de tráfico usando Google Maps para encontrar el mejor horario de viaje.

**Ruta:** Almarena Puerto Retiro (CABA) ↔ Asia 2055 (Belén de Escobar)

## Setup

### 1. API Key de Google Maps

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto (o usar uno existente)
3. Ir a **APIs & Services > Library** y habilitar **Directions API**
4. Ir a **APIs & Services > Credentials** y crear una **API Key**
5. (Recomendado) Restringir la key solo a Directions API

### 2. Configurar la API Key

```bash
# Agregar a ~/.zshrc (o ~/.bash_profile)
export GOOGLE_MAPS_API_KEY='AIza...'
source ~/.zshrc
```

### 3. Instalar dependencias

```bash
cd commute-tracker
pip3 install -r requirements.txt
```

## Uso

### Medir una vez (manual)

```bash
# Medir ida y vuelta
python3 commute_tracker.py

# Solo ida (origen → destino)
python3 commute_tracker.py ida

# Solo vuelta (destino → origen)
python3 commute_tracker.py vuelta
```

### Activar tracking automático (cada 10 min)

```bash
chmod +x setup_cron.sh
./setup_cron.sh start
```

### Ver estado del cron

```bash
./setup_cron.sh status
```

### Parar el tracking

```bash
./setup_cron.sh stop
```

### Ver logs en tiempo real

```bash
tail -f commute_tracker.log
```

## Análisis

Una vez que tengas datos acumulados:

```bash
# Analizar ambas direcciones
python3 commute_analysis.py

# Solo ida
python3 commute_analysis.py ida

# Solo vuelta
python3 commute_analysis.py vuelta
```

Genera:
- Duración promedio por hora del día (gráfico de barras)
- Duración promedio por día de la semana
- Heatmap día × hora
- Mejor y peor horario para salir
- Percentiles (p50, p75, p95) por franja horaria

Los gráficos se guardan en `graphs/` y se muestran en pantalla.

## Estructura

```
commute-tracker/
├── README.md
├── requirements.txt
├── commute_tracker.py      # Recolección de datos
├── commute_analysis.py     # Análisis y gráficos
├── setup_cron.sh           # Gestión del cron job
├── commute_data.csv        # Datos (se crea solo)
├── commute_tracker.log     # Logs del cron
└── graphs/                 # Gráficos PNG
```

## Costos

La Directions API cuesta ~$0.005/request. A 144 requests/día (ida+vuelta cada 10 min) = ~$0.72/día. Google Cloud da $200/mes de crédito gratis, así que sobra.
