from __future__ import annotations

import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


BASE_URL = "https://estadisticas.ciencia.gob.es/jaxiPx/files/_px/es"
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


@dataclass(frozen=True)
class Source:
    staff: str
    table_prefix: str
    url_path: str
    main_table: str
    value_col: str


SOURCES = [
    Source(
        staff="PDI",
        table_prefix="PDI",
        url_path="Universitaria/Personal/EPU23/PDI/PDI_TOTAL/l0",
        main_table="PDI0301",
        value_col="PDI",
    ),
    Source(
        staff="PTGAS",
        table_prefix="PAS",
        url_path="Universitaria/Personal/EPU23/PAS/PAS_TOTAL/l0",
        main_table="PAS0301",
        value_col="PTGAS",
    ),
]


UNIVERSITY_DIMENSIONS = {
    "A Coruña": ("Galicia", "A Coruña", "Pública", "Presencial"),
    "Santiago de Compostela": ("Galicia", "A Coruña", "Pública", "Presencial"),
    "Vigo": ("Galicia", "Pontevedra", "Pública", "Presencial"),
    "Intercontinental de la Empresa": ("Galicia", "A Coruña", "Privada", "Presencial"),
    "Oviedo": ("Principado de Asturias", "Asturias", "Pública", "Presencial"),
    "Cantabria": ("Cantabria", "Cantabria", "Pública", "Presencial"),
    "Europea del Atlántico": ("Cantabria", "Cantabria", "Privada", "Presencial"),
    "País Vasco/Euskal Herriko Unibertsitatea": ("País Vasco", "Varias", "Pública", "Presencial"),
    "Mondragón Unibertsitatea": ("País Vasco", "Gipuzkoa", "Privada", "Presencial"),
    "Deusto": ("País Vasco", "Bizkaia", "Privada", "Presencial"),
    "Euneiz": ("País Vasco", "Araba/Álava", "Privada", "Presencial"),
    "Pública de Navarra": ("C. Foral de Navarra", "Navarra", "Pública", "Presencial"),
    "Navarra": ("C. Foral de Navarra", "Navarra", "Privada", "Presencial"),
    "La Rioja": ("La Rioja", "La Rioja", "Pública", "Presencial"),
    "Int. de La Rioja": ("La Rioja", "La Rioja", "Privada", "No Presencial"),
    "Internacional de La Rioja": ("La Rioja", "La Rioja", "Privada", "No Presencial"),
    "Burgos": ("Castilla y León", "Burgos", "Pública", "Presencial"),
    "León": ("Castilla y León", "León", "Pública", "Presencial"),
    "Salamanca": ("Castilla y León", "Salamanca", "Pública", "Presencial"),
    "Valladolid": ("Castilla y León", "Valladolid", "Pública", "Presencial"),
    "Europea Miguel de Cervantes": ("Castilla y León", "Valladolid", "Privada", "Presencial"),
    "Europea Miguel de Cervantes, SA": ("Castilla y León", "Valladolid", "Privada", "Presencial"),
    "Int. Isabel I de Castilla": ("Castilla y León", "Burgos", "Privada", "No Presencial"),
    "Internacional Isabel I de Castilla": ("Castilla y León", "Burgos", "Privada", "No Presencial"),
    "Cat. de Ávila": ("Castilla y León", "Ávila", "Privada", "Presencial"),
    "Católica Santa Teresa de Jesús de Ávila": ("Castilla y León", "Ávila", "Privada", "Presencial"),
    "IE Universidad": ("Castilla y León", "Segovia", "Privada", "Presencial"),
    "Pont. de Salamanca": ("Castilla y León", "Salamanca", "Privada", "Presencial"),
    "Pontificia de Salamanca": ("Castilla y León", "Salamanca", "Privada", "Presencial"),
    "Zaragoza": ("Aragón", "Zaragoza", "Pública", "Presencial"),
    "San Jorge": ("Aragón", "Zaragoza", "Privada", "Presencial"),
    "Lleida": ("Cataluña", "Lleida", "Pública", "Presencial"),
    "Girona": ("Cataluña", "Girona", "Pública", "Presencial"),
    "Rovira i Virgili": ("Cataluña", "Tarragona", "Pública", "Presencial"),
    "Autónoma de Barcelona": ("Cataluña", "Barcelona", "Pública", "Presencial"),
    "Barcelona": ("Cataluña", "Barcelona", "Pública", "Presencial"),
    "Politécnica de Catalunya": ("Cataluña", "Barcelona", "Pública", "Presencial"),
    "Pompeu Fabra": ("Cataluña", "Barcelona", "Pública", "Presencial"),
    "Abat Oliba CEU": ("Cataluña", "Barcelona", "Privada", "Presencial"),
    "Vic- Central de Catalunya": ("Cataluña", "Barcelona", "Privada", "Presencial"),
    "Vic-Central de Catalunya": ("Cataluña", "Barcelona", "Privada", "Presencial"),
    "Internacional de Catalunya": ("Cataluña", "Barcelona", "Privada", "Presencial"),
    "Ramón Llull": ("Cataluña", "Barcelona", "Privada", "Presencial"),
    "Oberta de Catalunya": ("Cataluña", "Barcelona", "Privada", "No Presencial"),
    "Castilla-La Mancha": ("Castilla-La Mancha", "Varias", "Pública", "Presencial"),
    "Extremadura": ("Extremadura", "Badajoz", "Pública", "Presencial"),
    "Alcalá": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Autónoma de Madrid": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Carlos III de Madrid": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Complutense de Madrid": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Politécnica de Madrid": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Rey Juan Carlos": ("Comunidad de Madrid", "Madrid", "Pública", "Presencial"),
    "Europea de Madrid": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Francisco de Vitoria": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Alfonso X El Sabio": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Antonio de Nebrija": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Pontificia Comillas": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "San Pablo-CEU": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Camilo José Cela": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Internacional Villanueva": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "ESIC Universidad": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "CUNEF Universidad": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Internacional de la Empresa": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Diseño, Innovación y Tecnología (UDIT)": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "Universidad de Diseño, Innovación y Tecnología (UD": ("Comunidad de Madrid", "Madrid", "Privada", "Presencial"),
    "A Distancia de Madrid": ("Comunidad de Madrid", "Madrid", "Privada", "No Presencial"),
    "Córdoba": ("Andalucía", "Córdoba", "Pública", "Presencial"),
    "Sevilla": ("Andalucía", "Sevilla", "Pública", "Presencial"),
    "Pablo de Olavide": ("Andalucía", "Sevilla", "Pública", "Presencial"),
    "Huelva": ("Andalucía", "Huelva", "Pública", "Presencial"),
    "Cádiz": ("Andalucía", "Cádiz", "Pública", "Presencial"),
    "Málaga": ("Andalucía", "Málaga", "Pública", "Presencial"),
    "Granada": ("Andalucía", "Granada", "Pública", "Presencial"),
    "Almería": ("Andalucía", "Almería", "Pública", "Presencial"),
    "Jaén": ("Andalucía", "Jaén", "Pública", "Presencial"),
    "Internacional de Andalucía": ("Andalucía", "Sevilla", "Pública", "Especial"),
    "Loyola Andalucía": ("Andalucía", "Sevilla", "Privada", "Presencial"),
    "Murcia": ("Región de Murcia", "Murcia", "Pública", "Presencial"),
    "Católica San Antonio": ("Región de Murcia", "Murcia", "Privada", "Presencial"),
    "Politécnica de Cartagena": ("Región de Murcia", "Murcia", "Pública", "Presencial"),
    "Politécnica de Valencia": ("Comunitat Valenciana", "Valencia/València", "Pública", "Presencial"),
    "Politècnica de València": ("Comunitat Valenciana", "Valencia/València", "Pública", "Presencial"),
    "Valencia (Estudi General)": ("Comunitat Valenciana", "Valencia/València", "Pública", "Presencial"),
    "València (Estudi General)": ("Comunitat Valenciana", "Valencia/València", "Pública", "Presencial"),
    "Cardenal Herrera-CEU": ("Comunitat Valenciana", "Valencia/València", "Privada", "Presencial"),
    "Católica de Valencia": ("Comunitat Valenciana", "Valencia/València", "Privada", "Presencial"),
    "Católica de Valencia San Vicente Mártir": ("Comunitat Valenciana", "Valencia/València", "Privada", "Presencial"),
    "Europea de Valencia": ("Comunitat Valenciana", "Valencia/València", "Privada", "Presencial"),
    "Internacional Valenciana": ("Comunitat Valenciana", "Valencia/València", "Privada", "No Presencial"),
    "Jaume I de Castellón": ("Comunitat Valenciana", "Castellón/Castelló", "Pública", "Presencial"),
    "Alicante": ("Comunitat Valenciana", "Alicante/Alacant", "Pública", "Presencial"),
    "Miguel Hernández de Elche": ("Comunitat Valenciana", "Alicante/Alacant", "Pública", "Presencial"),
    "Illes Balears (Les)": ("Illes Balears", "Illes Balears", "Pública", "Presencial"),
    "La Laguna": ("Canarias", "Santa Cruz de Tenerife", "Pública", "Presencial"),
    "Las Palmas de Gran Canaria": ("Canarias", "Las Palmas", "Pública", "Presencial"),
    "Europea de Canarias": ("Canarias", "Santa Cruz de Tenerife", "Privada", "Presencial"),
    "Fernando Pessoa-Canarias": ("Canarias", "Las Palmas", "Privada", "Presencial"),
    "Fernando Pessoa-Canarias (UFP-C)": ("Canarias", "Las Palmas", "Privada", "Presencial"),
    "Atlántico Medio": ("Canarias", "Las Palmas", "Privada", "Presencial"),
    "Hespérides": ("Canarias", "Las Palmas", "Privada", "No Presencial"),
    "Universidad de las Hespérides": ("Canarias", "Las Palmas", "Privada", "No Presencial"),
    "Nacional de Educación a Distancia": ("España", "España", "Pública", "No Presencial"),
    "Internacional Menéndez Pelayo": ("España", "España", "Pública", "Especial"),
}


