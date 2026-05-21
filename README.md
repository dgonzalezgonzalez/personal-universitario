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
- `data/processed/personal_universitario_long_updated.xlsx`: Excel alternativo si el archivo principal está abierto y Windows no permite sobrescribirlo.
- `data/processed/university_dimensions.csv`: tabla universidad-territorio-tipo.
- `data/processed/university_dimensions.xlsx`: misma tabla en Excel.
- `data/processed/codebook.md` y `data/processed/codebook.xlsx`: codebook basado en la metainformación oficial de los ficheros PC-Axis.

La base larga conserva categorías totales como `España`, `Ambos sexos` y `Total`.
