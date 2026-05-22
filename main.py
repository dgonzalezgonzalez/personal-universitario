from __future__ import annotations

import csv
import json
import re
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
DASHBOARD_DIR = Path("data/dashboard")


@dataclass(frozen=True)
class Source:
    staff: str
    table_prefix: str
    url_path: str
    main_table: str
    value_col: str


@dataclass(frozen=True)
class StudentSource:
    flow: str
    level: str
    url_path: str
    table_file: str
    has_center: bool = False


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
    Source(
        staff="PEI",
        table_prefix="PEI",
        url_path="Universitaria/Personal/EPU23/PEI/l0",
        main_table="PEI0301",
        value_col="PEI",
    ),
]


STUDENT_SOURCES = [
    StudentSource(
        flow="Estudiantes matriculados",
        level="Grado y ciclo",
        url_path="Universitaria/Alumnado/EEU_2025/GradoCiclo/Matriculados/l0",
        table_file="3_4_Mat_Sex_Edad1_Amb_Univ.px",
    ),
    StudentSource(
        flow="Estudiantes egresados",
        level="Grado y ciclo",
        url_path="Universitaria/Alumnado/EEU_2025/GradoCiclo/Egresados/l0",
        table_file="3_3_Egr_Sex_Edad2_Amb_Univ.px",
    ),
    StudentSource(
        flow="Estudiantes matriculados",
        level="Máster",
        url_path="Universitaria/Alumnado/EEU_2025/Master/Matriculados/l0",
        table_file="3_4_Mat_Master_Sex_Edad2_Amb_Univ.px",
    ),
    StudentSource(
        flow="Estudiantes egresados",
        level="Máster",
        url_path="Universitaria/Alumnado/EEU_2025/Master/Egresados/l0",
        table_file="3_3_Egr_Master_Sex_Edad2_Amb_Univ.px",
    ),
    StudentSource(
        flow="Estudiantes matriculados",
        level="Doctorado",
        url_path="Universitaria/Alumnado/EEU_2025/Doctorado/Matriculados/l0",
        table_file="3_3_Mat_Sex_Edad2_Amb_Univ.px",
    ),
    StudentSource(
        flow="Estudiantes egresados",
        level="Doctorado",
        url_path="Universitaria/Alumnado/EEU_2025/Doctorado/Egresados/l0",
        table_file="3_3_Egr_Sex_Edad2_Amb_Univ.px",
        has_center=True,
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
    (RAW_DIR / "students").mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)


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


def valid_student_payload(payload: bytes) -> bool:
    if len(payload) < 500:
        return False
    head = payload[:400].decode("utf-8-sig", errors="ignore").lower()
    return "estudiantes" in head or "matriculados" in head or "egresados" in head


def slug(value: str) -> str:
    text = (
        value.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def student_raw_stem(source: StudentSource) -> str:
    return f"{slug(source.flow)}_{slug(source.level)}_{Path(source.table_file).stem}"


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
    for src in STUDENT_SOURCES:
        for fmt, ext in [("csv_sc", "csv"), ("px", "px")]:
            url = f"{BASE_URL}/{fmt}/{src.url_path}/{src.table_file}"
            try:
                payload = download(url)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ssl.SSLError):
                continue
            if not valid_student_payload(payload):
                continue
            out = RAW_DIR / "students" / f"{student_raw_stem(src)}.{ext}"
            out.write_bytes(payload)
            saved.append(out)
            print(f"student raw saved: {out}")
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


def normalize_student_label(value: object) -> str:
    text = normalize_text(value)
    replacements = {
        "Todas las universidades": "Total",
        "Total universidades": "Total",
        "Total centros": "Total",
    }
    return replacements.get(text, text)


def parse_student_table(csv_path: Path, source: StudentSource) -> pd.DataFrame:
    rows = list(csv.reader(csv_path.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
    period_re = re.compile(r"^\d{4}-\d{4}$")
    period_row_idx = next(
        i
        for i, row in enumerate(rows)
        if sum(1 for value in row[1:] if period_re.match(normalize_text(value))) >= 3
    )
    scope_row = rows[period_row_idx - 1][1:]
    period_row = rows[period_row_idx][1:]

    scopes: list[str] = []
    last_scope = ""
    for raw in scope_row:
        scope = normalize_student_label(raw)
        if scope:
            last_scope = scope
        scopes.append(last_scope)

    records: list[dict[str, object]] = []
    university = ""
    center = "Total"
    sex = ""

    for row in rows[period_row_idx + 1 :]:
        if not row:
            continue
        raw_label = row[0]
        label = normalize_student_label(raw_label)
        values = row[1 : 1 + min(len(scopes), len(period_row))]
        has_values = any(to_number(value) is not None for value in values)
        if not label:
            continue

        indent = len(raw_label) - len(raw_label.lstrip(" "))
        if not has_values:
            if indent == 0:
                university = label
                center = "Total"
                sex = ""
            elif source.has_center and indent <= 4:
                center = label
                sex = ""
            else:
                sex = label
            continue

        age_group = label
        for i, raw_value in enumerate(values):
            value = to_number(raw_value)
            if value is None:
                continue
            records.append(
                {
                    "Flujo": source.flow,
                    "Nivel académico": source.level,
                    "Curso": period_row[i],
                    "Universidad": university,
                    "Centro": center,
                    "Sexo": sex,
                    "Grupo de edad": age_group,
                    "Ámbito de estudio": scopes[i],
                    "Estudiantes": value,
                }
            )

    return pd.DataFrame.from_records(records)


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


def keep_total_indicator(df: pd.DataFrame, source: Source) -> pd.DataFrame:
    keys = ["Universidad", "Centro", "Sexo", "Grupo de edad", "Curso"]
    out = df[df["Indicador"].eq("Total")].copy()
    out["Programa investigador"] = ""
    return out[keys + ["Programa investigador", source.value_col]]


def parse_pei_table(csv_path: Path) -> pd.DataFrame:
    rows = list(csv.reader(csv_path.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
    header_rows = rows[5:8]
    filled_headers: list[list[str]] = []
    for header in header_rows:
        filled: list[str] = []
        last = ""
        for value in header[1:]:
            text = value.strip()
            if text:
                last = text
            filled.append(last)
        filled_headers.append(filled)

    max_cols = min(len(h) for h in filled_headers)
    records: list[dict[str, object]] = []
    current_university = ""
    for row in rows[8:]:
        if not row or not row[0].strip():
            continue
        label = row[0]
        values = row[1 : 1 + max_cols]
        if not label.startswith(" ") and not any(normalize_text(v) for v in values):
            current_university = label.strip()
            continue
        if not current_university:
            continue
        program = label.strip()
        for i, raw_value in enumerate(values):
            value = to_number(raw_value)
            if value is None:
                continue
            records.append(
                {
                    "Universidad": current_university,
                    "Centro": "Total",
                    "Sexo": filled_headers[0][i],
                    "Grupo de edad": filled_headers[1][i],
                    "Curso": filled_headers[2][i],
                    "Programa investigador": program,
                    "PEI": value,
                }
            )
    return pd.DataFrame.from_records(records)


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
                    "Provincia": "Total",
                    "Tipo de universidad": tipo,
                    "Modalidad de universidad": modalidad,
                    "dimension_source": "aggregate_row",
                }
            )
            continue
        ca, provincia, tipo, modalidad = UNIVERSITY_DIMENSIONS.get(name, ("", "", "", ""))
        if provincia == "España":
            provincia = "Total"
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
    pdi_ptgas_frames = []
    for src in SOURCES[:2]:
        csv_path = RAW_DIR / f"{src.main_table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing required raw file: {csv_path}")
        pdi_ptgas_frames.append(parse_main_table(csv_path, src))

    pei_path = RAW_DIR / "PEI0301.csv"
    if not pei_path.exists():
        raise FileNotFoundError(f"Missing required raw file: {pei_path}")

    pdi = keep_total_indicator(pdi_ptgas_frames[0], SOURCES[0])
    ptgas = keep_total_indicator(pdi_ptgas_frames[1], SOURCES[1])
    pei = parse_pei_table(pei_path)
    keys = ["Universidad", "Centro", "Sexo", "Grupo de edad", "Curso", "Programa investigador"]
    merged = pdi.merge(ptgas, on=keys, how="outer")
    merged = merged.merge(pei, on=keys, how="outer")

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
            "Programa investigador",
            "PDI",
            "PTGAS",
            "PEI",
        ]
    ].sort_values(["Curso", "Universidad", "Centro", "Sexo", "Grupo de edad", "Programa investigador"])
    return out, dims