AGGREGATE_ROWS = {
    "Total",
    "Pública",
    "Públicas",
    "Privada",
    "Privadas",
    "Pública Presencial",
    "Pública No Presencial",
    "Pública Especial",
    "Privada Presencial",
    "Privada No Presencial",
}


def mkdirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def download(url: str) -> bytes:
    ctx = ssl.create_default_context()
    # Ministry endpoint still needs OpenSSL's legacy server-connect flag in Python 3.14.
    ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
    req = urllib.request.Request(url, headers={"User-Agent": "personal-universitario/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        return resp.read()


def valid_table_payload(payload: bytes) -> bool:
    if len(payload) < 500:
        return False
    head = payload[:300].decode("utf-8-sig", errors="ignore").lower()
    return "recuentos por universidad" in head or "universidad" in head


def discover_and_download_raw() -> list[Path]:
    saved: list[Path] = []
    for src in SOURCES:
        for i in range(1, 31):
            code = f"{src.table_prefix}03{i:02d}"
            any_valid = False
            for fmt, ext in [("csv_sc", "csv"), ("px", "px")]:
                url = f"{BASE_URL}/{fmt}/{src.url_path}/{code}.px"
                try:
                    payload = download(url)
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ssl.SSLError):
                    continue
                if not valid_table_payload(payload):
                    continue
                out = RAW_DIR / f"{code}.{ext}"
                out.write_bytes(payload)
                saved.append(out)
                any_valid = True
                print(f"raw saved: {out}")
            if i > 8 and not any_valid:
                # Tables are numbered contiguously in this section; keep a small buffer after known IDs.
                pass
    return saved


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.startswith("Unnamed:") else text


def to_number(value: object) -> float | None:
    text = normalize_text(value)
    if text in {"", ".", ".."}:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def forward_fill_columns(columns: pd.MultiIndex) -> pd.MultiIndex:
    filled: list[tuple[str, ...]] = []
    last = [""] * columns.nlevels
    for col in columns:
        current = []
        for level, raw in enumerate(col):
            value = normalize_text(raw)
            if value:
                last[level] = value
            current.append(last[level])
        filled.append(tuple(current))
    return pd.MultiIndex.from_tuples(filled, names=["Centro", "Sexo", "Grupo de edad", "Indicador", "Curso"])


def parse_main_table(csv_path: Path, source: Source) -> pd.DataFrame:
    wide = pd.read_csv(csv_path, sep=";", header=[3, 4, 5, 6, 7], index_col=0, encoding="utf-8-sig")
    wide = wide.dropna(axis=1, how="all")
    wide.columns = forward_fill_columns(wide.columns)
    wide.index.name = "Universidad"

    long = wide.stack(list(range(wide.columns.nlevels)), future_stack=True).reset_index(name=source.value_col)
    long[source.value_col] = long[source.value_col].map(to_number)
    long = long.dropna(subset=[source.value_col])
    long.insert(0, "Personal", source.staff)
    long["Centro"] = long["Centro"].replace(
        {
            "Total centros": "Total",
            "Centros Propios": "Centros propios",
            "Centros Adscritos": "Centros adscritos",
        }
    )
    long["Indicador"] = long["Indicador"].str.replace(source.value_col, "", regex=False).str.strip()
    long["Indicador"] = long["Indicador"].replace({"en ETC": "ETC"})
    return long


def spread_indicators(df: pd.DataFrame, source: Source) -> pd.DataFrame:
    keys = ["Universidad", "Centro", "Sexo", "Grupo de edad", "Curso"]
    out = (
        df.pivot_table(index=keys, columns="Indicador", values=source.value_col, aggfunc="first")
        .reset_index()
        .rename_axis(columns=None)
    )
    rename = {"Total": source.value_col, "ETC": f"{source.value_col}_ETC"}
    out = out.rename(columns=rename)
    for col in [source.value_col, f"{source.value_col}_ETC"]:
        if col not in out.columns:
            out[col] = pd.NA
    return out[keys + [source.value_col, f"{source.value_col}_ETC"]]


def build_university_dimensions(universities: list[str]) -> pd.DataFrame:
    rows = []
    for name in sorted(set(universities)):
        if name in AGGREGATE_ROWS:
            tipo = "Total" if name in {"Total", "Públicas", "Privadas"} else name.split()[0]
            modalidad = "Total" if name in {"Total", "Públicas", "Privadas"} else " ".join(name.split()[1:])
            rows.append(
                {
                    "Universidad": name,
                    "Comunidad autónoma": "España",
                    "Provincia": "España",
                    "Tipo de universidad": tipo,
                    "Modalidad de universidad": modalidad,
                    "dimension_source": "aggregate_row",
                }
            )
            continue
        ca, provincia, tipo, modalidad = UNIVERSITY_DIMENSIONS.get(name, ("", "", "", ""))
        rows.append(
            {
                "Universidad": name,
                "Comunidad autónoma": ca,
                "Provincia": provincia,
                "Tipo de universidad": tipo,
                "Modalidad de universidad": modalidad,
                "dimension_source": "curated_from_map_image" if ca else "unmapped",
            }
        )
    return pd.DataFrame(rows)


def build_processed() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for src in SOURCES:
        csv_path = RAW_DIR / f"{src.main_table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing required raw file: {csv_path}")
        frames.append(parse_main_table(csv_path, src))

    pdi = spread_indicators(frames[0], SOURCES[0])
    ptgas = spread_indicators(frames[1], SOURCES[1])
    keys = ["Universidad", "Centro", "Sexo", "Grupo de edad", "Curso"]
    merged = pdi.merge(ptgas, on=keys, how="outer")

    dims = build_university_dimensions(merged["Universidad"].dropna().astype(str).tolist())
    out = merged.merge(dims, on="Universidad", how="left")
    out = out[
        [
            "Curso",
            "Universidad",
            "Centro",
            "Provincia",
            "Comunidad autónoma",
            "Tipo de universidad",
            "Modalidad de universidad",
            "Sexo",
            "Grupo de edad",
            "PDI",
            "PDI_ETC",
            "PTGAS",
            "PTGAS_ETC",
        ]
    ].sort_values(["Curso", "Universidad", "Centro", "Sexo", "Grupo de edad"])
    return out, dims


