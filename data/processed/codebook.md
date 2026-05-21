# Codebook

Source: official PC-Axis files downloaded by `main.py` from the two ministry pages requested by the user.

Official source string in the downloaded PC-Axis files:
`Sistema Integrado de Información Universitaria (SIIU). Ministerio de Ciencia, Innovación y Universidades.`

Official table descriptions used for the processed database:

- `PDI0301`: `PDI por universidad, tipo de centro, sexo y grupo de edad`
- `PAS0301`: `PTGAS por universidad, tipo de centro, sexo y grupo de edad`

Official unit in both tables: `Personal`.

## Variables

| Variable | Meaning / provenance |
| --- | --- |
| `Curso` | Academic year. Official PC-Axis variable `Periodo`. |
| `Universidad` | Row label from official table. Includes total rows where present. |
| `Centro` | Official center type dimension. `Total centros` in PDI and `Total` in PTGAS are normalized to one value: `Total`. |
| `Provincia` | Added lookup field derived from the provided university map image. Aggregate rows use `España`. |
| `Comunidad autónoma` | Added lookup field derived from the provided university map image. Aggregate rows use `España`. |
| `Tipo de universidad` | Added lookup field derived from the provided university map image (`Pública`, `Privada`, or aggregate total label). |
| `Modalidad de universidad` | Added lookup field derived from the provided university map image (`Presencial`, `No Presencial`, `Especial`, or aggregate total label). |
| `Sexo` | Official sex dimension. |
| `Grupo de edad` | Official age-group dimension. PDI and PTGAS use the groups present in their official files. |
| `PDI` | Official indicator `PDI Total`; official unit `Personal`. |
| `PDI_ETC` | Official indicator `PDI en ETC`; stored separately from `PDI`. |
| `PTGAS` | Official indicator `PTGAS Total`; official unit `Personal`. |
| `PTGAS_ETC` | Official indicator `PTGAS ETC`; stored separately from `PTGAS`. The PTGAS PC-Axis note expands ETC as `Equivalente a tiempo completo`. |

## Official Notes

- `PDI0301` note: `(...) Dato omitido para preservar el secreto estadístico`.
- `PAS0301` note: `(...) Dato omitido para preservar el secreto estadístico # ETC: Equivalente a tiempo completo`.

## Missing Values

The official CSV/PC-Axis files use `..` and `.` in some cells. The pipeline writes these as missing values.