def build_student_processed(dims: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for src in STUDENT_SOURCES:
        csv_path = RAW_DIR / "students" / f"{student_raw_stem(src)}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing required student raw file: {csv_path}")
        frames.append(parse_student_table(csv_path, src))

    students = pd.concat(frames, ignore_index=True)
    students["Centro"] = students["Centro"].replace(
        {
            "Total centros": "Total",
            "Centros Propios": "Centros propios",
            "Centros Adscritos": "Centros adscritos",
        }
    )
    student_dims = build_university_dimensions(students["Universidad"].dropna().astype(str).tolist())
    known_dims = pd.concat([dims, student_dims], ignore_index=True)
    known_dims = known_dims.drop_duplicates("Universidad", keep="first")
    out = students.merge(
        known_dims[
            [
                "Universidad",
                "Provincia",
                "Comunidad autónoma",
                "Tipo de universidad",
                "Modalidad de universidad",
            ]
        ],
        on="Universidad",
        how="left",
    )
    out = out[
        [
            "Flujo",
            "Nivel académico",
            "Curso",
            "Universidad",
            "Centro",
            "Provincia",
            "Comunidad autónoma",
            "Tipo de universidad",
            "Modalidad de universidad",
            "Sexo",
            "Grupo de edad",
            "Ámbito de estudio",
            "Estudiantes",
        ]
    ].sort_values(["Flujo", "Nivel académico", "Curso", "Universidad", "Centro", "Sexo", "Grupo de edad", "Ámbito de estudio"])
    return out


