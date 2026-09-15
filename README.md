# Labo 6/7 - Caracterización de junturas Josephson

Análisis de las etapas de filtrado del arreglo experimental (ITeDA), materia
Laboratorio 6/7, Lic. en Física (UBA).

## Estructura

- `programar/`: notebooks y clases de control de instrumental (`class_spectrum_analyzer.py`,
  `class_signal_generator.py`) y de análisis de datos.
- `barrido*/`: datos crudos de los barridos en frecuencia hechos con
  `programar/keysight_SA_control.ipynb` (generador + analizador de espectro
  Keysight N9021B). Cada `.csv` es una traza completa para una frecuencia de
  prueba (`sweep_f_test_<f>kHz.csv`).

## Para arrancar

```
cd programar
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
jupyter lab
```

Los notebooks de análisis (por ejemplo `analisis_barridos_frecuencia.ipynb`)
leen los datos con rutas relativas (`barrido*/` al lado de `programar/`), así
que alcanza con clonar el repo y correrlos, sin tocar ninguna ruta.

`keysight_SA_control.ipynb` necesita estar en la red del labo (usa las IPs
del generador y el analizador de espectro).
