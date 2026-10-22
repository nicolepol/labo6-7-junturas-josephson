# Labo 6/7 - Caracterización de junturas Josephson

Análisis de las etapas de filtrado del arreglo experimental (ITeDA), materia
Laboratorio 6/7, Lic. en Física (UBA).

## Estructura

- `programar/`: notebooks de simulación y análisis, y clases de control del
  instrumental (`class_spectrum_analyzer.py`, `class_signal_generator.py`).
- `barridos/1` a `barridos/8`: datos crudos de los barridos en frecuencia
  (generador + analizador de espectro Keysight N9021B), agrupados por día de
  medición. Cada `.csv` es una traza completa para una frecuencia de prueba
  (`sweep_f_test_<f>kHz.csv`).
- `LTspice/`: simulaciones de los filtros en LTspice.

## Para arrancar

```
cd programar
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
jupyter lab
```

Los notebooks leen los datos con rutas relativas (`../barridos/...`), así que
alcanza con clonar el repo y correrlos.

`keysight_SA_control.ipynb` y `barrido_automatico.ipynb` necesitan estar en la
red del labo (usan las IPs del generador y el analizador de espectro).