def write_codebook() -> None:
    markdown = """# Codebook

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
"""
    (PROCESSED_DIR / "codebook.md").write_text(markdown, encoding="utf-8")
    rows = [
        ("Curso", "Academic year. Official PC-Axis variable Periodo."),
        ("Universidad", "Row label from official table."),
        ("Centro", "Official center type dimension; Total centros normalized to Total."),
        ("Provincia", "Lookup field from provided university map image."),
        ("Comunidad autónoma", "Lookup field from provided university map image."),
        ("Tipo de universidad", "Lookup field from provided university map image."),
        ("Modalidad de universidad", "Lookup field from provided university map image."),
        ("Sexo", "Official sex dimension."),
        ("Grupo de edad", "Official age-group dimension."),
        ("PDI", "Official indicator PDI Total; official unit Personal."),
        ("PDI_ETC", "Official indicator PDI en ETC; stored separately from PDI."),
        ("PTGAS", "Official indicator PTGAS Total; official unit Personal."),
        ("PTGAS_ETC", "Official indicator PTGAS ETC; ETC note says Equivalente a tiempo completo."),
    ]
    pd.DataFrame(rows, columns=["variable", "description"]).to_excel(PROCESSED_DIR / "codebook.xlsx", index=False)


def write_excel_safely(df: pd.DataFrame, path: Path) -> Path:
    try:
        df.to_excel(path, index=False)
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}_updated{path.suffix}")
        df.to_excel(fallback, index=False)
        print(f"excel locked, wrote fallback: {fallback}")
        return fallback