def write_codebook() -> None:
    markdown = """# Codebook

Source: official PC-Axis files downloaded by `main.py` from the ministry pages requested by the user.

Official source string in the downloaded PC-Axis files:
`Sistema Integrado de Información Universitaria (SIIU). Ministerio de Ciencia, Innovación y Universidades.`

Official table descriptions used for the processed database:

- `PDI0301`: `PDI por universidad, tipo de centro, sexo y grupo de edad`
- `PAS0301`: `PTGAS por universidad, tipo de centro, sexo y grupo de edad`
- `PEI0301`: `PEI por universidad, programa del investigador, sexo y grupo de edad`
- Student tables under `EEU_2025`: per-university matriculados and egresados tables by sex, age group and ámbito de estudio for Grado y ciclo, Máster and Doctorado.

Official units: `Personal` for staff tables and `Número de estudiantes` for student tables.

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
| `Nivel académico` | Student level: `Grado y ciclo`, `Máster` or `Doctorado`; `Total` for staff rows in the dashboard payload. |
| `Ámbito de estudio` | Official student field dimension from the requested ámbito de estudio tables; `Total` for staff rows. |
| `Programa investigador` | Official PEI program dimension from `PEI0301`; blank for PDI/PTGAS rows. |
| `PDI` | Official indicator `PDI Total`; official unit `Personal`. |
| `PTGAS` | Official indicator `PTGAS Total`; official unit `Personal`. |
| `PEI` | Official PEI values from `PEI0301`; official unit `Personal`. |
| `Flujo` | Student flow: `Estudiantes matriculados` or `Estudiantes egresados`. |
| `Estudiantes` | Official student count from the requested SIIU tables. |

## Official Notes

- `PDI0301` note: `(...) Dato omitido para preservar el secreto estadístico`.
- `PAS0301` note: `(...) Dato omitido para preservar el secreto estadístico # ETC: Equivalente a tiempo completo`.
- `PEI0301` note: `(...) Dato omitido para preservar el secreto estadístico # El personal empleado investigador se recoge únicamente en centros propios de las universidades. # La U. Abat Oliva CEU no ha podido facilitar la información necesaria para el cálculo del indicador.`

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
        ("Nivel académico", "Student level: Grado y ciclo, Máster or Doctorado."),
        ("Ámbito de estudio", "Official student field dimension from SIIU ámbito de estudio tables."),
        ("Programa investigador", "Official PEI program dimension from PEI0301; blank for PDI/PTGAS rows."),
        ("PDI", "Official indicator PDI Total; official unit Personal."),
        ("PTGAS", "Official indicator PTGAS Total; official unit Personal."),
        ("PEI", "Official PEI values from PEI0301; official unit Personal."),
        ("Flujo", "Student flow: Estudiantes matriculados or Estudiantes egresados."),
        ("Estudiantes", "Official student count; official unit Número de estudiantes."),
    ]
    pd.DataFrame(rows, columns=["variable", "description"]).to_excel(PROCESSED_DIR / "codebook.xlsx", index=False)


def clean_options(values: pd.Series) -> list[str]:
    options = sorted(str(v) for v in values.dropna().unique() if str(v).strip())
    if "Total" in options:
        return ["Total"] + [v for v in options if v != "Total"]
    if "España" in options:
        return ["España"] + [v for v in options if v != "España"]
    if "Ambos sexos" in options:
        return ["Ambos sexos"] + [v for v in options if v != "Ambos sexos"]
    return options


def dashboard_university_rows(data: pd.DataFrame) -> pd.Series:
    university = data["Universidad"].astype(str)
    excluded = AGGREGATE_ROWS - {"Total"}
    return ~university.isin(excluded)


def build_dashboard_payload(data: pd.DataFrame, students: pd.DataFrame | None = None) -> dict[str, object]:
    dimensions = [
        "Universidad",
        "Centro",
        "Provincia",
        "Comunidad autónoma",
        "Tipo de universidad",
        "Modalidad de universidad",
        "Sexo",
        "Grupo de edad",
        "Nivel académico",
        "Ámbito de estudio",
        "Programa investigador",
    ]
    data = data[dashboard_university_rows(data)].copy()
    data["Nivel académico"] = "Total"
    data["Ámbito de estudio"] = "Total"
    rows: list[list[object]] = []
    filters_by_staff: dict[str, dict[str, list[str]]] = {}
    for metric in ["PDI", "PTGAS", "PEI"]:
        subset = data[data[metric].notna()]
        filters_by_staff[metric] = {col: clean_options(subset[col]) for col in dimensions}
        for record in subset[["Curso", *dimensions, metric]].itertuples(index=False, name=None):
            *dims, value = record
            rows.append([metric, *["" if pd.isna(v) else v for v in dims], float(value)])

    metrics = ["PDI", "PTGAS", "PEI"]
    if students is not None and not students.empty:
        students = students[dashboard_university_rows(students)].copy()
        students["Programa investigador"] = "Total"
        for metric in ["Estudiantes matriculados", "Estudiantes egresados"]:
            subset = students[students["Flujo"].eq(metric)]
            filters_by_staff[metric] = {col: clean_options(subset[col]) for col in dimensions}
            if "Total" not in filters_by_staff[metric]["Nivel académico"]:
                filters_by_staff[metric]["Nivel académico"] = ["Total", *filters_by_staff[metric]["Nivel académico"]]
            for record in subset[["Curso", *dimensions, "Estudiantes"]].itertuples(index=False, name=None):
                *dims, value = record
                rows.append([metric, *["" if pd.isna(v) else v for v in dims], float(value)])
        metrics.extend(["Estudiantes matriculados", "Estudiantes egresados"])

    filter_frames = [data[dimensions]]
    if students is not None and not students.empty:
        filter_frames.append(students.assign(**{"Programa investigador": "Total"})[dimensions])
    filters_source = pd.concat(filter_frames, ignore_index=True)
    dict_keys = [
        "metric",
        "period",
        "university",
        "center",
        "province",
        "ccaa",
        "universityType",
        "universityMode",
        "sex",
        "age",
        "academicLevel",
        "field",
        "program",
    ]
    dictionaries: dict[str, list[object]] = {}
    lookups: dict[str, dict[object, int]] = {}
    for pos, key in enumerate(dict_keys):
        values = sorted({row[pos] for row in rows}, key=lambda value: str(value))
        dictionaries[key] = values
        lookups[key] = {value: i for i, value in enumerate(values)}
    encoded_rows = [
        [*[lookups[key][row[pos]] for pos, key in enumerate(dict_keys)], row[-1]]
        for row in rows
    ]

    return {
        "periods": clean_options(pd.Series([row[1] for row in rows])),
        "staff": metrics,
        "filters": {col: clean_options(filters_source[col]) for col in dimensions},
        "filtersByStaff": filters_by_staff,
        "dicts": dictionaries,
        "rows": encoded_rows,
    }


def write_dashboard(data: pd.DataFrame, students: pd.DataFrame | None = None) -> None:
    payload = json.dumps(build_dashboard_payload(data, students), ensure_ascii=False, separators=(",", ":"))
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Indicadores universitarios</title>
  <style>
    :root {{
      --burgundy: #83082A;
      --crimson: #D00D43;
      --rose: #E397A0;
      --rose-2: #D46271;
      --text: #404040;
      --muted: #6f6f6f;
      --grid: #CCCCCC;
      --line: #e4d7db;
      --page: #f6f3f4;
      --panel: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--page);
      color: var(--text);
      font-family: "Century Gothic", "Aptos", "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    header {{
      background: #fff;
      border-bottom: 1px solid var(--line);
    }}
    .topbar, main, footer {{
      max-width: 1280px;
      margin: 0 auto;
      padding-left: 24px;
      padding-right: 24px;
    }}
    .topbar {{
      min-height: 62px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 18px;
      min-width: 0;
    }}
    .logo {{
      width: 38px;
      height: 38px;
      object-fit: contain;
      display: block;
    }}
    h1 {{
      margin: 0;
      font-size: 25px;
      line-height: 1.2;
      font-weight: 700;
    }}
    .subtitle {{
      margin: 5px 0 0;
      font-size: 13px;
      color: var(--muted);
    }}
    main {{
      padding-top: 22px;
      padding-bottom: 32px;
    }}
    .tabs {{
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 16px;
    }}
    .tab {{
      appearance: none;
      border: 0;
      background: transparent;
      color: var(--text);
      padding: 14px 22px;
      font: inherit;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      border-bottom: 4px solid transparent;
    }}
    .tab[aria-selected="true"] {{
      color: var(--burgundy);
      border-bottom-color: var(--burgundy);
    }}
    .filters {{
      display: grid;
      grid-template-columns: repeat(5, minmax(150px, 1fr));
      gap: 12px;
      margin: 16px 0 18px;
      align-items: end;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: 12px;
      font-weight: 700;
      color: var(--text);
    }}
    select {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 3px;
      background: #fff;
      color: var(--text);
      padding: 6px 9px;
      font: inherit;
      font-size: 13px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 2px 7px rgba(64,64,64,.14);
      min-width: 0;
      overflow: hidden;
    }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: start;
      padding: 16px 16px 0;
    }}
    h2 {{
      margin: 0;
      font-size: 16px;
      line-height: 1.25;
      font-weight: 700;
    }}
    .desc {{
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .csv {{
      border: 1px solid var(--burgundy);
      background: #fff;
      color: var(--burgundy);
      min-width: 52px;
      height: 30px;
      font: inherit;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .chart {{
      width: 100%;
      height: 360px;
      display: block;
      overflow: visible;
      padding: 6px 12px 14px;
    }}
    .hidden {{ display: none; }}
    .source {{
      display: none;
      margin: 0;
      padding: 0 16px 14px;
      color: var(--muted);
      font-size: 11px;
    }}
    .tooltip {{
      position: fixed;
      z-index: 20;
      pointer-events: none;
      opacity: 0;
      max-width: 260px;
      background: #fff;
      border: 1px solid var(--line);
      box-shadow: 0 10px 26px rgba(64,64,64,.16);
      padding: 9px 10px;
      font-size: 12px;
      line-height: 1.35;
    }}
    footer {{
      max-width: none;
      background: #4f0018;
      padding-top: 18px;
      padding-bottom: 28px;
      color: #fff;
      font-size: 12px;
      text-align: center;
    }}
    @media (max-width: 980px) {{
      .filters {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .topbar, main, footer {{ padding-left: 14px; padding-right: 14px; }}
      .topbar {{ align-items: start; padding-top: 16px; padding-bottom: 16px; }}
      .brand {{ align-items: start; flex-direction: column; gap: 8px; }}
      h1 {{ font-size: 21px; }}
      .tabs {{ overflow-x: auto; }}
      .tab {{ white-space: nowrap; padding-left: 12px; padding-right: 12px; }}
      .filters {{ grid-template-columns: 1fr; }}
      .chart {{ height: 310px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div class="brand">
        <img class="logo" src="airef-logo.png" alt="AIReF">
        <div>
          <h1>Indicadores universitarios</h1>
          <p class="subtitle">Dashboard interactivo de personal y estudiantes por universidad (2015-2025)</p>
        </div>
      </div>
    </div>
  </header>
  <main>
    <nav class="tabs" aria-label="Indicador">
      <button class="tab" data-tab="PDI" aria-selected="true">PDI</button>
      <button class="tab" data-tab="PTGAS" aria-selected="false">PTGAS</button>
      <button class="tab" data-tab="PEI" aria-selected="false">PEI</button>
      <button class="tab" data-tab="Estudiantes matriculados" aria-selected="false">Estudiantes matriculados</button>
      <button class="tab" data-tab="Estudiantes egresados" aria-selected="false">Estudiantes egresados</button>
    </nav>

    <section class="filters" aria-label="Filtros">
      <label>Universidad<select id="university"></select></label>
      <label>Centro<select id="center"></select></label>
      <label>Provincia<select id="province"></select></label>
      <label>Comunidad autónoma<select id="ccaa"></select></label>
      <label>Tipo de universidad<select id="universityType"></select></label>
      <label>Modalidad de universidad<select id="universityMode"></select></label>
      <label>Sexo<select id="sex"></select></label>
      <label>Grupo de edad<select id="age"></select></label>
      <label id="academicPanel" class="hidden">Nivel académico<select id="academicLevel"></select></label>
      <label id="fieldPanel" class="hidden">Ámbito de estudio<select id="field"></select></label>
      <label id="programPanel" class="hidden">Programa investigador<select id="program"></select></label>
    </section>

    <section class="grid">
      <article class="panel" id="evolutionPanel">
        <div class="panel-head">
          <div>
            <h2 id="countTitle">Número de empleados</h2>
            <p class="desc">Serie anual de la selección.</p>
          </div>
          <button class="csv" data-download="evolution">CSV</button>
        </div>
        <svg id="evolution" class="chart" role="img"></svg>
        <p class="source">Fuente: AIReF a partir de SIIU.</p>
      </article>

      <article class="panel" id="sharePanel">
        <div class="panel-head">
          <div>
            <h2>Peso sobre el total</h2>
            <p class="desc">Porcentaje de la selección sobre el total nacional.</p>
          </div>
          <button class="csv" data-download="share">CSV</button>
        </div>
        <svg id="share" class="chart" role="img"></svg>
        <p class="source">Fuente: AIReF a partir de SIIU.</p>
      </article>
    </section>
  </main>
  <footer>© Autoridad Independiente de Responsabilidad Fiscal (AIReF), AAI. Todos los derechos reservados.</footer>
  <div id="tooltip" class="tooltip"></div>

  <script>
    const db = {payload};
    const idx = {{metric:0, period:1, university:2, center:3, province:4, ccaa:5, universityType:6, universityMode:7, sex:8, age:9, academicLevel:10, field:11, program:12, value:13}};
    const filterMap = {{
      university: "Universidad",
      center: "Centro",
      province: "Provincia",
      ccaa: "Comunidad autónoma",
      universityType: "Tipo de universidad",
      universityMode: "Modalidad de universidad",
      sex: "Sexo",
      age: "Grupo de edad",
      academicLevel: "Nivel académico",
      field: "Ámbito de estudio",
      program: "Programa investigador"
    }};
    const scopeKeys = ["university", "province", "ccaa", "universityType", "universityMode"];
    const scopeTotal = {{ university: "Total", province: "Total", ccaa: "España", universityType: "Total", universityMode: "Total" }};
    const els = Object.fromEntries(Object.keys(filterMap).map(k => [k, document.getElementById(k)]));
    const downloads = {{}};
    const state = {{ tab: "PDI", updating: false }};
    const tooltip = document.getElementById("tooltip");

    function isStudentTab() {{ return state.tab.startsWith("Estudiantes "); }}
    function cell(row, key) {{ return key === "value" ? row[idx.value] : db.dicts[key][row[idx[key]]]; }}

    function init() {{
      refreshFilters();
      document.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => {{
        state.tab = btn.dataset.tab;
        document.querySelectorAll(".tab").forEach(b => b.setAttribute("aria-selected", String(b === btn)));
        togglePanels();
        refreshFilters();
        render();
      }}));
      Object.entries(els).forEach(([key, el]) => el.addEventListener("change", () => {{
        if (state.updating) return;
        if (key === "university") applyUniversityDefaults();
        refreshFilters(key);
        render();
      }}));
      document.querySelectorAll(".csv").forEach(btn => btn.addEventListener("click", () => downloadCsv(btn.dataset.download)));
      render();
    }}
    function fillSelect(select, values, current = select.value) {{
      select.innerHTML = "";
      values.forEach(value => {{
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value || "Sin clasificar";
        select.appendChild(opt);
      }});
      if (values.includes(current)) select.value = current;
      else if (values.length) select.value = values[0];
    }}
    function activeFilterKeys() {{
      return Object.keys(filterMap).filter(key => {{
        if (key === "program") return state.tab === "PEI";
        if (key === "academicLevel" || key === "field") return isStudentTab();
        return true;
      }});
    }}
    function baseRows() {{
      return db.rows.filter(row => cell(row, "metric") === state.tab && (state.tab === "PEI" || cell(row, "program") === "Total" || !cell(row, "program")));
    }}
    function staffOptions(key) {{
      return (db.filtersByStaff[state.tab] && db.filtersByStaff[state.tab][filterMap[key]]) || db.filters[filterMap[key]] || [];
    }}
    function isScopeTotal(key) {{
      return scopeTotal[key] && els[key].value === scopeTotal[key];
    }}
    function allScopeTotal() {{
      return scopeKeys.every(isScopeTotal);
    }}
    function selectedValueMatches(row, key) {{
      if (scopeKeys.includes(key) && isScopeTotal(key)) return true;
      if ((key === "academicLevel" || key === "field") && els[key].value === "Total") return true;
      return cell(row, key) === els[key].value;
    }}
    function scopedRows() {{
      return baseRows().filter(row => {{
        if (allScopeTotal()) return cell(row, "university") === "Total";
        if (cell(row, "university") === "Total") return false;
        return activeFilterKeys().every(key => selectedValueMatches(row, key));
      }});
    }}
    function rowsForOptions(targetKey) {{
      return baseRows().filter(row => {{
        if (targetKey !== "university" && cell(row, "university") === "Total") return false;
        return activeFilterKeys().every(key => key === targetKey || selectedValueMatches(row, key));
      }});
    }}
    function optionsFromRows(key, rows) {{
      if (key === "university") {{
        const values = [...new Set(rows.map(row => cell(row, "university")).filter(v => v && v !== "Total"))].sort((a, b) => a.localeCompare(b, "es"));
        return ["Total", ...values];
      }}
      const values = [...new Set(rows.map(row => cell(row, key)).filter(v => v || v === ""))].sort((a, b) => String(a).localeCompare(String(b), "es"));
      const priority = key === "sex" ? "Ambos sexos" : key === "ccaa" ? "España" : "Total";
      if ((key === "academicLevel" || key === "field") && !values.includes("Total")) values.unshift("Total");
      if (scopeTotal[key] && !values.includes(scopeTotal[key])) values.unshift(scopeTotal[key]);
      return values.includes(priority) ? [priority, ...values.filter(v => v !== priority)] : values;
    }}
    function togglePanels() {{
      document.getElementById("programPanel").classList.toggle("hidden", state.tab !== "PEI");
      document.getElementById("academicPanel").classList.toggle("hidden", !isStudentTab());
      document.getElementById("fieldPanel").classList.toggle("hidden", !isStudentTab());
      document.getElementById("countTitle").textContent = isStudentTab() ? "Número de estudiantes" : "Número de empleados";
    }}
    function refreshFilters(changedKey = null) {{
      state.updating = true;
      togglePanels();
      activeFilterKeys().forEach(key => {{
        const options = changedKey === null || key === changedKey ? staffOptions(key) : optionsFromRows(key, rowsForOptions(key));
        fillSelect(els[key], options.length ? options : staffOptions(key));
      }});
      if (state.tab !== "PEI") els.program.value = "Total";
      if (!isStudentTab()) {{
        els.academicLevel.value = "Total";
        els.field.value = "Total";
      }}
      state.updating = false;
    }}
    function applyUniversityDefaults() {{
      const selected = els.university.value;
      if (!selected || selected === "Total") return;
      const row = baseRows().find(r => cell(r, "university") === selected);
      if (!row) return;
      ["province", "ccaa", "universityType", "universityMode"].forEach(key => {{
        const value = cell(row, key);
        if (value) fillSelect(els[key], staffOptions(key), value);
      }});
    }}
    function rowMatches(row) {{
      if (cell(row, "metric") !== state.tab) return false;
      if (state.tab !== "PEI" && cell(row, "program") && cell(row, "program") !== "Total") return false;
      if (allScopeTotal()) return cell(row, "university") === "Total" && activeFilterKeys().every(key => !scopeKeys.includes(key) && selectedValueMatches(row, key) || scopeKeys.includes(key));
      if (cell(row, "university") === "Total") return false;
      return activeFilterKeys().every(key => selectedValueMatches(row, key));
    }}
    function selectedRows() {{
      const grouped = new Map();
      db.rows.filter(rowMatches).forEach(row => grouped.set(cell(row, "period"), (grouped.get(cell(row, "period")) || 0) + (cell(row, "value") || 0)));
      return db.periods.map(period => ({{ period, value: grouped.get(period) ?? null }})).filter(d => d.value != null);
    }}
    function totalRows() {{
      const grouped = new Map();
      db.rows.forEach(row => {{
        if (cell(row, "metric") !== state.tab) return;
        if (cell(row, "university") !== "Total" || cell(row, "center") !== "Total" || cell(row, "sex") !== "Ambos sexos" || cell(row, "age") !== "Total") return;
        if (isStudentTab() && cell(row, "field") !== "Total") return;
        if (state.tab === "PEI" && cell(row, "program") !== "Total") return;
        if (state.tab !== "PEI" && !isStudentTab() && cell(row, "program")) return;
        grouped.set(cell(row, "period"), (grouped.get(cell(row, "period")) || 0) + (cell(row, "value") || 0));
      }});
      return db.periods.map(period => ({{ period, value: grouped.get(period) ?? null }})).filter(d => d.value != null);
    }}
    function render() {{
      const rows = selectedRows();
      renderEvolution(rows);
      renderShare(rows);
    }}
    function shiftYear(period, delta) {{
      const y = Number(period.slice(0, 4)) + delta;
      return `${{y}}-${{y + 1}}`;
    }}
    function yoyFor(rows, point) {{
      const prev = rows.find(r => r.period === shiftYear(point.period, -1));
      return prev && prev.value ? (point.value / prev.value - 1) * 100 : null;
    }}
    function selectionLabel() {{ return state.tab; }}
    function renderEvolution(rows) {{
      const svg = document.getElementById("evolution"); clear(svg);
      const {{ w, h, m }} = dims(svg);
      const values = rows.map(r => r.value).filter(v => v != null);
      if (!values.length) return noData(svg, w, h);
      const maxY = niceAxisMax(values);
      const x = i => m.l + i / Math.max(1, rows.length - 1) * (w - m.l - m.r);
      const y = v => h - m.b - v / maxY * (h - m.t - m.b);
      grid(svg, w, h, m, 5, maxY, countAxisLabel(maxY));
      axisLabels(svg, rows, x, h, m);
      axisTitles(svg, w, h, m, "Curso", isStudentTab() ? "Estudiantes" : "Empleados");
      const pts = rows.map((r, i) => [x(i), y(r.value || 0), r]);
      smoothLine(svg, pts, "#83082A", 2.5);
      hoverPoints(svg, pts, r => `<strong>${{r.period}}</strong><br>${{selectionLabel()}}: ${{fmtInt(r.value)}}<br>Variación interanual: ${{fmtPct(yoyFor(rows, r))}}`);
      node(svg, "text", {{ x: m.l, y: 18, fill: "#83082A", "font-size": 12, "font-weight": 700 }}, selectionLabel());
      downloads.evolution = [["Curso", isStudentTab() ? "Estudiantes" : "Empleados","Variación interanual"], ...rows.map(r => [r.period, r.value, yoyFor(rows, r)])];
    }}
    function renderShare(rows) {{
      const svg = document.getElementById("share"); clear(svg);
      const {{ w, h, m }} = dims(svg);
      const totals = new Map(totalRows().map(r => [r.period, r.value]));
      const data = rows.map(r => {{
        const total = totals.get(r.period);
        return {{ period: r.period, value: total ? r.value / total * 100 : null }};
      }}).filter(r => r.value != null);
      if (!data.length) return noData(svg, w, h);
      const maxY = niceAxisMax(data.map(r => r.value), 100);
      const x = i => m.l + i / Math.max(1, data.length - 1) * (w - m.l - m.r);
      const y = v => h - m.b - Math.min(maxY, Math.max(0, v)) / maxY * (h - m.t - m.b);
      grid(svg, w, h, m, 5, maxY, v => fmtPct(v));
      axisLabels(svg, data, x, h, m);
      axisTitles(svg, w, h, m, "Curso", "% sobre total nacional");
      const pts = data.map((r, i) => [x(i), y(r.value || 0), r]);
      const base = h - m.b;
      const polygon = pts.map(p => `${{p[0]}},${{p[1]}}`).join(" ") + " " + [...pts].reverse().map(p => `${{p[0]}},${{base}}`).join(" ");
      node(svg, "polygon", {{ points: polygon, fill: "#E397A0", opacity: .35 }});
      smoothLine(svg, pts, "#83082A", 2.5);
      hoverPoints(svg, pts, r => `<strong>${{r.period}}</strong><br>Peso: ${{fmtPct(r.value)}}<br>Variación interanual: ${{fmtPct(yoyFor(data, r))}}`);
      downloads.share = [["Curso","Peso sobre total nacional","Variación interanual"], ...data.map(r => [r.period, r.value, yoyFor(data, r)])];
    }}
    function dims(svg) {{
      const box = svg.getBoundingClientRect();
      const w = Math.max(320, box.width || 600), h = Math.max(260, box.height || 360);
      svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      return {{ w, h, m: {{ t: 32, r: 24, b: 48, l: 72 }} }};
    }}
    function niceAxisMax(values, cap = Infinity) {{
      const usable = values.filter(v => v != null && Number.isFinite(v) && v > 0);
      if (!usable.length) return Number.isFinite(cap) ? cap : 1;
      const target = Math.min(Math.max(...usable) * 1.12, cap);
      const pow = Math.pow(10, Math.floor(Math.log10(target)));
      const scaled = target / pow;
      const step = scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 2.5 ? 2.5 : scaled <= 5 ? 5 : 10;
      return Math.min(step * pow, cap);
    }}
    function countAxisLabel(maxValue) {{ return v => maxValue <= 1 && v > 0 ? "" : fmtInt(v); }}
    function grid(svg, w, h, m, count, maxValue = null, formatter = v => v) {{
      for (let i = 0; i <= count; i++) {{
        const y = m.t + i / count * (h - m.t - m.b);
        node(svg, "line", {{ x1: m.l, y1: y, x2: w - m.r, y2: y, stroke: "#CCCCCC" }});
        if (maxValue != null) node(svg, "text", {{ x: m.l - 8, y: y + 4, "text-anchor": "end", fill: "#404040", "font-size": 10 }}, formatter(maxValue * (1 - i / count)));
      }}
    }}
    function axisTitles(svg, w, h, m, xLabel, yLabel) {{
      node(svg, "text", {{ x: (m.l + w - m.r) / 2, y: h - 8, "text-anchor": "middle", fill: "#404040", "font-size": 11, "font-style": "italic" }}, xLabel);
      node(svg, "text", {{ x: 20, y: (m.t + h - m.b) / 2, "text-anchor": "middle", fill: "#404040", "font-size": 11, transform: `rotate(-90 20 ${{(m.t + h - m.b) / 2}})` }}, yLabel);
    }}
    function axisLabels(svg, rows, x, h, m) {{
      rows.forEach((r, i) => node(svg, "text", {{ x: x(i), y: h - 18, "text-anchor": "middle", fill: "#404040", "font-size": 11 }}, r.period.slice(0, 4)));
    }}
    function line(svg, points, color, width, dash = "") {{
      const d = points.map((p, i) => `${{i ? "L" : "M"}}${{p[0]}},${{p[1]}}`).join(" ");
      node(svg, "path", {{ d, fill: "none", stroke: color, "stroke-width": width, "stroke-dasharray": dash }});
    }}
    function smoothLine(svg, points, color, width, dash = "") {{
      if (!points.length) return;
      if (points.length < 3) return line(svg, points, color, width, dash);
      let d = `M${{points[0][0]}},${{points[0][1]}}`;
      for (let i = 0; i < points.length - 1; i++) {{
        const p0 = points[Math.max(0, i - 1)];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[Math.min(points.length - 1, i + 2)];
        const c1x = p1[0] + (p2[0] - p0[0]) / 6;
        const c1y = p1[1] + (p2[1] - p0[1]) / 6;
        const c2x = p2[0] - (p3[0] - p1[0]) / 6;
        const c2y = p2[1] - (p3[1] - p1[1]) / 6;
        d += ` C${{c1x}},${{c1y}} ${{c2x}},${{c2y}} ${{p2[0]}},${{p2[1]}}`;
      }}
      node(svg, "path", {{ d, fill: "none", stroke: color, "stroke-width": width, "stroke-dasharray": dash, "stroke-linecap": "round", "stroke-linejoin": "round" }});
    }}
    function hoverPoints(svg, points, html, color = "#83082A") {{
      points.forEach(p => {{
        const hit = node(svg, "circle", {{ cx: p[0], cy: p[1], r: 7, fill: "transparent", stroke: "transparent" }});
        hit.addEventListener("mousemove", e => showTip(e, html(p[2])));
        hit.addEventListener("mouseleave", hideTip);
        node(svg, "circle", {{ cx: p[0], cy: p[1], r: 3, fill: color, stroke: "#fff", "stroke-width": 1.5 }});
      }});
    }}
    function node(parent, tag, attrs = {{}}, text = "") {{
      const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
      if (text !== "") el.textContent = text;
      parent.appendChild(el);
      return el;
    }}
    function clear(el) {{ while (el.firstChild) el.removeChild(el.firstChild); }}
    function noData(svg, w, h) {{
      node(svg, "text", {{ x: w / 2, y: h / 2, "text-anchor": "middle", fill: "#6f6f6f", "font-size": 13 }}, "Sin datos para la selección");
    }}
    function fmtInt(value) {{ return value == null ? "n.d." : Math.round(value).toLocaleString("es-ES"); }}
    function fmtPct(value) {{ return value == null || !Number.isFinite(value) ? "n.d." : `${{value.toLocaleString("es-ES", {{ maximumFractionDigits: 1 }})}}%`; }}
    function showTip(e, html) {{
      tooltip.innerHTML = html;
      tooltip.style.opacity = 1;
      tooltip.style.left = `${{Math.min(window.innerWidth - 280, e.clientX + 14)}}px`;
      tooltip.style.top = `${{e.clientY + 14}}px`;
    }}
    function hideTip() {{ tooltip.style.opacity = 0; }}
    function downloadCsv(key) {{
      const rows = downloads[key] || [];
      if (!rows.length) return;
      const csv = rows.map(r => r.map(v => `"${{String(v ?? "").replaceAll('"', '""')}}"`).join(";")).join("\\n");
      const blob = new Blob([csv], {{ type: "text/csv;charset=utf-8" }});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `personal_universitario_${{key}}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    }}
    init();
  </script>
</body>
</html>
"""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    (DASHBOARD_DIR / "index.html").write_text(html, encoding="utf-8")


