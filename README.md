# Personal universitario

Pipeline Python para descargar y procesar los recuentos por universidad de PDI y PTGAS del Ministerio de Ciencia, Innovación y Universidades.

## Uso

```powershell
py -3 main.py
```

No crea ni requiere entorno virtual. Usa `pandas` y `openpyxl` si están instalados en el Python del sistema.

## Salidas

- `data/raw/`: CSV y PC-Axis originales descargados.
- `data/processed/personal_universitario_long.csv`: base larga con PDI y PTGAS.
- `data/processed/personal_universitario_long.xlsx`: misma base en Excel.
- `data/processed/university_dimensions.csv`: tabla universidad-territorio-tipo.
- `data/processed/university_dimensions.xlsx`: misma tabla en Excel.

La base larga conserva categorías totales como `España`, `Total centros`, `Ambos sexos` y `Total`.
