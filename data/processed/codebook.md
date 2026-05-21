# Codebook

Source: official PC-Axis files downloaded by `main.py` from the ministry pages requested by the user.

Official source string in the downloaded PC-Axis files:
`Sistema Integrado de Información Universitaria (SIIU). Ministerio de Ciencia, Innovación y Universidades.`

Official table descriptions used for the processed database:

- `PDI0301`: `PDI por universidad, tipo de centro, sexo y grupo de edad`
- `PAS0301`: `PTGAS por universidad, tipo de centro, sexo y grupo de edad`
- `PEI0301`: `PEI por universidad, programa del investigador, sexo y grupo de edad`

Official unit in the three processed tables: `Personal`.

## Variables

| Variable | Meaning / provenance |
| --- | --- |
| `Curso` | Academic year. Official PC-Axis variable `Periodo`. |
| `Universidad` | Row label from official table. Includes total rows where present. |
| `Centro` | Official center type dimension. `Total centros` in PDI and `Total` in PTGAS are normalized to one value: `Total`. |
| `Provincia` | Added lookup field derived from the provided university map image. Aggregate and national rows use `Total`. |
| `Comunidad autónoma` | Added lookup field derived from the provided university map image. Aggregate rows use `España`. |
| `Tipo de universidad` | Added lookup field derived from the provided university map image (`Pública`, `Privada`, or aggregate total label). |
| `Modalidad de universidad` | Added lookup field derived from the provided university map image (`Presencial`, `No Presencial`, `Especial`, or aggregate total label). |
| `Sexo` | Official sex dimension. |
| `Grupo de edad` | Official age-group dimension. Each source uses the groups present in its official file. |
| `Programa investigador` | Official PEI program dimension from `PEI0301`; blank for PDI/PTGAS rows. |
| `PDI` | Official indicator `PDI Total`; official unit `Personal`. |
| `PTGAS` | Official indicator `PTGAS Total`; official unit `Personal`. |
| `PEI` | Official PEI values from `PEI0301`; official unit `Personal`. |

## Official Notes

- `PDI0301` note: `(...) Dato omitido para preservar el secreto estadístico`.
- `PAS0301` note: `(...) Dato omitido para preservar el secreto estadístico # ETC: Equivalente a tiempo completo`.
- `PEI0301` note: `(...) Dato omitido para preservar el secreto estadístico # El personal empleado investigador se recoge únicamente en centros propios de las universidades. # La U. Abat Oliva CEU no ha podido facilitar la información necesaria para el cálculo del indicador.`

## Missing Values

The official CSV/PC-Axis files use `..` and `.` in some cells. The pipeline writes these as missing values.