def write_outputs(data: pd.DataFrame, dims: pd.DataFrame) -> None:
    data.to_csv(PROCESSED_DIR / "personal_universitario_long.csv", index=False, encoding="utf-8-sig")
    dims.to_csv(PROCESSED_DIR / "university_dimensions.csv", index=False, encoding="utf-8-sig")
    write_excel_safely(data, PROCESSED_DIR / "personal_universitario_long.xlsx")
    write_excel_safely(dims, PROCESSED_DIR / "university_dimensions.xlsx")
    write_codebook()

    unmapped = dims[dims["dimension_source"].eq("unmapped")]
    unmapped_path = PROCESSED_DIR / "unmapped_universities.txt"
    if not unmapped.empty:
        unmapped_path.write_text(
            "\n".join(unmapped["Universidad"].astype(str).tolist()) + "\n",
            encoding="utf-8",
        )
    elif unmapped_path.exists():
        unmapped_path.unlink()


def main() -> int:
    mkdirs()
    raw_files = discover_and_download_raw()
    if not raw_files:
        print("No raw files downloaded. Check network or source URLs.", file=sys.stderr)
        return 1
    data, dims = build_processed()
    write_outputs(data, dims)
    print(f"processed rows: {len(data):,}")
    print(f"universities/dimension rows: {len(dims):,}")
    print(f"unmapped universities: {dims['dimension_source'].eq('unmapped').sum():,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