def write_outputs(data: pd.DataFrame, dims: pd.DataFrame, students: pd.DataFrame) -> None:
    data.to_csv(PROCESSED_DIR / "personal_universitario_long.csv", index=False, encoding="utf-8-sig")
    students.to_csv(PROCESSED_DIR / "estudiantes_universitarios_long.csv", index=False, encoding="utf-8-sig")
    students.to_csv(PROCESSED_DIR / "estudiantes_universitarios_long.csv.gz", index=False, encoding="utf-8-sig", compression="gzip")
    dims.to_csv(PROCESSED_DIR / "university_dimensions.csv", index=False, encoding="utf-8-sig")
    data.to_excel(PROCESSED_DIR / "personal_universitario_long.xlsx", index=False)
    students.to_excel(PROCESSED_DIR / "estudiantes_universitarios_long.xlsx", index=False)
    dims.to_excel(PROCESSED_DIR / "university_dimensions.xlsx", index=False)
    write_codebook()
    write_dashboard(data, students)

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
    students = build_student_processed(dims)
    write_outputs(data, dims, students)
    print(f"processed rows: {len(data):,}")
    print(f"student rows: {len(students):,}")
    print(f"universities/dimension rows: {len(dims):,}")
    print(f"unmapped universities: {dims['dimension_source'].eq('unmapped').sum():,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
