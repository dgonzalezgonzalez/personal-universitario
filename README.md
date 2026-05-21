# Personal universitario

Pipeline Python para descargar y procesar los recuentos por universidad de PDI, PTGAS y PEI del Ministerio de Ciencia, Innovación y Universidades.

## Uso

```powershell
py -3 main.py
```

No crea ni requiere entorno virtual. Usa `pandas` y `openpyxl` si están instalados en el Python del sistema.

## Salidas

- `data/raw/`: CSV y PC-Axis originales descargados.
- `data/processed/personal_universitario_long.csv`: base larga con PDI, PTGAS y PEI.
- `data/processed/personal_universitario_long.xlsx`: misma base en Excel.
- `data/processed/university_dimensions.csv`: tabla universidad-territorio-tipo.
- `data/processed/university_dimensions.xlsx`: misma tabla en Excel.
- `data/processed/codebook.md` y `data/processed/codebook.xlsx`: codebook basado en la metainformación oficial de los ficheros PC-Axis.
- `data/dashboard/index.html`: dashboard interactivo estático con pestañas PDI, PTGAS y PEI, generado a partir de `data/processed/personal_universitario_long.csv`.
- `data/dashboard/airef-logo.png`: logotipo usado por el dashboard.

La base larga conserva categorías totales como `España`, `Ambos sexos` y `Total`. En `Provincia`, el total nacional se codifica como `Total`.

## Dashboard

El dashboard replica la estructura visual del panel de prestaciones: pestañas superiores, filtros, dos gráficos SVG y exportación CSV por gráfico.

Filtros disponibles: `Universidad`, `Centro`, `Provincia`, `Comunidad autónoma`, `Tipo de universidad`, `Modalidad de universidad`, `Sexo` y `Grupo de edad`. El filtro `Programa investigador` aparece solo en la pestaña `PEI`. Los filtros se recalculan por pestaña y selección; `Universidad = Total` agrega las universidades compatibles con el resto de filtros, y las universidades individuales actualizan automáticamente provincia, comunidad autónoma, tipo y modalidad.

Los gráficos muestran:

- `Número de empleados`: evolución anual de la selección.
- `Peso sobre el total`: porcentaje de la selección sobre el total nacional del mismo colectivo.
