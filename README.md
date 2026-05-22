# Indicadores universitarios

Pipeline Python para descargar, procesar y visualizar indicadores universitarios del SIIU del Ministerio de Ciencia, Innovación y Universidades.

El proyecto integra dos familias de datos:

- Personal universitario: PDI, PTGAS y PEI.
- Estudiantes: matriculados y egresados de Grado y ciclo, Máster y Doctorado.

## Uso

```powershell
py -3 main.py
```

No crea ni requiere entorno virtual. Usa `pandas` y `openpyxl` si están instalados en el Python del sistema.

## Salidas

- `data/raw/`: CSV y PC-Axis originales descargados de personal.
- `data/raw/students/`: CSV y PC-Axis originales descargados de estudiantes.
- `data/processed/personal_universitario_long.csv`: base larga con PDI, PTGAS y PEI.
- `data/processed/personal_universitario_long.xlsx`: misma base en Excel.
- `data/processed/estudiantes_universitarios_long.csv.gz`: base larga comprimida con estudiantes matriculados y egresados.
- `data/processed/estudiantes_universitarios_long.xlsx`: misma base en Excel.
- `data/processed/university_dimensions.csv`: tabla universidad-territorio-tipo.
- `data/processed/university_dimensions.xlsx`: misma tabla en Excel.
- `data/processed/codebook.md` y `data/processed/codebook.xlsx`: codebook basado en la metainformación oficial de los ficheros PC-Axis.
- `data/dashboard/index.html`: dashboard interactivo estático con pestañas PDI, PTGAS, PEI, estudiantes matriculados y estudiantes egresados.
- `data/dashboard/airef-logo.png`: logotipo usado por el dashboard.

Las bases largas conservan categorías totales como `España`, `Ambos sexos` y `Total`. En `Provincia`, el total nacional se codifica como `Total`.

## Dashboard

El dashboard replica la estructura visual del panel de prestaciones: pestañas superiores, filtros, dos gráficos SVG y exportación CSV por gráfico.

Filtros comunes: `Universidad`, `Centro`, `Provincia`, `Comunidad autónoma`, `Tipo de universidad`, `Modalidad de universidad`, `Sexo` y `Grupo de edad`. El filtro `Programa investigador` aparece solo en la pestaña `PEI`. Los filtros `Nivel académico` y `Ámbito de estudio` aparecen en las pestañas de estudiantes.

Los filtros se recalculan por pestaña y selección; `Universidad = Total` agrega las universidades compatibles con el resto de filtros, y las universidades individuales actualizan automáticamente provincia, comunidad autónoma, tipo y modalidad.

Los gráficos muestran:

- `Número de empleados` o `Número de estudiantes`: evolución anual de la selección.
- `Peso sobre el total`: porcentaje de la selección sobre el total nacional del mismo colectivo.
