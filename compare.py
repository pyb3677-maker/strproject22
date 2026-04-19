from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="EV 1:1 퍼포먼스 비교 아레나", page_icon="🚗", layout="wide")


APP_DIR = Path(__file__).resolve().parent
PROJECT_ALL_CARS_CSV = APP_DIR / "data" / "all_cars_with_images.csv"
ALL_CARS_DASHBOARD_CSV = PROJECT_ALL_CARS_CSV
ALL_CARS_IMAGES_CSV = PROJECT_ALL_CARS_CSV
USER_ALL_CARS_CSV = Path(r"C:/Users/KDS26/Documents/카카오톡 받은 파일/all_cars.csv")
SAMPLE_DATA_PATH = APP_DIR / "ev_specs_sample.csv"

CURRENT_YEAR = datetime.now().year
MODEL_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
MODEL_YEAR_SHORT_PATTERN = re.compile(r"\b(\d{2})\s*MY\b", flags=re.IGNORECASE)
EV_FUEL_PATTERN = re.compile(r"(?:전기|electric|bev|ev)", flags=re.IGNORECASE)


def format_int(value: float) -> str:
    return f"{int(round(value)):,}"


def format_float_1(value: float) -> str:
    return f"{value:.1f}"


def format_float_2(value: float) -> str:
    return f"{value:.2f}"


def format_krw(value: float) -> str:
    return f"{value / 10000:,.0f}만원"


def format_manwon_1(value: float) -> str:
    return f"{value / 10000:,.1f}"


Metric = dict[str, str | bool | Callable[[float], str]]
METRICS: list[Metric] = [
    {"key": "price_krw", "label": "가격", "unit": "", "higher_is_better": False, "formatter": format_krw},
    {"key": "power_kw", "label": "최고출력", "unit": "kW", "higher_is_better": True, "formatter": format_int},
    {"key": "torque_nm", "label": "최대토크", "unit": "N·m", "higher_is_better": True, "formatter": format_int},
    {"key": "efficiency_km_l", "label": "복합연비", "unit": "km/L", "higher_is_better": True, "formatter": format_float_1},
    {"key": "range_km", "label": "1회 충전 주행거리", "unit": "km", "higher_is_better": True, "formatter": format_int},
    {"key": "efficiency_km_kwh", "label": "전비", "unit": "km/kWh", "higher_is_better": True, "formatter": format_float_1},
    {"key": "battery_kwh", "label": "배터리 용량", "unit": "kWh", "higher_is_better": True, "formatter": format_float_1},
    {"key": "zero_to_100_s", "label": "0-100 km/h", "unit": "초", "higher_is_better": False, "formatter": format_float_1},
    {"key": "fast_charge_min", "label": "급속충전 시간(10~80%)", "unit": "분", "higher_is_better": False, "formatter": format_int},
    {"key": "top_speed_kmh", "label": "최고속도", "unit": "km/h", "higher_is_better": True, "formatter": format_int},
    {"key": "weight_kg", "label": "공차중량", "unit": "kg", "higher_is_better": False, "formatter": format_int},
    {"key": "displacement_cc", "label": "배기량", "unit": "cc", "higher_is_better": False, "formatter": format_int},
    {"key": "length_mm", "label": "전장", "unit": "mm", "higher_is_better": True, "formatter": format_int},
    {"key": "width_mm", "label": "전폭", "unit": "mm", "higher_is_better": True, "formatter": format_int},
    {"key": "height_mm", "label": "전고", "unit": "mm", "higher_is_better": True, "formatter": format_int},
    {"key": "wheelbase_mm", "label": "휠베이스", "unit": "mm", "higher_is_better": True, "formatter": format_int},
    {"key": "seats", "label": "좌석수", "unit": "석", "higher_is_better": True, "formatter": format_int},
]

INSIGHT_METRICS: list[dict[str, str | bool | Callable[[float], str]]] = [
    {
        "key": "price_per_kw_krw",
        "label": "출력 가성비",
        "unit": "만원/kW",
        "higher_is_better": False,
        "formatter": format_manwon_1,
        "guide": "낮을수록 같은 가격에서 더 높은 출력을 확보합니다.",
    },
    {
        "key": "price_per_seat_krw",
        "label": "좌석당 가격",
        "unit": "만원/석",
        "higher_is_better": False,
        "formatter": format_manwon_1,
        "guide": "낮을수록 탑승 인원 대비 구매비용이 효율적입니다.",
    },
    {
        "key": "wheelbase_ratio_pct",
        "label": "공간 효율 (휠베이스/전장)",
        "unit": "%",
        "higher_is_better": True,
        "formatter": format_float_1,
        "guide": "높을수록 같은 차 길이에서 실내 거주성 확보에 유리합니다.",
    },
    {
        "key": "footprint_m2",
        "label": "주차 부담 (차체 면적)",
        "unit": "㎡",
        "higher_is_better": False,
        "formatter": format_float_2,
        "guide": "낮을수록 도심 주차/회차에서 부담이 적습니다.",
    },
    {
        "key": "torque_per_kw",
        "label": "토크-출력 밸런스",
        "unit": "N·m/kW",
        "higher_is_better": True,
        "formatter": format_float_2,
        "guide": "높을수록 일상 가속에서 힘이 두텁게 느껴질 가능성이 큽니다.",
    },
]

PERCENTILE_METRICS: list[dict[str, str | bool]] = [
    {"key": "price_per_kw_krw", "label": "출력 가성비", "higher_is_better": False},
    {"key": "price_per_seat_krw", "label": "좌석당 가격", "higher_is_better": False},
    {"key": "wheelbase_ratio_pct", "label": "공간 효율", "higher_is_better": True},
    {"key": "torque_per_kw", "label": "토크 밀도", "higher_is_better": True},
    {"key": "power_kw", "label": "절대 출력", "higher_is_better": True},
]

NORMALIZE_DIRECTION: dict[str, bool] = {
    "price_krw": False,
    "range_km": True,
    "efficiency_km_kwh": True,
    "efficiency_km_l": True,
    "battery_kwh": True,
    "power_kw": True,
    "torque_nm": True,
    "zero_to_100_s": False,
    "fast_charge_min": False,
    "top_speed_kmh": True,
    "weight_kg": False,
    "displacement_cc": False,
    "length_mm": True,
    "width_mm": True,
    "height_mm": True,
    "wheelbase_mm": True,
    "seats": True,
    "price_per_kw_krw": False,
    "price_per_seat_krw": False,
    "wheelbase_ratio_pct": True,
    "footprint_m2": False,
    "torque_per_kw": True,
    "safety_score": True,
    "cargo_l": True,
    "charge_speed_kw": True,
}

PURPOSE_WEIGHTS: dict[str, dict[str, float]] = {
    "출퇴근 중심": {
        "price_per_seat_krw": 0.25,
        "price_krw": 0.20,
        "efficiency_km_l": 0.20,
        "efficiency_km_kwh": 0.15,
        "footprint_m2": 0.10,
        "wheelbase_ratio_pct": 0.10,
    },
    "장거리 중심": {
        "range_km": 0.25,
        "efficiency_km_l": 0.15,
        "efficiency_km_kwh": 0.15,
        "wheelbase_ratio_pct": 0.20,
        "torque_per_kw": 0.15,
        "seats": 0.10,
    },
    "가성비 중심": {
        "price_per_kw_krw": 0.30,
        "price_per_seat_krw": 0.30,
        "price_krw": 0.20,
        "efficiency_km_l": 0.10,
        "efficiency_km_kwh": 0.10,
    },
    "퍼포먼스 중심": {
        "power_kw": 0.30,
        "torque_nm": 0.20,
        "torque_per_kw": 0.15,
        "zero_to_100_s": 0.20,
        "top_speed_kmh": 0.15,
    },
    "충전 편의 중심": {
        "fast_charge_min": 0.45,
        "charge_speed_kw": 0.30,
        "range_km": 0.15,
        "efficiency_km_kwh": 0.10,
    },
}

RADAR_METRICS: list[tuple[str, str]] = [
    ("price_krw", "가격경쟁력"),
    ("power_kw", "출력"),
    ("torque_nm", "토크"),
    ("efficiency_km_kwh", "전비"),
    ("efficiency_km_l", "연비"),
    ("range_km", "주행거리"),
    ("wheelbase_mm", "공간성"),
    ("seats", "좌석수"),
]

REQUIRED_COLUMNS: dict[str, object] = {
    "maker": "Unknown",
    "model": "Unknown",
    "year": pd.NA,
    "trim": "기본",
    "price_krw": pd.NA,
    "battery_kwh": pd.NA,
    "range_km": pd.NA,
    "efficiency_km_kwh": pd.NA,
    "efficiency_km_l": pd.NA,
    "power_kw": pd.NA,
    "torque_nm": pd.NA,
    "displacement_cc": pd.NA,
    "zero_to_100_s": pd.NA,
    "fast_charge_min": pd.NA,
    "top_speed_kmh": pd.NA,
    "weight_kg": pd.NA,
    "length_mm": pd.NA,
    "width_mm": pd.NA,
    "height_mm": pd.NA,
    "wheelbase_mm": pd.NA,
    "seats": pd.NA,
    "safety_score": pd.NA,
    "cargo_l": pd.NA,
    "image_url": pd.NA,
    "image_width": pd.NA,
    "image_height": pd.NA,
    "brand": pd.NA,
    "fuel_type": pd.NA,
    "segment": pd.NA,
    "source": "all_cars",
}

NUMERIC_COLUMNS = [
    "year",
    "price_krw",
    "battery_kwh",
    "range_km",
    "efficiency_km_kwh",
    "efficiency_km_l",
    "power_kw",
    "torque_nm",
    "displacement_cc",
    "zero_to_100_s",
    "fast_charge_min",
    "top_speed_kmh",
    "weight_kg",
    "length_mm",
    "width_mm",
    "height_mm",
    "wheelbase_mm",
    "seats",
    "safety_score",
    "cargo_l",
    "image_width",
    "image_height",
]


def try_read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def extract_candidate_years(*values: object) -> list[int]:
    years: list[int] = []
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value)
        for match in MODEL_YEAR_PATTERN.finditer(text):
            year = int(match.group(1))
            if 2010 <= year <= CURRENT_YEAR + 1:
                years.append(year)
        for match in MODEL_YEAR_SHORT_PATTERN.finditer(text):
            year = 2000 + int(match.group(1))
            if 2010 <= year <= CURRENT_YEAR + 1:
                years.append(year)
    return years


def normalize_image_path(value: object) -> object:
    if value is None or pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    if text.lower().startswith(("http://", "https://")):
        return text
    path = Path(text)
    if path.is_absolute():
        if path.exists():
            return str(path)
        normalized_text = text.replace("\\", "/")
        marker = "streamlit/project/"
        if marker in normalized_text:
            relative_tail = normalized_text.split(marker, 1)[1]
            candidate = (APP_DIR / relative_tail).resolve()
            return str(candidate)
        if "ev_compare_dashboard/" in normalized_text:
            relative_tail = normalized_text.split("ev_compare_dashboard/", 1)[1]
            candidate = (APP_DIR / "ev_compare_dashboard" / relative_tail).resolve()
            return str(candidate)
        return str(path)
    return str((APP_DIR / path).resolve())


def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    for col, default in REQUIRED_COLUMNS.items():
        if col not in normalized.columns:
            normalized[col] = default

    if "price" in normalized.columns:
        normalized["price_krw"] = normalized["price_krw"].fillna(
            pd.to_numeric(normalized["price"], errors="coerce") * 10000
        )
    if "power_ps" in normalized.columns:
        normalized["power_kw"] = normalized["power_kw"].fillna(
            pd.to_numeric(normalized["power_ps"], errors="coerce") * 0.73549875
        )
    if "efficiency" in normalized.columns:
        normalized["efficiency_km_l"] = normalized["efficiency_km_l"].fillna(
            pd.to_numeric(normalized["efficiency"], errors="coerce")
        )
    if "local_path" in normalized.columns:
        normalized["image_url"] = normalized["image_url"].fillna(normalized["local_path"])
    if "image_local_path" in normalized.columns:
        normalized["image_url"] = normalized["image_url"].fillna(normalized["image_local_path"])

    for col in NUMERIC_COLUMNS:
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    normalized["maker"] = normalized["maker"].fillna("Unknown").astype(str).str.strip()
    normalized["model"] = normalized["model"].fillna("Unknown").astype(str).str.strip()
    normalized["trim"] = normalized["trim"].fillna("기본").astype(str).str.strip()
    normalized["source"] = normalized["source"].fillna("all_cars").astype(str)
    normalized["fuel_type"] = normalized["fuel_type"].fillna("").astype(str).str.strip()

    maker_empty = normalized["maker"].isin(["", "Unknown"]) & normalized["brand"].notna()
    normalized.loc[maker_empty, "maker"] = normalized.loc[maker_empty, "brand"].astype(str).str.strip()
    normalized.loc[normalized["maker"] == "", "maker"] = "Unknown"

    normalized["image_url"] = normalized["image_url"].apply(normalize_image_path)

    # 연료 타입 기준으로 효율 단위를 정규화한다.
    # EV: 전비(km/kWh), 내연기관/하이브리드: 복합연비(km/L)
    fuel_lower = normalized["fuel_type"].str.lower()
    ev_mask = fuel_lower.str.contains(EV_FUEL_PATTERN)
    non_ev_mask = ~ev_mask

    normalized.loc[ev_mask & normalized["efficiency_km_kwh"].isna(), "efficiency_km_kwh"] = normalized.loc[
        ev_mask & normalized["efficiency_km_kwh"].isna(), "efficiency_km_l"
    ]
    normalized.loc[ev_mask, "efficiency_km_l"] = pd.NA

    normalized.loc[non_ev_mask & normalized["efficiency_km_l"].isna(), "efficiency_km_l"] = normalized.loc[
        non_ev_mask & normalized["efficiency_km_l"].isna(), "efficiency_km_kwh"
    ]
    normalized.loc[non_ev_mask, "efficiency_km_kwh"] = pd.NA

    inferred_years: list[int] = []
    for _, row in normalized.iterrows():
        if pd.notna(row["year"]):
            inferred_years.append(int(float(row["year"])))
            continue
        candidates = extract_candidate_years(row.get("trim"), row.get("model"), row.get("image_url"))
        inferred_years.append(max(candidates) if candidates else CURRENT_YEAR)

    normalized["year"] = pd.Series(inferred_years, index=normalized.index, dtype="Int64")
    year_text = normalized["year"].apply(
        lambda year_value: f"{int(year_value)}년식" if pd.notna(year_value) else f"{CURRENT_YEAR}년식"
    ).astype(str)
    normalized["display_name"] = (
        normalized["maker"].astype(str)
        + " "
        + normalized["model"].astype(str)
        + " ("
        + year_text
        + ", "
        + normalized["trim"].astype(str)
        + ")"
    )

    normalized["charge_speed_kw"] = (
        normalized["battery_kwh"] / (normalized["fast_charge_min"] / 60.0)
    ).where((normalized["battery_kwh"] > 0) & (normalized["fast_charge_min"] > 0))

    # 구매 의사결정 보조 파생지표
    normalized["price_per_kw_krw"] = (
        normalized["price_krw"] / normalized["power_kw"]
    ).where((normalized["price_krw"] > 0) & (normalized["power_kw"] > 0))
    normalized["price_per_seat_krw"] = (
        normalized["price_krw"] / normalized["seats"]
    ).where((normalized["price_krw"] > 0) & (normalized["seats"] > 0))
    normalized["wheelbase_ratio_pct"] = (
        normalized["wheelbase_mm"] / normalized["length_mm"] * 100.0
    ).where((normalized["wheelbase_mm"] > 0) & (normalized["length_mm"] > 0))
    normalized["footprint_m2"] = (
        normalized["length_mm"] * normalized["width_mm"] / 1_000_000.0
    ).where((normalized["length_mm"] > 0) & (normalized["width_mm"] > 0))
    normalized["torque_per_kw"] = (
        normalized["torque_nm"] / normalized["power_kw"]
    ).where((normalized["torque_nm"] > 0) & (normalized["power_kw"] > 0))

    return normalized.sort_values(by=["maker", "model", "year", "trim"], ascending=[True, True, False, True]).reset_index(
        drop=True
    )


def merge_fields_from_source(base: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    if base.empty or source.empty:
        return base

    src = source.copy()
    if "maker" not in src.columns and "brand" in src.columns:
        src["maker"] = src["brand"]
    if "price_krw" not in src.columns and "price" in src.columns:
        src["price_krw"] = pd.to_numeric(src["price"], errors="coerce") * 10000
    if "power_kw" not in src.columns and "power_ps" in src.columns:
        src["power_kw"] = pd.to_numeric(src["power_ps"], errors="coerce") * 0.73549875
    if "efficiency_km_l" not in src.columns and "efficiency" in src.columns:
        src["efficiency_km_l"] = pd.to_numeric(src["efficiency"], errors="coerce")
    if "image_url" not in src.columns and "local_path" in src.columns:
        src["image_url"] = src["local_path"]

    key_cols = ["maker", "model", "trim"]
    if any(col not in src.columns for col in key_cols):
        return base

    fill_cols = [
        "price_krw",
        "power_kw",
        "torque_nm",
        "efficiency_km_l",
        "displacement_cc",
        "length_mm",
        "width_mm",
        "height_mm",
        "wheelbase_mm",
        "seats",
        "fuel_type",
        "segment",
        "image_url",
    ]
    available_fill_cols = [col for col in fill_cols if col in src.columns]
    if not available_fill_cols:
        return base

    left = base.copy()
    right = src[key_cols + available_fill_cols].copy()

    for col in key_cols:
        left[col] = left[col].fillna("").astype(str).str.strip()
        right[col] = right[col].fillna("").astype(str).str.strip()

    right = right.drop_duplicates(subset=key_cols, keep="first")
    merged = left.merge(right, on=key_cols, how="left", suffixes=("", "__src"))

    for col in available_fill_cols:
        src_col = f"{col}__src"
        if src_col not in merged.columns:
            continue
        if col in merged.columns:
            merged[col] = merged[col].where(merged[col].notna(), merged[src_col])
        else:
            merged[col] = merged[src_col]
        merged = merged.drop(columns=[src_col])

    return merged


@st.cache_data(show_spinner=False)
def load_all_cars_dashboard_data(path: Path, file_mtime: float | None = None) -> pd.DataFrame:
    _ = file_mtime
    if not path.exists():
        return ensure_schema(pd.DataFrame())
    raw = try_read_csv(path)

    if ALL_CARS_IMAGES_CSV.exists() and ALL_CARS_IMAGES_CSV.resolve() != path.resolve():
        raw = merge_fields_from_source(raw, try_read_csv(ALL_CARS_IMAGES_CSV))
    if USER_ALL_CARS_CSV.exists() and USER_ALL_CARS_CSV.resolve() != path.resolve():
        raw = merge_fields_from_source(raw, try_read_csv(USER_ALL_CARS_CSV))

    if "source" not in raw.columns:
        raw["source"] = "all_cars"
    else:
        raw["source"] = raw["source"].fillna("all_cars")
    return ensure_schema(raw)


@st.cache_data(show_spinner=False)
def load_sample_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["source"] = "sample"
    return ensure_schema(df)


def add_normalized_columns(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()
    for key, higher_is_better in NORMALIZE_DIRECTION.items():
        if key not in scored.columns:
            scored[f"norm_{key}"] = pd.NA
            continue
        values = pd.to_numeric(scored[key], errors="coerce")
        minimum = values.min(skipna=True)
        maximum = values.max(skipna=True)
        if pd.isna(minimum) or pd.isna(maximum):
            scored[f"norm_{key}"] = pd.NA
            continue
        if maximum == minimum:
            scored[f"norm_{key}"] = values.apply(lambda v: 0.5 if pd.notna(v) else pd.NA)
            continue
        if higher_is_better:
            scored[f"norm_{key}"] = (values - minimum) / (maximum - minimum)
        else:
            scored[f"norm_{key}"] = (maximum - values) / (maximum - minimum)
    return scored


def card_value(value: object, formatter: Callable[[float], str], unit: str) -> str:
    if value is None or pd.isna(value):
        return "데이터 없음"
    suffix = f" {unit}" if unit else ""
    return f"{formatter(float(value))}{suffix}"


def is_electric_vehicle(car: pd.Series) -> bool:
    fuel = str(car.get("fuel_type", "")).strip()
    return bool(EV_FUEL_PATTERN.search(fuel))


def efficiency_label_and_value(car: pd.Series) -> tuple[str, str]:
    if is_electric_vehicle(car):
        ev_eff = pd.to_numeric(car.get("efficiency_km_kwh"), errors="coerce")
        if pd.notna(ev_eff):
            return "전비", card_value(ev_eff, format_float_1, "km/kWh")
        fallback = pd.to_numeric(car.get("efficiency_km_l"), errors="coerce")
        if pd.notna(fallback):
            return "전비", card_value(fallback, format_float_1, "km/kWh")
        return "전비", "데이터 없음"

    ice_eff = pd.to_numeric(car.get("efficiency_km_l"), errors="coerce")
    if pd.notna(ice_eff):
        return "복합연비", card_value(ice_eff, format_float_1, "km/L")
    fallback = pd.to_numeric(car.get("efficiency_km_kwh"), errors="coerce")
    if pd.notna(fallback):
        return "복합연비", card_value(fallback, format_float_1, "km/L")
    return "복합연비", "데이터 없음"


def render_stat_tile(label: str, value: str) -> None:
    size_class = " tiny" if len(value) >= 15 else (" small" if len(value) >= 11 else "")
    value_html = f'<div class="stat-value{size_class}">{html.escape(value)}</div>'
    tile = f'<div class="stat-tile"><div class="stat-label">{html.escape(label)}</div>{value_html}</div>'
    st.markdown(tile, unsafe_allow_html=True)


def format_diff(key: str, value: float, unit: str) -> str:
    if key == "price_krw":
        return format_krw(value)
    if unit:
        if value >= 100:
            return f"{value:,.0f} {unit}"
        return f"{value:,.1f} {unit}"
    return f"{value:,.1f}"


def build_comparison_table(car_a: pd.Series, car_b: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    for metric in METRICS:
        key = str(metric["key"])
        label = str(metric["label"])
        unit = str(metric["unit"])
        higher_is_better = bool(metric["higher_is_better"])
        formatter = metric["formatter"]

        val_a = pd.to_numeric(car_a.get(key), errors="coerce")
        val_b = pd.to_numeric(car_b.get(key), errors="coerce")

        # "데이터 있는 항목만 비교" 요청: 두 차량 모두 값이 있는 항목만 표에 노출
        if pd.isna(val_a) or pd.isna(val_b):
            continue

        a_text = card_value(val_a, formatter, unit)
        b_text = card_value(val_b, formatter, unit)

        diff = float(val_a) - float(val_b)
        if abs(diff) < 1e-9:
            diff_text = "동일"
            winner = "동일"
        else:
            absolute = abs(diff)
            pct = (absolute / abs(float(val_b)) * 100) if abs(float(val_b)) > 1e-9 else None
            diff_text = format_diff(key, absolute, unit)
            if pct is not None:
                diff_text = f"{diff_text} ({pct:.1f}%)"

            if higher_is_better:
                winner = "차량 A" if diff > 0 else "차량 B"
            else:
                winner = "차량 A" if diff < 0 else "차량 B"

        rows.append({"항목": label, "차량 A": a_text, "차량 B": b_text, "차이": diff_text, "우세": winner})

    return pd.DataFrame(rows)


def style_comparison(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    col_a = df.columns.get_loc("차량 A")
    col_b = df.columns.get_loc("차량 B")
    col_winner = df.columns.get_loc("우세")

    def row_style(row: pd.Series) -> list[str]:
        styles = [""] * len(row)
        winner = row.iloc[col_winner]
        if winner == "차량 A":
            styles[col_a] = "color:#2563eb; font-weight:700;"
            styles[col_b] = "color:#dc2626; font-weight:600;"
        elif winner == "차량 B":
            styles[col_a] = "color:#dc2626; font-weight:600;"
            styles[col_b] = "color:#2563eb; font-weight:700;"
        elif winner == "동일":
            styles[col_a] = "color:#0f172a; font-weight:600;"
            styles[col_b] = "color:#0f172a; font-weight:600;"
        else:
            styles[col_a] = "color:#64748b;"
            styles[col_b] = "color:#64748b;"
        return styles

    return (
        df.style.apply(row_style, axis=1)
        .set_properties(**{"text-align": "center", "font-variant-numeric": "tabular-nums"})
        .set_properties(subset=["항목"], **{"text-align": "left", "font-weight": "700"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center"), ("font-weight", "800")]},
                {"selector": "td", "props": [("vertical-align", "middle")]},
            ]
        )
    )


def insight_value_for_car(car: pd.Series, key: str) -> float | None:
    direct = pd.to_numeric(car.get(key), errors="coerce")
    if pd.notna(direct):
        return float(direct)

    price = pd.to_numeric(car.get("price_krw"), errors="coerce")
    power = pd.to_numeric(car.get("power_kw"), errors="coerce")
    seats = pd.to_numeric(car.get("seats"), errors="coerce")
    wheelbase = pd.to_numeric(car.get("wheelbase_mm"), errors="coerce")
    length = pd.to_numeric(car.get("length_mm"), errors="coerce")
    width = pd.to_numeric(car.get("width_mm"), errors="coerce")
    torque = pd.to_numeric(car.get("torque_nm"), errors="coerce")

    if key == "price_per_kw_krw":
        if pd.notna(price) and pd.notna(power) and float(price) > 0 and float(power) > 0:
            return float(price) / float(power)
    elif key == "price_per_seat_krw":
        if pd.notna(price) and pd.notna(seats) and float(price) > 0 and float(seats) > 0:
            return float(price) / float(seats)
    elif key == "wheelbase_ratio_pct":
        if pd.notna(wheelbase) and pd.notna(length) and float(wheelbase) > 0 and float(length) > 0:
            return float(wheelbase) / float(length) * 100.0
    elif key == "footprint_m2":
        if pd.notna(length) and pd.notna(width) and float(length) > 0 and float(width) > 0:
            return float(length) * float(width) / 1_000_000.0
    elif key == "torque_per_kw":
        if pd.notna(torque) and pd.notna(power) and float(torque) > 0 and float(power) > 0:
            return float(torque) / float(power)

    return None


def build_buyer_insight_table(car_a: pd.Series, car_b: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    for metric in INSIGHT_METRICS:
        key = str(metric["key"])
        label = str(metric["label"])
        unit = str(metric["unit"])
        higher_is_better = bool(metric["higher_is_better"])
        formatter = metric["formatter"]
        guide = str(metric["guide"])

        val_a = insight_value_for_car(car_a, key)
        val_b = insight_value_for_car(car_b, key)
        if val_a is None or val_b is None:
            continue

        a_text = card_value(val_a, formatter, unit)
        b_text = card_value(val_b, formatter, unit)

        diff = float(val_a) - float(val_b)
        diff_text = card_value(abs(diff), formatter, unit)

        if abs(diff) < 1e-9:
            winner = "동일"
        else:
            if higher_is_better:
                winner = "차량 A" if diff > 0 else "차량 B"
            else:
                winner = "차량 A" if diff < 0 else "차량 B"

        rows.append(
            {
                "지표": label,
                "판단 기준": "높을수록 유리" if higher_is_better else "낮을수록 유리",
                "차량 A": a_text,
                "차량 B": b_text,
                "차이": diff_text,
                "우세": winner,
                "해석": guide,
            }
        )

    # 안전장치: 파생지표가 부족한 경우에도 최소 3개는 보여주기 위해 보조 지표를 추가
    if len(rows) < 3:
        fallback_metrics: list[dict[str, str | bool | Callable[[float], str]]] = [
            {
                "key": "price_krw",
                "label": "절대 가격",
                "unit": "",
                "higher_is_better": False,
                "formatter": format_krw,
                "guide": "낮을수록 초기 구매 부담이 작습니다.",
            },
            {
                "key": "power_kw",
                "label": "절대 출력",
                "unit": "kW",
                "higher_is_better": True,
                "formatter": format_int,
                "guide": "높을수록 고속 추월/가속 여유가 큽니다.",
            },
            {
                "key": "wheelbase_mm",
                "label": "휠베이스",
                "unit": "mm",
                "higher_is_better": True,
                "formatter": format_int,
                "guide": "길수록 2열 거주성과 주행 안정감에 유리합니다.",
            },
        ]

        existing_labels = {row["지표"] for row in rows}
        for metric in fallback_metrics:
            if len(rows) >= 3:
                break
            label = str(metric["label"])
            if label in existing_labels:
                continue
            key = str(metric["key"])
            unit = str(metric["unit"])
            higher_is_better = bool(metric["higher_is_better"])
            formatter = metric["formatter"]
            guide = str(metric["guide"])

            val_a = pd.to_numeric(car_a.get(key), errors="coerce")
            val_b = pd.to_numeric(car_b.get(key), errors="coerce")
            if pd.isna(val_a) or pd.isna(val_b):
                continue

            diff = float(val_a) - float(val_b)
            winner = "동일"
            if abs(diff) > 1e-9:
                if higher_is_better:
                    winner = "차량 A" if diff > 0 else "차량 B"
                else:
                    winner = "차량 A" if diff < 0 else "차량 B"

            rows.append(
                {
                    "지표": label,
                    "판단 기준": "높을수록 유리" if higher_is_better else "낮을수록 유리",
                    "차량 A": card_value(val_a, formatter, unit),
                    "차량 B": card_value(val_b, formatter, unit),
                    "차이": card_value(abs(diff), formatter, unit),
                    "우세": winner,
                    "해석": guide,
                }
            )
            existing_labels.add(label)

    return pd.DataFrame(rows)


def style_insight(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    col_a = df.columns.get_loc("차량 A")
    col_b = df.columns.get_loc("차량 B")
    col_winner = df.columns.get_loc("우세")

    def row_style(row: pd.Series) -> list[str]:
        styles = [""] * len(row)
        winner = row.iloc[col_winner]
        if winner == "차량 A":
            styles[col_a] = "color:#2563eb; font-weight:700;"
            styles[col_b] = "color:#dc2626; font-weight:600;"
        elif winner == "차량 B":
            styles[col_a] = "color:#dc2626; font-weight:600;"
            styles[col_b] = "color:#2563eb; font-weight:700;"
        else:
            styles[col_a] = "font-weight:600;"
            styles[col_b] = "font-weight:600;"
        return styles

    return (
        df.style.apply(row_style, axis=1)
        .set_properties(**{"text-align": "center", "font-variant-numeric": "tabular-nums"})
        .set_properties(subset=["지표", "해석"], **{"text-align": "left"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center"), ("font-weight", "800")]},
                {"selector": "td", "props": [("vertical-align", "middle")]},
            ]
        )
    )


def build_radar(car_a: pd.Series, car_b: pd.Series) -> go.Figure | None:
    categories: list[str] = []
    a_values: list[float] = []
    b_values: list[float] = []

    for key, label in RADAR_METRICS:
        col = f"norm_{key}"
        if col not in car_a.index:
            continue
        a_val = car_a.get(col)
        b_val = car_b.get(col)
        if pd.isna(a_val) or pd.isna(b_val):
            continue
        categories.append(label)
        a_values.append(float(a_val))
        b_values.append(float(b_val))

    if len(categories) < 3:
        return None

    categories_closed = categories + [categories[0]]
    a_closed = a_values + [a_values[0]]
    b_closed = b_values + [b_values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=a_closed,
            theta=categories_closed,
            fill="toself",
            name="차량 A",
            line=dict(color="#2563eb", width=2),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=b_closed,
            theta=categories_closed,
            fill="toself",
            name="차량 B",
            line=dict(color="#dc2626", width=2),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        margin=dict(l=30, r=30, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
    )
    return fig


def build_diff_chart(car_a: pd.Series, car_b: pd.Series) -> go.Figure | None:
    rows: list[dict[str, float | str]] = []
    labels = {str(metric["key"]): str(metric["label"]) for metric in METRICS}

    for key in labels:
        norm_key = f"norm_{key}"
        if norm_key not in car_a.index:
            continue
        a_val = car_a.get(norm_key)
        b_val = car_b.get(norm_key)
        if pd.isna(a_val) or pd.isna(b_val):
            continue
        rows.append({"항목": labels[key], "차량A_우위점수": (float(a_val) - float(b_val)) * 100.0})

    if not rows:
        return None

    diff_df = pd.DataFrame(rows).sort_values(by="차량A_우위점수")
    colors = ["#2563eb" if x > 0 else "#dc2626" if x < 0 else "#94a3b8" for x in diff_df["차량A_우위점수"]]

    fig = go.Figure(
        go.Bar(
            x=diff_df["차량A_우위점수"],
            y=diff_df["항목"],
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}: %{x:.1f}점<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b")
    fig.update_layout(
        xaxis_title="차량 A 우위 점수 (+면 차량 A 우세)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def build_insight_advantage_chart(car_a: pd.Series, car_b: pd.Series) -> go.Figure | None:
    rows: list[dict[str, float | str]] = []
    for metric in INSIGHT_METRICS:
        key = str(metric["key"])
        label = str(metric["label"])
        col = f"norm_{key}"
        a_val = pd.to_numeric(car_a.get(col), errors="coerce")
        b_val = pd.to_numeric(car_b.get(col), errors="coerce")
        if pd.isna(a_val) or pd.isna(b_val):
            continue
        rows.append({"지표": label, "차량A_우위점수": (float(a_val) - float(b_val)) * 100.0})

    if not rows:
        return None

    chart_df = pd.DataFrame(rows).sort_values(by="차량A_우위점수")
    colors = ["#2563eb" if x > 0 else "#dc2626" if x < 0 else "#94a3b8" for x in chart_df["차량A_우위점수"]]
    fig = go.Figure(
        go.Bar(
            x=chart_df["차량A_우위점수"],
            y=chart_df["지표"],
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}: %{x:.1f}점<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b")
    fig.update_layout(
        xaxis_title="신규 지표 기준 차량 A 우위 점수 (+면 차량 A 우세)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def build_market_positioning_map(
    data: pd.DataFrame,
    car_a: pd.Series,
    car_b: pd.Series,
    *,
    scope_mode: str = "전체 시장",
    use_log_x: bool = False,
) -> go.Figure | None:
    required = {"price_krw", "power_kw", "display_name", "fuel_type"}
    if not required.issubset(set(data.columns)):
        return None

    plot_df = data.dropna(subset=["price_krw", "power_kw"]).copy()
    if plot_df.shape[0] < 3:
        return None

    def safe_text(value: object) -> str:
        text = str(value).strip()
        return text if text and text.lower() != "nan" else ""

    def selected_xy(car: pd.Series) -> tuple[float | None, float | None]:
        px = pd.to_numeric(car.get("price_krw"), errors="coerce")
        pw = pd.to_numeric(car.get("power_kw"), errors="coerce")
        if pd.isna(px) or pd.isna(pw):
            return None, None
        return float(px), float(pw)

    # 범위 선택: 전체 / 유사군 / 주변 확대
    if scope_mode == "유사 차급/연료":
        seg_set = {safe_text(car_a.get("segment")), safe_text(car_b.get("segment"))}
        seg_set.discard("")
        fuel_set = {safe_text(car_a.get("fuel_type")), safe_text(car_b.get("fuel_type"))}
        fuel_set.discard("")

        scoped = pd.DataFrame()
        if seg_set:
            scoped = plot_df[plot_df["segment"].fillna("").astype(str).str.strip().isin(seg_set)]
        if fuel_set:
            scoped_fuel = plot_df[plot_df["fuel_type"].fillna("").astype(str).str.strip().isin(fuel_set)]
            scoped = pd.concat([scoped, scoped_fuel], ignore_index=True).drop_duplicates()
        if len(scoped) >= 16:
            plot_df = scoped
    elif scope_mode == "선택 차량 주변 확대":
        ax, ay = selected_xy(car_a)
        bx, by = selected_xy(car_b)
        x_vals = [v for v in [ax, bx] if v is not None]
        y_vals = [v for v in [ay, by] if v is not None]
        if x_vals and y_vals:
            x_min, x_max = min(x_vals), max(x_vals)
            y_min, y_max = min(y_vals), max(y_vals)

            x_pad = max(15_000_000.0, (x_max - x_min) * 0.55)
            y_pad = max(45.0, (y_max - y_min) * 0.70)
            left = max(1_000_000.0, x_min - x_pad)
            right = x_max + x_pad
            bottom = max(0.0, y_min - y_pad)
            top = y_max + y_pad

            scoped = plot_df[
                (plot_df["price_krw"] >= left)
                & (plot_df["price_krw"] <= right)
                & (plot_df["power_kw"] >= bottom)
                & (plot_df["power_kw"] <= top)
            ]
            if len(scoped) >= 12:
                plot_df = scoped.copy()

    if plot_df.shape[0] < 3:
        return None

    # x축을 만원 단위로 바꿔 축 가독성 개선
    plot_df["price_manwon"] = pd.to_numeric(plot_df["price_krw"], errors="coerce") / 10000.0

    if "wheelbase_ratio_pct" in plot_df.columns:
        size_base = pd.to_numeric(plot_df["wheelbase_ratio_pct"], errors="coerce")
    else:
        size_base = pd.Series(index=plot_df.index, dtype="float64")
    if size_base.notna().sum() < 3:
        plot_df["bubble_size"] = 10.0
    else:
        min_v = float(size_base.min())
        max_v = float(size_base.max())
        if max_v == min_v:
            plot_df["bubble_size"] = 10.0
        else:
            plot_df["bubble_size"] = 7.0 + ((size_base - min_v) / (max_v - min_v)) * 12.0

    fuel_series = plot_df["fuel_type"].fillna("기타").astype(str).str.strip().replace("", "기타")
    top_fuels = fuel_series.value_counts().head(5).index.tolist()
    plot_df["fuel_group"] = fuel_series.where(fuel_series.isin(top_fuels), "기타")

    fuel_values = plot_df["fuel_group"].value_counts().index.tolist()
    color_palette = ["#2563eb", "#f97316", "#16a34a", "#9333ea", "#0ea5e9", "#ef4444", "#64748b"]
    color_map = {fuel: color_palette[idx % len(color_palette)] for idx, fuel in enumerate(fuel_values)}

    fig = go.Figure()
    for fuel in fuel_values:
        part = plot_df[plot_df["fuel_group"] == fuel]
        fig.add_trace(
            go.Scatter(
                x=part["price_manwon"],
                y=part["power_kw"],
                mode="markers",
                name=fuel,
                marker=dict(
                    size=part["bubble_size"],
                    color=color_map.get(fuel, "#94a3b8"),
                    line=dict(color="#ffffff", width=0.8),
                    opacity=0.40,
                ),
                text=part["display_name"],
                customdata=part["price_krw"],
                hovertemplate="%{text}<br>가격: %{customdata:,.0f}원<br>출력: %{y:,.0f} kW<extra></extra>",
            )
        )

    def add_selected_marker(car: pd.Series, label: str, color: str, symbol: str) -> None:
        px = pd.to_numeric(car.get("price_krw"), errors="coerce")
        pw = pd.to_numeric(car.get("power_kw"), errors="coerce")
        if pd.isna(px) or pd.isna(pw):
            return
        x = float(px) / 10000.0
        y = float(pw)

        # 바깥 링으로 선택 차량을 강하게 강조
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker=dict(size=30, color="rgba(0,0,0,0)", line=dict(color=color, width=3)),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[label],
                textposition="top center",
                textfont=dict(size=12, color=color),
                marker=dict(size=16, color=color, symbol=symbol, line=dict(color="#ffffff", width=1.8)),
                name=label,
                hovertemplate=f"{label}<br>가격: {px:,.0f}원<br>출력: {pw:,.0f} kW<extra></extra>",
            )
        )

    add_selected_marker(car_a, "차량 A", "#2563eb", "diamond")
    add_selected_marker(car_b, "차량 B", "#dc2626", "diamond-open")

    median_price = float(pd.to_numeric(plot_df["price_manwon"], errors="coerce").median())
    median_power = float(pd.to_numeric(plot_df["power_kw"], errors="coerce").median())
    if not pd.isna(median_price):
        fig.add_vline(x=median_price, line_dash="dot", line_color="#94a3b8")
    if not pd.isna(median_power):
        fig.add_hline(y=median_power, line_dash="dot", line_color="#94a3b8")

    ax, ay = selected_xy(car_a)
    bx, by = selected_xy(car_b)
    if ax is not None and bx is not None and ay is not None and by is not None:
        delta_price = ax - bx
        delta_power = ay - by
        summary = (
            f"A-B 가격차: {delta_price:,.0f}원<br>"
            f"A-B 출력차: {delta_power:+.0f}kW"
        )
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top",
            text=summary,
            showarrow=False,
            align="left",
            font=dict(size=11, color="#334155"),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#dbe4f0",
            borderwidth=1,
            borderpad=6,
        )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="가격 (만원, 낮을수록 유리)",
        yaxis_title="최고출력 (kW, 높을수록 유리)",
        margin=dict(l=18, r=18, t=38, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0, bgcolor="rgba(255,255,255,0.6)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
    )
    fig.update_xaxes(tickformat=",.0f", type="log" if use_log_x else "linear", gridcolor="#e5eaf2")
    fig.update_yaxes(gridcolor="#e5eaf2", zeroline=False)
    return fig


def compute_percentile(value: float, series: pd.Series, *, higher_is_better: bool) -> float | None:
    if pd.isna(value):
        return None
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return None
    if higher_is_better:
        pct = (vals <= float(value)).mean() * 100.0
    else:
        pct = (vals >= float(value)).mean() * 100.0
    return float(max(0.0, min(100.0, pct)))


def choose_peer_pool(data: pd.DataFrame, car: pd.Series) -> tuple[pd.DataFrame, str]:
    fuel = str(car.get("fuel_type", "")).strip()
    segment = str(car.get("segment", "")).strip()

    pool = data.copy()
    if fuel:
        pool_fuel = pool[pool["fuel_type"].fillna("").astype(str).str.strip() == fuel]
    else:
        pool_fuel = pd.DataFrame()

    if segment:
        pool_seg = pool[pool["segment"].fillna("").astype(str).str.strip() == segment]
    else:
        pool_seg = pd.DataFrame()

    if not pool_fuel.empty and not pool_seg.empty:
        pool_both = pool_fuel[pool_fuel["segment"].fillna("").astype(str).str.strip() == segment]
        if len(pool_both) >= 6:
            return pool_both, f"비교 기준: {segment} · {fuel}"
    if len(pool_seg) >= 6:
        return pool_seg, f"비교 기준: {segment} 전체"
    if len(pool_fuel) >= 6:
        return pool_fuel, f"비교 기준: {fuel} 전체"
    return pool, "비교 기준: 전체 시장"


def build_percentile_card_items(data: pd.DataFrame, car: pd.Series) -> tuple[list[dict[str, object]], str]:
    peer_pool, peer_label = choose_peer_pool(data, car)
    items: list[dict[str, object]] = []

    for metric in PERCENTILE_METRICS:
        key = str(metric["key"])
        label = str(metric["label"])
        higher_is_better = bool(metric["higher_is_better"])
        value = pd.to_numeric(car.get(key), errors="coerce")
        if pd.isna(value) or key not in peer_pool.columns:
            continue
        pct = compute_percentile(value, peer_pool[key], higher_is_better=higher_is_better)
        if pct is None:
            continue
        items.append({"label": label, "percentile": pct, "higher_is_better": higher_is_better})

    return items, peer_label


def render_percentile_cards(title: str, items: list[dict[str, object]], peer_label: str, theme: str) -> None:
    if not items:
        st.info(f"{title}: 백분위 계산 가능한 지표가 부족합니다.")
        return

    st.markdown(f"#### {title}")
    st.caption(peer_label)
    cols = st.columns(len(items))
    theme_class = "pct-theme-a" if theme == "a" else "pct-theme-b"

    for col, item in zip(cols, items):
        label = str(item["label"])
        pct = float(item["percentile"])
        bias = "높을수록 유리" if bool(item["higher_is_better"]) else "낮을수록 유리"
        with col:
            st.markdown(
                f"""
                <div class="pct-card {theme_class}">
                    <div class="pct-title">{html.escape(label)}</div>
                    <div class="pct-value">{pct:.0f}<span class="pct-unit">백분위</span></div>
                    <div class="pct-track"><span class="pct-fill" style="width:{pct:.0f}%"></span></div>
                    <div class="pct-bias">{bias}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_insight_waterfall(car_a: pd.Series, car_b: pd.Series) -> go.Figure | None:
    def direct_value(car: pd.Series, key: str) -> float | None:
        value = pd.to_numeric(car.get(key), errors="coerce")
        if pd.isna(value):
            return None
        return float(value)

    # 신규 파생지표 + 보조 핵심지표를 함께 사용해 워터폴이 안정적으로 그려지도록 구성
    metric_pool: list[tuple[str, str, bool]] = [
        ("price_per_kw_krw", "출력 가성비", False),
        ("price_per_seat_krw", "좌석당 가격", False),
        ("wheelbase_ratio_pct", "공간 효율", True),
        ("footprint_m2", "주차 부담", False),
        ("torque_per_kw", "토크-출력 밸런스", True),
        ("price_krw", "절대 가격", False),
        ("power_kw", "절대 출력", True),
        ("wheelbase_mm", "휠베이스", True),
    ]

    rows: list[tuple[str, float]] = []
    used_labels: set[str] = set()
    for key, label, higher_is_better in metric_pool:
        if label in used_labels:
            continue

        if key in {"price_per_kw_krw", "price_per_seat_krw", "wheelbase_ratio_pct", "footprint_m2", "torque_per_kw"}:
            a_val = insight_value_for_car(car_a, key)
            b_val = insight_value_for_car(car_b, key)
        else:
            a_val = direct_value(car_a, key)
            b_val = direct_value(car_b, key)

        if a_val is None or b_val is None:
            continue

        denom = max(abs(a_val), abs(b_val), 1e-9)
        contribution = ((a_val - b_val) / denom) * 100.0
        if not higher_is_better:
            contribution = -contribution

        rows.append((label, float(contribution)))
        used_labels.add(label)

    if not rows:
        return None

    rows.sort(key=lambda x: abs(x[1]), reverse=True)
    rows = rows[:6]
    labels = [name for name, _ in rows]
    values = [val for _, val in rows]
    total = sum(values)

    fig = go.Figure(
        go.Waterfall(
            name="우세 기여도",
            orientation="v",
            measure=["relative"] * len(values) + ["total"],
            x=labels + ["총합"],
            y=values + [total],
            text=[f"{v:+.1f}" for v in values] + [f"{total:+.1f}"],
            textposition="outside",
            connector={"line": {"color": "#94a3b8", "width": 1}},
            increasing={"marker": {"color": "#2563eb"}},
            decreasing={"marker": {"color": "#dc2626"}},
            totals={"marker": {"color": "#0f172a"}},
            hovertemplate="%{x}: %{y:+.1f}점<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="구매 판단 지표",
        yaxis_title="차량 A 우위 기여도 (점)",
        margin=dict(l=10, r=10, t=20, b=20),
    )
    return fig


def estimate_efficiency(car: pd.Series) -> float | None:
    efficiency = pd.to_numeric(car.get("efficiency_km_kwh"), errors="coerce")
    if pd.notna(efficiency) and float(efficiency) > 0:
        return float(efficiency)
    range_km = pd.to_numeric(car.get("range_km"), errors="coerce")
    battery_kwh = pd.to_numeric(car.get("battery_kwh"), errors="coerce")
    if pd.notna(range_km) and pd.notna(battery_kwh) and float(battery_kwh) > 0:
        return float(range_km) / float(battery_kwh)
    return None


def has_simulation_inputs(car: pd.Series) -> bool:
    return estimate_efficiency(car) is not None


def estimate_degradation_rate(car: pd.Series, annual_km: int, fast_ratio: float) -> float | None:
    battery_kwh = pd.to_numeric(car.get("battery_kwh"), errors="coerce")
    if pd.isna(battery_kwh) or float(battery_kwh) <= 0:
        return None

    range_km = pd.to_numeric(car.get("range_km"), errors="coerce")
    if pd.isna(range_km) or float(range_km) <= 0:
        efficiency = estimate_efficiency(car)
        if efficiency is None:
            return None
        range_km = float(battery_kwh) * efficiency

    charge_cycles = annual_km / max(float(range_km), 120.0)
    base = 0.018
    cycle_penalty = min(0.020, charge_cycles * 0.00009)
    fast_penalty = 0.016 * fast_ratio
    total = base + cycle_penalty + fast_penalty
    return max(0.010, min(total, 0.070))


def build_simulation(
    car_a: pd.Series,
    car_b: pd.Series,
    annual_km: int,
    price_per_kwh: int,
    fast_charge_ratio: int,
    years: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fast_ratio = fast_charge_ratio / 100.0
    year_points = list(range(1, years + 1))

    rows_cost: list[dict[str, float | int | str]] = []
    rows_soh: list[dict[str, float | int | str]] = []

    for name, car in [("차량 A", car_a), ("차량 B", car_b)]:
        efficiency = estimate_efficiency(car)
        if efficiency is not None:
            annual_energy = annual_km / max(efficiency, 0.1)
            annual_cost = annual_energy * price_per_kwh
            for year in year_points:
                rows_cost.append({"연차": year, "구분": name, "누적 충전비(원)": annual_cost * year})

        rate = estimate_degradation_rate(car, annual_km=annual_km, fast_ratio=fast_ratio)
        if rate is not None:
            for year in year_points:
                soh = max(60.0, 100.0 * ((1.0 - rate) ** year))
                rows_soh.append({"연차": year, "구분": name, "SOH(%)": soh})

    return pd.DataFrame(rows_cost), pd.DataFrame(rows_soh)


def weighted_score(car: pd.Series, purpose: str) -> tuple[float | None, list[tuple[str, float]]]:
    weights = PURPOSE_WEIGHTS[purpose]
    score = 0.0
    used_weight = 0.0
    contributions: list[tuple[str, float]] = []

    for metric_key, weight in weights.items():
        col = f"norm_{metric_key}"
        metric_score = car.get(col)
        if metric_score is None or pd.isna(metric_score):
            continue
        weighted = float(metric_score) * weight
        score += weighted
        used_weight += weight
        contributions.append((metric_key, weighted))

    if used_weight == 0:
        return None, []

    contributions.sort(key=lambda x: x[1], reverse=True)
    return score / used_weight, contributions


def purpose_metric_name(metric_key: str) -> str:
    mapping = {
        "price_krw": "가격 경쟁력",
        "price_per_kw_krw": "출력 가성비",
        "price_per_seat_krw": "좌석당 가격",
        "range_km": "주행거리",
        "efficiency_km_kwh": "전비",
        "efficiency_km_l": "복합연비",
        "battery_kwh": "배터리",
        "power_kw": "출력",
        "torque_nm": "토크",
        "torque_per_kw": "토크-출력 밸런스",
        "zero_to_100_s": "가속 성능",
        "fast_charge_min": "충전시간",
        "top_speed_kmh": "최고속도",
        "weight_kg": "경량성",
        "safety_score": "안전성",
        "cargo_l": "적재공간",
        "charge_speed_kw": "충전 파워",
        "wheelbase_mm": "휠베이스",
        "wheelbase_ratio_pct": "공간 효율",
        "footprint_m2": "주차 부담",
        "length_mm": "전장",
        "seats": "좌석수",
    }
    return mapping.get(metric_key, metric_key)


def resolve_image_source(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower().startswith(("http://", "https://")):
        return text
    path = Path(text)
    if path.exists():
        return str(path)
    return None


def car_picker(data: pd.DataFrame, key_prefix: str, default_display_name: str | None = None) -> pd.Series:
    seed_row = None
    if default_display_name:
        matched = data[data["display_name"] == default_display_name]
        if not matched.empty:
            seed_row = matched.iloc[0]

    maker_options = sorted(data["maker"].dropna().astype(str).unique().tolist())
    maker_default = str(seed_row["maker"]) if seed_row is not None else maker_options[0]
    maker_index = maker_options.index(maker_default) if maker_default in maker_options else 0
    maker = st.selectbox("브랜드", options=maker_options, index=maker_index, key=f"{key_prefix}_maker")

    maker_df = data[data["maker"] == maker].copy()
    model_options = sorted(maker_df["model"].dropna().astype(str).unique().tolist())
    model_default = str(seed_row["model"]) if seed_row is not None and seed_row["maker"] == maker else model_options[0]
    model_index = model_options.index(model_default) if model_default in model_options else 0
    model = st.selectbox("모델", options=model_options, index=model_index, key=f"{key_prefix}_model")

    model_df = maker_df[maker_df["model"] == model].copy()
    model_df = model_df.sort_values(by=["year", "trim"], ascending=[False, True]).reset_index(drop=True)

    trim_indices = list(model_df.index)

    def trim_label(row_index: int) -> str:
        row = model_df.loc[row_index]
        year = int(row["year"]) if pd.notna(row["year"]) else CURRENT_YEAR
        fuel = str(row.get("fuel_type", "")).strip()
        fuel_text = f" | {fuel}" if fuel and fuel.lower() != "nan" else ""
        return f"{year}년식 | {row['trim']}{fuel_text}"

    trim_index = 0
    if seed_row is not None and seed_row["maker"] == maker and seed_row["model"] == model:
        selected_trim = model_df[model_df["display_name"] == seed_row["display_name"]]
        if not selected_trim.empty:
            trim_index = int(selected_trim.index[0])

    selected_row_index = st.selectbox(
        "트림",
        options=trim_indices,
        index=trim_index,
        key=f"{key_prefix}_trim",
        format_func=trim_label,
    )
    return model_df.loc[int(selected_row_index)]


def resolve_selected_car_defaults(data: pd.DataFrame) -> tuple[str, str]:
    display_names = data["display_name"].dropna().astype(str).tolist()
    if not display_names:
        return "", ""

    default_a = st.session_state.get("selected_car_a_display_name")
    if default_a not in display_names:
        default_a = display_names[0]

    remaining = [name for name in display_names if name != default_a]
    default_b = st.session_state.get("selected_car_b_display_name")
    if default_b not in display_names or default_b == default_a:
        default_b = remaining[0] if remaining else default_a

    return str(default_a), str(default_b)


def sync_selected_car_state(car_a: pd.Series, car_b: pd.Series) -> None:
    if str(car_a["display_name"]) == str(car_b["display_name"]):
        return
    st.session_state["selected_car_a_display_name"] = str(car_a["display_name"])
    st.session_state["selected_car_b_display_name"] = str(car_b["display_name"])


def sync_number_from_slider(slider_key: str, input_key: str) -> None:
    st.session_state[input_key] = int(st.session_state[slider_key])


def sync_slider_from_number(
    slider_key: str,
    input_key: str,
    min_value: int,
    max_value: int,
    step: int,
) -> None:
    raw_value = int(st.session_state[input_key])
    clamped = max(min_value, min(max_value, raw_value))
    adjusted = int(round((clamped - min_value) / step) * step + min_value)
    adjusted = max(min_value, min(max_value, adjusted))
    st.session_state[input_key] = adjusted
    st.session_state[slider_key] = adjusted


def render_synced_slider_number_input(
    label: str,
    min_value: int,
    max_value: int,
    default_value: int,
    step: int,
    slider_key: str,
    input_key: str,
) -> int:
    if slider_key not in st.session_state:
        st.session_state[slider_key] = default_value
    if input_key not in st.session_state:
        st.session_state[input_key] = int(st.session_state[slider_key])

    st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=int(st.session_state[slider_key]),
        step=step,
        key=slider_key,
        on_change=sync_number_from_slider,
        args=(slider_key, input_key),
    )
    st.number_input(
        f"{label} 직접 입력",
        min_value=min_value,
        max_value=max_value,
        step=step,
        key=input_key,
        on_change=sync_slider_from_number,
        args=(slider_key, input_key, min_value, max_value, step),
    )
    return int(st.session_state[slider_key])


def sync_budget_inputs_from_slider(slider_key: str, min_key: str, max_key: str) -> None:
    lower, upper = st.session_state[slider_key]
    st.session_state[min_key] = int(lower)
    st.session_state[max_key] = int(upper)


def sync_budget_slider_from_inputs(
    slider_key: str,
    min_key: str,
    max_key: str,
    min_value: int,
    max_value: int,
    step: int,
) -> None:
    lower = int(st.session_state[min_key])
    upper = int(st.session_state[max_key])
    lower = max(min_value, min(max_value, lower))
    upper = max(min_value, min(max_value, upper))
    if lower > upper:
        lower, upper = upper, lower

    lower = int(round((lower - min_value) / step) * step + min_value)
    upper = int(round((upper - min_value) / step) * step + min_value)
    lower = max(min_value, min(max_value, lower))
    upper = max(min_value, min(max_value, upper))

    st.session_state[min_key] = lower
    st.session_state[max_key] = upper
    st.session_state[slider_key] = (lower, upper)


def render_synced_budget_range_input(
    label: str,
    min_value: int,
    max_value: int,
    default_range: tuple[int, int],
    step: int,
    slider_key: str,
    min_key: str,
    max_key: str,
) -> tuple[int, int]:
    if slider_key not in st.session_state:
        st.session_state[slider_key] = default_range
    if min_key not in st.session_state:
        st.session_state[min_key] = int(st.session_state[slider_key][0])
    if max_key not in st.session_state:
        st.session_state[max_key] = int(st.session_state[slider_key][1])

    st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=tuple(st.session_state[slider_key]),
        step=step,
        key=slider_key,
        on_change=sync_budget_inputs_from_slider,
        args=(slider_key, min_key, max_key),
    )
    budget_col_1, budget_col_2 = st.columns(2)
    with budget_col_1:
        st.number_input(
            "최소 예산",
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=min_key,
            on_change=sync_budget_slider_from_inputs,
            args=(slider_key, min_key, max_key, min_value, max_value, step),
        )
    with budget_col_2:
        st.number_input(
            "최대 예산",
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=max_key,
            on_change=sync_budget_slider_from_inputs,
            args=(slider_key, min_key, max_key, min_value, max_value, step),
    )
    return tuple(int(v) for v in st.session_state[slider_key])


def render_car_panel(car: pd.Series, title: str) -> None:
    fuel_text = str(car.get("fuel_type", "")).strip() or "연료 미상"
    fuel_badge_class = "vehicle-chip-ev" if is_electric_vehicle(car) else "vehicle-chip-ice"
    eff_label, eff_value = efficiency_label_and_value(car)
    aux_label = "1회 충전 주행거리" if is_electric_vehicle(car) else "배기량"
    aux_value = (
        card_value(car.get("range_km"), format_int, "km")
        if is_electric_vehicle(car)
        else card_value(car.get("displacement_cc"), format_int, "cc")
    )

    st.markdown(
        f"""
        <div class="vehicle-heading">
            <h3 class="vehicle-label">{html.escape(title)}</h3>
            <span class="vehicle-chip {fuel_badge_class}">{html.escape(fuel_text)}</span>
        </div>
        <p class="vehicle-name">{html.escape(str(car["display_name"]))}</p>
        """,
        unsafe_allow_html=True,
    )

    image_source = resolve_image_source(car.get("image_url"))
    if image_source:
        _, image_col, _ = st.columns([0.03, 0.94, 0.03])
        with image_col:
            st.image(image_source, use_container_width=True)
    else:
        st.markdown('<div class="car-image-placeholder">이미지 데이터 없음</div>', unsafe_allow_html=True)

    stat_rows = [
        ("가격", card_value(car.get("price_krw"), format_krw, "")),
        ("최고출력", card_value(car.get("power_kw"), format_int, "kW")),
        ("최대토크", card_value(car.get("torque_nm"), format_int, "N·m")),
        (eff_label, eff_value),
        ("전장", card_value(car.get("length_mm"), format_int, "mm")),
        ("휠베이스", card_value(car.get("wheelbase_mm"), format_int, "mm")),
        (aux_label, aux_value),
        ("좌석수", card_value(car.get("seats"), format_int, "석")),
    ]

    for row_start in range(0, len(stat_rows), 4):
        row_cols = st.columns(4, gap="small")
        for col, (label, value) in zip(row_cols, stat_rows[row_start : row_start + 4]):
            with col:
                render_stat_tile(label, value)



MAINTENANCE_FINANCE_TERM_OPTIONS = [12, 24, 36, 48, 60]
MAINTENANCE_DEFAULT_GASOLINE_PRICE = 1993
MAINTENANCE_DEFAULT_DIESEL_PRICE = 1987
MAINTENANCE_DEFAULT_ELECTRIC_PRICE = 339
MAINTENANCE_DEFAULT_HYDROGEN_PRICE = 10228
MAINTENANCE_INSTALLMENT_RATE = {12: 0.044, 24: 0.047, 36: 0.050, 48: 0.051, 60: 0.052}
MAINTENANCE_LEASE_RATE = {12: 0.045, 24: 0.048, 36: 0.052, 48: 0.055, 60: 0.058}
MAINTENANCE_LEASE_RESIDUAL = {12: 0.75, 24: 0.65, 36: 0.55, 48: 0.45, 60: 0.35}
MAINTENANCE_TAX_REFERENCE_TEXT = (
    "자동차세는 전기·수소차 13만원 고정, 그 외 승용차는 "
    "1,000cc 이하 80원/cc, 1,600cc 이하 140원/cc, "
    "1,600cc 초과 200원/cc 기준에 지방교육세를 반영한 추정치입니다."
)
TOP5_PRIORITY_OPTIONS = {
    "연비": "fuel_cost",
    "경제성": "maintenance_cost",
    "주행 성능": "driving_performance",
    "실내 공간": "interior_space",
}
TOP5_STANDARD_ANNUAL_DISTANCE = 15000
TOP5_STANDARD_GASOLINE_PRICE = 1950
TOP5_STANDARD_DIESEL_PRICE = 1950
TOP5_STANDARD_FINANCE_TYPE = "일시불"
TOP5_STANDARD_FINANCE_TERM_MONTHS = 36


def inject_dashboard_extension_css() -> None:
    st.markdown(
        """
        <style>
        .subsection-wrap {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 255, 0.98) 100%);
            border: 1px solid #dbe4f0;
            border-radius: 22px;
            padding: 18px 18px 18px;
            box-shadow: 0 16px 34px rgba(28, 47, 94, 0.08);
            margin-bottom: 16px;
        }
        .subsection-note {
            color: #6a7488;
            font-size: 0.94rem;
            line-height: 1.58;
            margin-bottom: 10px;
        }
        .recommend-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #dde6f1;
            border-radius: 20px;
            padding: 16px 15px 15px;
            min-height: 100%;
            box-shadow: 0 12px 26px rgba(28, 47, 94, 0.06);
        }
        .recommend-rank {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 1.95rem;
            font-weight: 800;
            color: #d7e1f0;
            line-height: 1;
            margin-bottom: 6px;
        }
        .recommend-brand {
            color: #6b7688;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 2px;
        }
        .recommend-model {
            color: #111827;
            font-size: 1.05rem;
            font-weight: 800;
            line-height: 1.3;
            min-height: 2.5em;
            margin-bottom: 6px;
        }
        .recommend-score {
            color: #1f5fd6;
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 1.24rem;
            font-weight: 800;
            margin: 6px 0 8px;
        }
        .recommend-meta {
            color: #66758c;
            font-size: 0.84rem;
            line-height: 1.48;
            font-weight: 600;
        }
        .recommend-empty {
            border: 1px dashed #cfdae9;
            border-radius: 20px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            color: #64748b;
            padding: 28px 18px;
            text-align: center;
            font-weight: 600;
            box-shadow: 0 10px 24px rgba(28, 47, 94, 0.05);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def maintenance_energy_type(fuel_type: object) -> str:
    fuel = str(fuel_type or "").strip()
    if "전기" in fuel:
        return "electric"
    if "수소" in fuel:
        return "hydrogen"
    if "디젤" in fuel:
        return "diesel"
    return "gasoline"


def maintenance_efficiency_unit(car: pd.Series) -> str:
    energy_type = maintenance_energy_type(car.get("fuel_type"))
    if energy_type == "electric":
        return "km/kWh"
    if energy_type == "hydrogen":
        return "km/kg"
    return "km/L"


def maintenance_fuel_price_unit(car: pd.Series) -> str:
    energy_type = maintenance_energy_type(car.get("fuel_type"))
    if energy_type == "electric":
        return "원/kWh"
    if energy_type == "hydrogen":
        return "원/kg"
    return "원/L"


def maintenance_fuel_price_for_vehicle(car: pd.Series, gasoline_price: int, diesel_price: int) -> float:
    energy_type = maintenance_energy_type(car.get("fuel_type"))
    if energy_type == "diesel":
        return float(diesel_price)
    if energy_type == "electric":
        return float(MAINTENANCE_DEFAULT_ELECTRIC_PRICE)
    if energy_type == "hydrogen":
        return float(MAINTENANCE_DEFAULT_HYDROGEN_PRICE)
    return float(gasoline_price)


def maintenance_annual_car_tax(car: pd.Series) -> float:
    displacement_cc = pd.to_numeric(car.get("displacement_cc"), errors="coerce")
    energy_type = maintenance_energy_type(car.get("fuel_type"))
    if energy_type in {"electric", "hydrogen"} or pd.isna(displacement_cc) or float(displacement_cc) <= 0:
        return 130000.0
    cc = float(displacement_cc)
    if cc <= 1000:
        base_tax = cc * 80
    elif cc <= 1600:
        base_tax = cc * 140
    else:
        base_tax = cc * 200
    return base_tax * 1.3


def maintenance_installment_monthly_payment(price_krw: float, term_months: int) -> float:
    annual_rate = MAINTENANCE_INSTALLMENT_RATE[term_months]
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return float(price_krw) / term_months
    return float(price_krw) * monthly_rate / (1 - (1 + monthly_rate) ** (-term_months))


def maintenance_lease_monthly_payment(price_krw: float, term_months: int) -> tuple[float, float]:
    residual_rate = MAINTENANCE_LEASE_RESIDUAL[term_months]
    residual_value = float(price_krw) * residual_rate
    annual_rate = MAINTENANCE_LEASE_RATE[term_months]
    monthly_depreciation = (float(price_krw) - residual_value) / term_months
    monthly_finance_charge = ((float(price_krw) + residual_value) / 2) * (annual_rate / 12)
    return monthly_depreciation + monthly_finance_charge, residual_rate


def maintenance_finance_annual_cost(finance_type: str, car: pd.Series, term_months: int) -> tuple[float, float, float | None]:
    price_krw = pd.to_numeric(car.get("price_krw"), errors="coerce")
    if pd.isna(price_krw) or float(price_krw) <= 0:
        return 0.0, 0.0, None
    if finance_type == "할부":
        monthly_payment = maintenance_installment_monthly_payment(float(price_krw), term_months)
        return monthly_payment * 12, monthly_payment, None
    if finance_type == "리스":
        monthly_payment, residual_rate = maintenance_lease_monthly_payment(float(price_krw), term_months)
        return monthly_payment * 12, monthly_payment, residual_rate
    return 0.0, 0.0, None


def maintenance_efficiency_value(car: pd.Series) -> float | None:
    energy_type = maintenance_energy_type(car.get("fuel_type"))
    if energy_type == "electric":
        val = pd.to_numeric(car.get("efficiency_km_kwh"), errors="coerce")
        if pd.notna(val):
            return float(val)
    val = pd.to_numeric(car.get("efficiency_km_l"), errors="coerce")
    if pd.notna(val):
        return float(val)
    return None


def build_maintenance_summary(
    car: pd.Series,
    annual_distance: int,
    finance_type: str,
    finance_term_months: int,
    gasoline_price: int,
    diesel_price: int,
) -> dict[str, float | str | None]:
    efficiency = maintenance_efficiency_value(car)
    fuel_price = maintenance_fuel_price_for_vehicle(car, gasoline_price, diesel_price)
    annual_car_tax = maintenance_annual_car_tax(car)
    annual_finance_cost, monthly_finance_payment, residual_rate = maintenance_finance_annual_cost(
        finance_type, car, finance_term_months
    )
    annual_energy_use = (annual_distance / efficiency) if efficiency and efficiency > 0 else 0.0
    annual_fuel_cost = annual_energy_use * fuel_price
    annual_total_cost = annual_car_tax + annual_finance_cost + annual_fuel_cost
    price_krw = pd.to_numeric(car.get("price_krw"), errors="coerce")
    maintenance_vs_price_pct = (
        annual_total_cost / float(price_krw) * 100 if pd.notna(price_krw) and float(price_krw) > 0 else 0.0
    )
    return {
        "annual_total_cost": annual_total_cost,
        "monthly_average_cost": annual_total_cost / 12,
        "annual_finance_cost": annual_finance_cost,
        "annual_fuel_cost": annual_fuel_cost,
        "annual_car_tax": annual_car_tax,
        "maintenance_vs_price_pct": maintenance_vs_price_pct,
        "monthly_finance_payment": monthly_finance_payment,
        "finance_interest_rate_pct": (
            MAINTENANCE_INSTALLMENT_RATE[finance_term_months] * 100
            if finance_type == "할부"
            else MAINTENANCE_LEASE_RATE[finance_term_months] * 100
            if finance_type == "리스"
            else 0.0
        ),
        "lease_residual_rate_pct": residual_rate * 100 if residual_rate is not None else None,
        "annual_energy_use": annual_energy_use,
        "fuel_price": fuel_price,
        "fuel_price_unit": maintenance_fuel_price_unit(car),
        "efficiency_unit": maintenance_efficiency_unit(car),
        "finance_type": finance_type,
        "finance_term_months": finance_term_months,
    }


def build_maintenance_peer_summary(
    data: pd.DataFrame,
    car: pd.Series,
    annual_distance: int,
    finance_type: str,
    finance_term_months: int,
    gasoline_price: int,
    diesel_price: int,
) -> dict[str, float]:
    peer_df = data[data["segment"].astype(str) == str(car.get("segment", ""))].copy()
    if peer_df.empty:
        return {
            "segment_avg_total": 0.0,
            "segment_avg_ratio": 0.0,
            "segment_vehicle_count": 0,
        }
    totals = []
    ratios = []
    for _, row in peer_df.iterrows():
        summary = build_maintenance_summary(
            row, annual_distance, finance_type, finance_term_months, gasoline_price, diesel_price
        )
        totals.append(float(summary["annual_total_cost"]))
        ratios.append(float(summary["maintenance_vs_price_pct"]))
    return {
        "segment_avg_total": float(pd.Series(totals).mean()),
        "segment_avg_ratio": float(pd.Series(ratios).mean()),
        "segment_vehicle_count": int(len(peer_df)),
    }


def render_maintenance_panel(title: str, car: pd.Series, summary: dict[str, float | str | None], peer_summary: dict[str, float]) -> None:
    st.markdown(f"#### {title}")
    st.caption(f"{car['maker']} {car['model']} | {car['trim']} | {summary['finance_type']}")
    delta_total = float(summary["annual_total_cost"]) - float(peer_summary["segment_avg_total"])
    delta_ratio = float(summary["maintenance_vs_price_pct"]) - float(peer_summary["segment_avg_ratio"])

    ratio_favorable = delta_ratio <= 0
    total_favorable = delta_total <= 0
    ratio_class = "maintenance-gap-good" if ratio_favorable else "maintenance-gap-bad"
    total_class = "maintenance-gap-good" if total_favorable else "maintenance-gap-bad"
    ratio_word = "낮음" if ratio_favorable else "높음"
    total_word = "낮음" if total_favorable else "높음"
    ratio_arrow = "▼" if ratio_favorable else "▲"
    total_arrow = "▼" if total_favorable else "▲"

    row1 = st.columns(2)
    with row1[0]:
        render_stat_tile("연간 총 유지비", format_krw(float(summary["annual_total_cost"])))
    with row1[1]:
        render_stat_tile("월 평균 비용", format_krw(float(summary["monthly_average_cost"]) * 12 / 12))
    row2 = st.columns(2)
    with row2[0]:
        render_stat_tile("유지비 / 차량 가격", f"{float(summary['maintenance_vs_price_pct']):.2f}%")
        st.markdown(
            f"""
            <div class="maintenance-gap-inline {ratio_class}">
                <span class="maintenance-gap-arrow">{ratio_arrow}</span>
                동급 평균 대비 {abs(delta_ratio):.2f}%p {ratio_word}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with row2[1]:
        render_stat_tile("동급 평균 연간 유지비", format_krw(float(peer_summary["segment_avg_total"])))
        st.markdown(
            f"""
            <div class="maintenance-gap-inline {total_class}">
                <span class="maintenance-gap-arrow">{total_arrow}</span>
                선택 차량 기준 {format_krw(abs(delta_total))} {total_word}
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_maintenance_compare_figure(car_a: pd.Series, summary_a: dict[str, float | str | None], car_b: pd.Series, summary_b: dict[str, float | str | None]) -> go.Figure:
    labels = [
        "연간 총 유지비",
        "월 평균 비용",
        "연간 금융비용",
        "연간 연료비",
        "연간 자동차세",
    ]
    values_a = [
        float(summary_a["annual_total_cost"]),
        float(summary_a["monthly_average_cost"]),
        float(summary_a["annual_finance_cost"]),
        float(summary_a["annual_fuel_cost"]),
        float(summary_a["annual_car_tax"]),
    ]
    values_b = [
        float(summary_b["annual_total_cost"]),
        float(summary_b["monthly_average_cost"]),
        float(summary_b["annual_finance_cost"]),
        float(summary_b["annual_fuel_cost"]),
        float(summary_b["annual_car_tax"]),
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=str(car_a["display_name"]), x=labels, y=values_a, marker_color="#2563eb"))
    fig.add_trace(go.Bar(name=str(car_b["display_name"]), x=labels, y=values_b, marker_color="#dc2626"))
    fig.update_layout(
        barmode="group",
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis_title="비용 (원)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
    )
    return fig


def build_maintenance_detail_table(
    car_a: pd.Series,
    summary_a: dict[str, float | str | None],
    peer_a: dict[str, float],
    car_b: pd.Series,
    summary_b: dict[str, float | str | None],
    peer_b: dict[str, float],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"계산 지표": "차량", "차량 A": str(car_a["display_name"]), "차량 B": str(car_b["display_name"])},
            {"계산 지표": "차량 가격", "차량 A": format_krw(float(car_a["price_krw"])), "차량 B": format_krw(float(car_b["price_krw"]))},
            {"계산 지표": "구매 방식", "차량 A": str(summary_a["finance_type"]), "차량 B": str(summary_b["finance_type"])},
            {"계산 지표": "금융 기간", "차량 A": f"{int(summary_a['finance_term_months'])}개월" if summary_a['finance_type'] != '일시불' else '-', "차량 B": f"{int(summary_b['finance_term_months'])}개월" if summary_b['finance_type'] != '일시불' else '-'},
            {"계산 지표": "예상 월 납입금", "차량 A": f"{float(summary_a['monthly_finance_payment']):,.0f}원" if summary_a['finance_type'] != '일시불' else '-', "차량 B": f"{float(summary_b['monthly_finance_payment']):,.0f}원" if summary_b['finance_type'] != '일시불' else '-'},
            {"계산 지표": "연간 자동차세", "차량 A": f"{float(summary_a['annual_car_tax']):,.0f}원", "차량 B": f"{float(summary_b['annual_car_tax']):,.0f}원"},
            {"계산 지표": "연간 금융비용", "차량 A": f"{float(summary_a['annual_finance_cost']):,.0f}원", "차량 B": f"{float(summary_b['annual_finance_cost']):,.0f}원"},
            {"계산 지표": "연간 연료비", "차량 A": f"{float(summary_a['annual_fuel_cost']):,.0f}원", "차량 B": f"{float(summary_b['annual_fuel_cost']):,.0f}원"},
            {"계산 지표": "연간 총 유지비", "차량 A": f"{float(summary_a['annual_total_cost']):,.0f}원", "차량 B": f"{float(summary_b['annual_total_cost']):,.0f}원"},
            {"계산 지표": "월 평균 비용", "차량 A": f"{float(summary_a['monthly_average_cost']):,.0f}원", "차량 B": f"{float(summary_b['monthly_average_cost']):,.0f}원"},
            {"계산 지표": "유지비 / 차량 가격", "차량 A": f"{float(summary_a['maintenance_vs_price_pct']):.2f}%", "차량 B": f"{float(summary_b['maintenance_vs_price_pct']):.2f}%"},
            {"계산 지표": "동급 평균 연간 유지비", "차량 A": f"{float(peer_a['segment_avg_total']):,.0f}원", "차량 B": f"{float(peer_b['segment_avg_total']):,.0f}원"},
        ]
    )


def top5_cost_per_100km(row: pd.Series) -> float | None:
    efficiency = maintenance_efficiency_value(row)
    if efficiency is None or efficiency <= 0:
        return None
    fuel_price = maintenance_fuel_price_for_vehicle(
        row,
        TOP5_STANDARD_GASOLINE_PRICE,
        TOP5_STANDARD_DIESEL_PRICE,
    )
    return (100.0 / efficiency) * fuel_price


def top5_annual_maintenance_cost(row: pd.Series) -> float | None:
    summary = build_maintenance_summary(
        row,
        TOP5_STANDARD_ANNUAL_DISTANCE,
        TOP5_STANDARD_FINANCE_TYPE,
        TOP5_STANDARD_FINANCE_TERM_MONTHS,
        TOP5_STANDARD_GASOLINE_PRICE,
        TOP5_STANDARD_DIESEL_PRICE,
    )
    return float(summary["annual_total_cost"])


def top5_driving_performance_score(row: pd.Series) -> float | None:
    power_kw = pd.to_numeric(row.get("power_kw"), errors="coerce")
    torque_nm = pd.to_numeric(row.get("torque_nm"), errors="coerce")
    if pd.isna(power_kw) and pd.isna(torque_nm):
        return None
    power_score = float(power_kw) if pd.notna(power_kw) else 0.0
    torque_score = float(torque_nm) if pd.notna(torque_nm) else 0.0
    return power_score * 0.6 + torque_score * 0.4


def top5_interior_space_score(row: pd.Series) -> float | None:
    width_mm = pd.to_numeric(row.get("width_mm"), errors="coerce")
    height_mm = pd.to_numeric(row.get("height_mm"), errors="coerce")
    wheelbase_mm = pd.to_numeric(row.get("wheelbase_mm"), errors="coerce")
    if pd.isna(width_mm) and pd.isna(height_mm) and pd.isna(wheelbase_mm):
        return None
    width_score = float(width_mm) if pd.notna(width_mm) else 0.0
    height_score = float(height_mm) if pd.notna(height_mm) else 0.0
    wheelbase_score = float(wheelbase_mm) if pd.notna(wheelbase_mm) else 0.0
    return width_score * 0.3 + height_score * 0.2 + wheelbase_score * 0.5


def recommendation_metric_value(row: pd.Series, priority_mode: str) -> float | None:
    if priority_mode == "fuel_cost":
        return top5_cost_per_100km(row)
    if priority_mode == "maintenance_cost":
        return top5_annual_maintenance_cost(row)
    if priority_mode == "driving_performance":
        return top5_driving_performance_score(row)
    if priority_mode == "interior_space":
        return top5_interior_space_score(row)
    return None


def recommendation_metric_label(row: pd.Series, priority_mode: str) -> tuple[str, str]:
    value = recommendation_metric_value(row, priority_mode)
    if value is None:
        return "비교 지표", "데이터 없음"

    if priority_mode == "fuel_cost":
        return "100km 주행 비용", f"{value:,.0f}원"

    if priority_mode == "maintenance_cost":
        return "연간 유지비", f"{value:,.0f}원"

    if priority_mode == "driving_performance":
        power_kw = pd.to_numeric(row.get("power_kw"), errors="coerce")
        torque_nm = pd.to_numeric(row.get("torque_nm"), errors="coerce")
        power_text = f"{float(power_kw):,.0f}kW" if pd.notna(power_kw) else "-"
        torque_text = f"{float(torque_nm):,.0f}N·m" if pd.notna(torque_nm) else "-"
        return "최고출력 · 최대토크", f"{power_text} · {torque_text}"

    width_mm = pd.to_numeric(row.get("width_mm"), errors="coerce")
    height_mm = pd.to_numeric(row.get("height_mm"), errors="coerce")
    wheelbase_mm = pd.to_numeric(row.get("wheelbase_mm"), errors="coerce")
    width_text = f"{float(width_mm):,.0f}mm" if pd.notna(width_mm) else "-"
    height_text = f"{float(height_mm):,.0f}mm" if pd.notna(height_mm) else "-"
    wheelbase_text = f"{float(wheelbase_mm):,.0f}mm" if pd.notna(wheelbase_mm) else "-"
    return "전폭 · 전고 · 휠베이스", f"{width_text} · {height_text} · {wheelbase_text}"


def recommendation_sort_ascending(priority_mode: str) -> bool:
    return priority_mode in {"fuel_cost", "maintenance_cost"}


def normalize_rank_series(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    minimum = numeric.min(skipna=True)
    maximum = numeric.max(skipna=True)
    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(pd.NA, index=values.index, dtype="Float64")
    if maximum == minimum:
        return numeric.apply(lambda v: 1.0 if pd.notna(v) else pd.NA).astype("Float64")
    return ((numeric - minimum) / (maximum - minimum)).astype("Float64")


def build_top5_recommendations(data: pd.DataFrame, budget_range_manwon: tuple[int, int], priority_mode: str) -> pd.DataFrame:
    ranked = data.copy()
    ranked = ranked.dropna(subset=["price_krw"])
    ranked["price_manwon"] = pd.to_numeric(ranked["price_krw"], errors="coerce") / 10000.0
    ranked = ranked[(ranked["price_manwon"] >= budget_range_manwon[0]) & (ranked["price_manwon"] <= budget_range_manwon[1])]
    if priority_mode in {"fuel_cost", "maintenance_cost"}:
        ranked["priority_value"] = ranked.apply(lambda row: recommendation_metric_value(row, priority_mode), axis=1)
    elif priority_mode == "driving_performance":
        power_score = normalize_rank_series(ranked["power_kw"])
        torque_score = normalize_rank_series(ranked["torque_nm"])
        ranked["priority_value"] = power_score * 0.6 + torque_score * 0.4
    else:
        width_score = normalize_rank_series(ranked["width_mm"])
        height_score = normalize_rank_series(ranked["height_mm"])
        wheelbase_score = normalize_rank_series(ranked["wheelbase_mm"])
        ranked["priority_value"] = width_score * 0.3 + height_score * 0.2 + wheelbase_score * 0.5
    ranked = ranked.dropna(subset=["priority_value"])
    ranked = ranked.sort_values(
        by=["priority_value", "price_krw"],
        ascending=[recommendation_sort_ascending(priority_mode), True],
    )
    ranked = ranked.drop_duplicates(subset=["maker", "model"], keep="first")
    return ranked.head(5).reset_index(drop=True)


def render_top5_cards(recommended: pd.DataFrame, priority_mode: str) -> None:
    if recommended.empty:
        st.markdown('<div class="recommend-empty">현재 조건으로 추천 TOP 5를 만들 수 없습니다. 예산이나 필터를 조금 넓혀보세요.</div>', unsafe_allow_html=True)
        return
    cols = st.columns(5)
    for idx, (_, row) in enumerate(recommended.iterrows(), start=1):
        metric_label, metric_value = recommendation_metric_label(row, priority_mode)
        with cols[idx - 1]:
            st.markdown(
                f"""
                <div class="recommend-card">
                    <div class="recommend-rank">{idx:02d}</div>
                    <div class="recommend-brand">{html.escape(str(row['maker']))}</div>
                    <div class="recommend-model">{html.escape(str(row['model']))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            image_source = resolve_image_source(row.get("image_url"))
            if image_source:
                st.image(image_source, use_container_width=True)
            else:
                st.markdown('<div class="car-image-placeholder">이미지 데이터 없음</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="recommend-card">
                    <div class="recommend-score">가격 {html.escape(format_krw(float(row['price_krw'])))}</div>
                    <div class="recommend-meta">{html.escape(metric_label)} 기준 추천</div>
                    <div class="recommend-meta">{html.escape(metric_value)}</div>
                    <div class="recommend-meta">{html.escape(str(row.get('segment', '')))} | {html.escape(str(row.get('fuel_type', '')))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

        :root {
            --ink: #171b28;
            --muted: #697385;
            --line: #dde5f0;
            --line-strong: #cfd9e8;
            --brand: #2f6df6;
            --brand-dark: #1d57d8;
            --brand-soft: #edf3ff;
            --accent: #ffc94d;
            --panel-bg: #f4f7fb;
            --card-bg: #ffffff;
            --soft-bg: #eff3f9;
            --ok: #1ea97d;
            --bad: #ec4c6a;
            --shadow-lg: 0 24px 54px rgba(39, 61, 108, 0.14);
            --shadow-md: 0 16px 34px rgba(39, 61, 108, 0.09);
            --shadow-sm: 0 10px 24px rgba(39, 61, 108, 0.06);
        }

        html, body, [class*="css"] {
            font-family: "Noto Sans KR", "SUIT", "Pretendard", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(1200px 520px at 100% -15%, rgba(249, 115, 22, 0.07), transparent 62%),
                radial-gradient(1200px 520px at -5% -20%, rgba(15, 76, 129, 0.12), transparent 58%),
                linear-gradient(180deg, #f6f8fc 0%, #edf2f8 100%);
        }

        .main .block-container {
            max-width: 1320px;
            padding-top: 1.1rem;
            padding-bottom: 2.2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(250,252,255,0.98) 100%);
            border-right: 1px solid #dde5ef;
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.65);
        }

        [data-testid="stSidebar"] * {
            font-family: "Noto Sans KR", "SUIT", "Pretendard", sans-serif;
        }

        [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }

        label[data-testid="stWidgetLabel"] p {
            color: #202738;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-bottom: 0.25rem;
        }

        div[data-baseweb="select"] > div,
        div[data-testid="stTextInputRootElement"] > div,
        [data-baseweb="base-input"] {
            background: #ffffff;
            border: 1px solid #d7dfeb;
            border-radius: 14px;
            min-height: 48px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
        }

        div[data-baseweb="select"] > div:hover,
        div[data-testid="stTextInputRootElement"] > div:hover,
        [data-baseweb="base-input"]:hover {
            border-color: var(--brand);
            box-shadow: 0 0 0 4px rgba(47, 109, 246, 0.08);
        }

        div[data-baseweb="select"] input,
        div[data-baseweb="select"] span,
        div[data-testid="stTextInputRootElement"] input {
            color: #1d2433;
        }

        [data-testid="stSidebar"] .stButton > button {
            min-height: 48px;
            border-radius: 16px;
            border: 1px solid var(--line);
            background: #ffffff;
            color: #2c3445;
            font-weight: 800;
            box-shadow: var(--shadow-sm);
            transition: all 0.18s ease;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--brand);
            color: var(--brand);
            transform: translateY(-1px);
        }

        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, var(--brand) 0%, var(--brand-dark) 100%);
            border-color: transparent;
            color: #ffffff;
            box-shadow: 0 14px 28px rgba(47, 109, 246, 0.28);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dce4ef !important;
            border-radius: 22px !important;
            background: var(--card-bg);
            box-shadow: var(--shadow-md);
        }

        .title-wrap {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #dfe6f1;
            border-radius: 22px;
            padding: 18px 24px 16px;
            margin-bottom: 18px;
            box-shadow: var(--shadow-sm);
        }

        .title-kicker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            background: var(--brand-soft);
            color: var(--brand);
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .title-main {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            color: #171b28;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            line-height: 1.2;
            margin: 0;
        }

        .title-sub {
            color: #6b7587;
            font-size: 0.96rem;
            line-height: 1.58;
            margin: 8px 0 0;
            max-width: 980px;
        }

        .section-title {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin: 4px 0 2px;
            color: #10243a;
        }

        .sidebar-switch-title {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 11px;
            border-radius: 999px;
            background: #eef4ff;
            font-size: 0.82rem;
            font-weight: 800;
            color: var(--brand);
            margin-bottom: 0.7rem;
        }

        .sidebar-gap {
            height: 0.55rem;
        }

        .maintenance-gap-inline {
            margin-top: 8px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.84rem;
            font-weight: 700;
            padding: 4px 0 0;
        }

        .maintenance-gap-good {
            color: #0f9f6e;
        }

        .maintenance-gap-bad {
            color: #e11d48;
        }

        .maintenance-gap-arrow {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 0.95rem;
            font-weight: 800;
        }

        .top5-empty {
            text-align: center;
            padding: 64px 24px;
            border: 1px dashed #d0d9e7;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,251,255,0.96) 100%);
            color: #64748b;
            font-weight: 700;
            box-shadow: var(--shadow-sm);
        }

        .vehicle-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .vehicle-label {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 1.55rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.01em;
            color: #0f1d33;
        }

        .vehicle-chip {
            display: inline-flex;
            align-items: center;
            padding: 7px 11px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            line-height: 1;
            white-space: nowrap;
        }

        .vehicle-chip-ev {
            color: #215fd7;
            background: #eef4ff;
            border: 1px solid #c9dbfd;
        }

        .vehicle-chip-ice {
            color: #8c6118;
            background: #fff7e4;
            border: 1px solid #ffe4a9;
        }

        .vehicle-name {
            margin: 8px 0 10px;
            color: var(--muted);
            font-weight: 500;
            line-height: 1.5;
            min-height: 44px;
        }

        div[data-testid="stImage"] {
            min-height: 300px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 4px;
            margin-bottom: 6px;
            border-radius: 20px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        }

        div[data-testid="stImage"] img {
            width: 100% !important;
            max-width: 100% !important;
            max-height: 290px !important;
            object-fit: contain !important;
            margin: 0 auto !important;
        }

        .car-image-placeholder {
            min-height: 300px;
            height: 300px;
            border: 1px dashed #cfd9e8;
            border-radius: 20px;
            background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
            color: #64748b;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-top: 4px;
            margin-bottom: 6px;
        }

        .stat-tile {
            background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
            border: 1px solid #dde6f1;
            border-radius: 18px;
            padding: 12px 14px;
            min-height: 102px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 6px;
            width: 100%;
            margin-top: 10px;
            box-shadow: 0 10px 22px rgba(39, 61, 108, 0.05);
        }

        .stat-label {
            font-size: 0.81rem;
            line-height: 1.25;
            color: #5a667a;
            font-weight: 700;
            min-height: 20px;
            letter-spacing: 0.01em;
        }

        .stat-value {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: clamp(0.94rem, 0.5vw + 0.58rem, 1.16rem);
            line-height: 1.18;
            font-weight: 700;
            color: #111827;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.005em;
            white-space: normal;
            word-break: keep-all;
            overflow-wrap: anywhere;
            max-width: 100%;
        }

        .stat-value.small {
            font-size: clamp(0.88rem, 0.45vw + 0.54rem, 1.06rem);
        }

        .stat-value.tiny {
            font-size: clamp(0.82rem, 0.38vw + 0.5rem, 0.98rem);
        }

        .pct-card {
            border: 1px solid #dce4ef;
            border-radius: 18px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            padding: 12px 12px 13px;
            min-height: 116px;
            box-shadow: 0 10px 22px rgba(39, 61, 108, 0.05);
        }

        .pct-theme-a {
            box-shadow: inset 0 0 0 2px rgba(47, 109, 246, 0.08), 0 10px 22px rgba(39, 61, 108, 0.05);
        }

        .pct-theme-b {
            box-shadow: inset 0 0 0 2px rgba(236, 76, 106, 0.08), 0 10px 22px rgba(39, 61, 108, 0.05);
        }

        .pct-title {
            font-size: 0.8rem;
            color: #516076;
            font-weight: 700;
            margin-bottom: 6px;
            min-height: 18px;
            line-height: 1.2;
        }

        .pct-value {
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-size: 1.22rem;
            color: #0f172a;
            font-weight: 800;
            line-height: 1;
            display: flex;
            align-items: baseline;
            gap: 3px;
            margin-bottom: 8px;
        }

        .pct-unit {
            font-size: 0.66em;
            color: #4b5563;
        }

        .pct-track {
            width: 100%;
            height: 8px;
            border-radius: 999px;
            background: #e6edf8;
            overflow: hidden;
        }

        .pct-fill {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #4d88ff 0%, #2f6df6 100%);
        }

        .pct-theme-b .pct-fill {
            background: linear-gradient(90deg, #ff7f97 0%, #ec4c6a 100%);
        }

        .pct-bias {
            margin-top: 7px;
            font-size: 0.73rem;
            color: #667488;
            font-weight: 600;
            line-height: 1.2;
        }

        div[data-testid="stDataFrame"] {
            background: var(--card-bg);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 8px 8px 6px;
            box-shadow: var(--shadow-sm);
        }

        div[data-testid="stPlotlyChart"] {
            background: var(--card-bg);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 10px 10px 2px;
            box-shadow: var(--shadow-sm);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #dce4ef;
            border-radius: 18px;
            padding: 12px 14px;
            box-shadow: var(--shadow-sm);
        }

        div[data-testid="stMetricLabel"] p {
            color: #6b7588;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: #151b2b;
            font-family: "Montserrat", "Noto Sans KR", sans-serif;
            font-weight: 800;
        }

        @media (max-width: 1024px) {
            .main .block-container {
                margin-top: 0.7rem;
                border-radius: 22px;
            }
            .title-main {
                font-size: 1.7rem;
            }
        }
        </style>
        <div class="title-wrap">
            <div class="title-kicker">Dashboard</div>
            <h1 class="title-main">Compare Cars, Choose Better</h1>
            <p class="title-sub">
                차량 비교, 유지비 분석, 추천 라인업을 한 화면 흐름 안에서 더 직관적으로 볼 수 있도록
                카드 중심 자동차 대시보드 스타일로 정리했습니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    inject_dashboard_extension_css()

    all_cars_mtime = ALL_CARS_DASHBOARD_CSV.stat().st_mtime if ALL_CARS_DASHBOARD_CSV.exists() else None
    all_cars_df = load_all_cars_dashboard_data(ALL_CARS_DASHBOARD_CSV, file_mtime=all_cars_mtime)
    sample_df = load_sample_data(SAMPLE_DATA_PATH)

    if not all_cars_df.empty:
        base_df = all_cars_df.copy()
    else:
        base_df = sample_df.copy()

    if base_df.empty:
        st.stop()

    scored_df = add_normalized_columns(base_df)

    view_options = ["비교 분석", "유지비 분석", "TOP 5 추천"]
    if "dashboard_view" not in st.session_state:
        st.session_state.dashboard_view = view_options[0]

    segment_options = sorted(scored_df["segment"].dropna().astype(str).unique().tolist())
    fuel_options = sorted(scored_df["fuel_type"].dropna().astype(str).unique().tolist())
    maker_options = sorted(scored_df["maker"].dropna().astype(str).unique().tolist())
    min_budget = int(scored_df["price_krw"].min() // 10000)
    max_budget = int(scored_df["price_krw"].max() // 10000)
    default_budget = (max(min_budget, 2000), min(max_budget, 6000))
    if default_budget[0] > default_budget[1]:
        default_budget = (min_budget, max_budget)

    with st.sidebar:
        st.markdown('<div class="sidebar-switch-title">뷰 전환</div>', unsafe_allow_html=True)
        for label in view_options:
            if st.button(
                label,
                use_container_width=True,
                type="primary" if st.session_state.dashboard_view == label else "secondary",
                key=f"view_switch_{label}",
            ):
                st.session_state.dashboard_view = label
                st.rerun()
        st.markdown('<div class="sidebar-gap"></div>', unsafe_allow_html=True)

        current_view = st.session_state.dashboard_view

        if current_view == "유지비 분석":
            st.header("공통 비용 가정")
            render_synced_slider_number_input(
                "연간 주행거리 (km)",
                3000,
                50000,
                15000,
                1000,
                "maintenance_annual_distance_sidebar",
                "maintenance_annual_distance_input",
            )
            render_synced_slider_number_input(
                "가솔린 가격 (원/L)",
                1300,
                2100,
                MAINTENANCE_DEFAULT_GASOLINE_PRICE,
                50,
                "maintenance_gasoline_sidebar",
                "maintenance_gasoline_input",
            )
            render_synced_slider_number_input(
                "디젤 가격 (원/L)",
                1300,
                2100,
                MAINTENANCE_DEFAULT_DIESEL_PRICE,
                50,
                "maintenance_diesel_sidebar",
                "maintenance_diesel_input",
            )
            st.caption("전기차와 수소차는 각각 기본 단가를 적용해 계산합니다.")
            st.info("전기 339원/kWh, 수소 10,228원/kg 기준입니다.")
            st.caption(MAINTENANCE_TAX_REFERENCE_TEXT)
        elif current_view == "TOP 5 추천":
            st.markdown("<h2 style='margin-bottom:10px; letter-spacing:-1px;'>TOP 5 추천</h2>", unsafe_allow_html=True)
            render_synced_budget_range_input(
                "예산 범위 (만원)",
                min_budget,
                max_budget,
                default_budget,
                100,
                "top5_budget_sidebar",
                "top5_budget_min_input",
                "top5_budget_max_input",
            )
            st.multiselect("제조사", maker_options, default=[], placeholder="제조사 선택", key="top5_makers_sidebar")
            st.multiselect("차급", segment_options, default=[], placeholder="차급 선택", key="top5_segments_sidebar")
            st.multiselect("연료", fuel_options, default=[], placeholder="연료 선택", key="top5_fuels_sidebar")
            st.selectbox("추천 기준", list(TOP5_PRIORITY_OPTIONS.keys()), key="top5_priority_sidebar")
            if st.button("필터 초기화", use_container_width=True, key="top5_reset_sidebar"):
                for state_key, default_value in {
                    "top5_makers_sidebar": [],
                    "top5_segments_sidebar": [],
                    "top5_fuels_sidebar": [],
                    "top5_priority_sidebar": list(TOP5_PRIORITY_OPTIONS.keys())[0],
                    "top5_budget_sidebar": default_budget,
                    "top5_budget_min_input": default_budget[0],
                    "top5_budget_max_input": default_budget[1],
                }.items():
                    st.session_state[state_key] = default_value
                st.rerun()

    current_view = st.session_state.dashboard_view
    if current_view == "비교 분석":
        filtered = scored_df.reset_index(drop=True)
        if len(filtered) < 2:
            st.warning("비교 분석을 위해 최소 2대 이상의 차량이 필요합니다.")
            return

        st.markdown('<p class="section-title">차량 선택</p>', unsafe_allow_html=True)
        st.caption("차량 A와 차량 B를 선택하면 핵심 제원, 비교 차트, 구매 인사이트를 한 번에 확인할 수 있습니다.")

        default_a, default_b = resolve_selected_car_defaults(filtered)

        pick_col_a, pick_col_b = st.columns(2)
        with pick_col_a:
            with st.container(border=True):
                st.markdown("#### 차량 A")
                car_a = car_picker(filtered, key_prefix="shared_car_a", default_display_name=default_a)
        with pick_col_b:
            with st.container(border=True):
                st.markdown("#### 차량 B")
                car_b = car_picker(filtered, key_prefix="shared_car_b", default_display_name=default_b)

        if str(car_a["display_name"]) == str(car_b["display_name"]):
            st.warning("차량 A와 차량 B가 같습니다. 서로 다른 차량을 선택해주세요.")
            return

        sync_selected_car_state(car_a, car_b)

        view_col_a, view_col_b = st.columns(2)
        with view_col_a:
            render_car_panel(car_a, "차량 A")
        with view_col_b:
            render_car_panel(car_b, "차량 B")

        st.markdown('<p class="section-title">핵심 제원 비교</p>', unsafe_allow_html=True)
        comparison_df = build_comparison_table(car_a, car_b)
        if comparison_df.empty:
            st.info("비교할 수 있는 공통 제원 데이터가 부족합니다.")
        else:
            st.dataframe(style_comparison(comparison_df), use_container_width=True, hide_index=True)

        chart_col_1, chart_col_2 = st.columns(2)
        with chart_col_1:
            st.markdown('<p class="section-title">레이더 차트</p>', unsafe_allow_html=True)
            radar_fig = build_radar(car_a, car_b)
            if radar_fig is None:
                st.info("레이더 차트를 그리기에 충분한 데이터가 없습니다.")
            else:
                st.plotly_chart(radar_fig, use_container_width=True)
        with chart_col_2:
            st.markdown('<p class="section-title">항목별 우세 비교</p>', unsafe_allow_html=True)
            diff_fig = build_diff_chart(car_a, car_b)
            if diff_fig is None:
                st.info("항목별 차이 데이터를 만들 수 없습니다.")
            else:
                st.plotly_chart(diff_fig, use_container_width=True)

        st.markdown('<p class="section-title">시장 포지셔닝 맵</p>', unsafe_allow_html=True)
        ctrl_col_1, ctrl_col_2 = st.columns([5, 2])
        with ctrl_col_1:
            scope_mode = st.radio("비교 범위", options=["전체 시장", "동일 차급/연료", "동일 제조사 비교"], horizontal=True, key="positioning_scope_mode_v2")
        with ctrl_col_2:
            use_log_x = st.toggle("가격 축 로그", value=False, key="positioning_log_x_v2")
        st.caption("선택한 두 차량의 위치와, 해당 비교군 안에서의 상대적인 좌표를 함께 보여줍니다.")
        positioning_fig = build_market_positioning_map(filtered, car_a, car_b, scope_mode=scope_mode, use_log_x=use_log_x)
        if positioning_fig is None:
            st.info("포지셔닝 맵을 구성할 수 있는 비교 데이터가 부족합니다.")
        else:
            st.plotly_chart(positioning_fig, use_container_width=True)

        st.markdown('<p class="section-title">백분위 카드</p>', unsafe_allow_html=True)
        st.caption("전체 데이터 안에서 각 차량이 어느 정도 위치에 있는지 백분위로 확인할 수 있습니다.")
        pct_col_a, pct_col_b = st.columns(2)
        with pct_col_a:
            items_a, peer_label_a = build_percentile_card_items(scored_df, car_a)
            render_percentile_cards("차량 A 백분위", items_a, peer_label_a, theme="a")
        with pct_col_b:
            items_b, peer_label_b = build_percentile_card_items(scored_df, car_b)
            render_percentile_cards("차량 B 백분위", items_b, peer_label_b, theme="b")

        st.markdown('<p class="section-title">구매 인사이트</p>', unsafe_allow_html=True)
        st.caption("두 차량의 강점이 어떤 항목에서 갈리는지 요약해서 보여줍니다.")
        insight_df = build_buyer_insight_table(car_a, car_b)
        if insight_df.empty:
            st.info("인사이트를 만들 수 있는 데이터가 아직 부족합니다.")
        else:
            winner_column = "우세" if "우세" in insight_df.columns else insight_df.columns[-1]
            win_a = int((insight_df[winner_column] == "차량 A").sum())
            win_b = int((insight_df[winner_column] == "차량 B").sum())
            tie_n = int((insight_df[winner_column] == "동률").sum())

            sum_col_1, sum_col_2, sum_col_3 = st.columns(3)
            with sum_col_1:
                st.metric("차량 A 우세 수", f"{win_a}")
            with sum_col_2:
                st.metric("차량 B 우세 수", f"{win_b}")
            with sum_col_3:
                st.metric("동률 수", f"{tie_n}")

            if win_a > win_b:
                st.success("현재 비교 기준에서는 차량 A가 조금 더 강한 선택지로 보입니다.")
            elif win_b > win_a:
                st.success("현재 비교 기준에서는 차량 B가 조금 더 강한 선택지로 보입니다.")
            else:
                st.info("두 차량의 강점이 꽤 균형 있게 나뉘어 있습니다.")

            st.dataframe(style_insight(insight_df), use_container_width=True, hide_index=True)
            insight_fig = build_insight_advantage_chart(car_a, car_b)
            if insight_fig is not None:
                st.plotly_chart(insight_fig, use_container_width=True)

            waterfall_fig = build_insight_waterfall(car_a, car_b)
            if waterfall_fig is not None:
                st.markdown('<p class="section-title">누적 우세도</p>', unsafe_allow_html=True)
                st.caption("세부 항목이 누적되면서 어느 차량 쪽으로 무게가 실리는지 보여줍니다.")
                st.plotly_chart(waterfall_fig, use_container_width=True)

        st.markdown('<p class="section-title">목적별 추천</p>', unsafe_allow_html=True)
        purpose = st.selectbox("사용 목적", list(PURPOSE_WEIGHTS.keys()))
        score_a, contrib_a = weighted_score(car_a, purpose)
        score_b, contrib_b = weighted_score(car_b, purpose)
        if score_a is None or score_b is None:
            st.info("목적별 점수를 계산하기에 필요한 데이터가 부족합니다.")
        else:
            rec_col_1, rec_col_2, rec_col_3 = st.columns([1, 1, 2])
            with rec_col_1:
                st.metric("차량 A 목적 점수", f"{score_a * 100:.1f}")
            with rec_col_2:
                st.metric("차량 B 목적 점수", f"{score_b * 100:.1f}")
            with rec_col_3:
                if score_a > score_b:
                    top_reasons = ", ".join(purpose_metric_name(key) for key, _ in contrib_a[:2])
                    st.success(f"추천: 차량 A ({top_reasons})")
                elif score_b > score_a:
                    top_reasons = ", ".join(purpose_metric_name(key) for key, _ in contrib_b[:2])
                    st.success(f"추천: 차량 B ({top_reasons})")
                else:
                    st.info("두 차량 모두 비슷한 수준으로 잘 맞습니다.")

    elif current_view == "유지비 분석":
        if len(scored_df) < 2:
            st.warning("유지비 분석을 위해 최소 2대 이상의 차량이 필요합니다.")
            return

        annual_distance = st.session_state.get("maintenance_annual_distance_sidebar", 15000)
        gasoline_price = st.session_state.get("maintenance_gasoline_sidebar", MAINTENANCE_DEFAULT_GASOLINE_PRICE)
        diesel_price = st.session_state.get("maintenance_diesel_sidebar", MAINTENANCE_DEFAULT_DIESEL_PRICE)
        default_a, default_b = resolve_selected_car_defaults(scored_df)

        st.markdown('<p class="section-title">차량 유지비 비교</p>', unsafe_allow_html=True)
        st.caption("두 차량을 직접 선택하고, 구매 방식까지 반영해 연간 유지비를 비교할 수 있습니다.")

        pick_col_a, pick_col_b = st.columns(2)
        with pick_col_a:
            with st.container(border=True):
                st.markdown("#### 차량 A")
                car_a = car_picker(scored_df, key_prefix="shared_car_a", default_display_name=default_a)
                finance_type_a = st.radio("차량 A 구매 방식", ["일시불", "할부", "리스"], key="maintenance_finance_type_a_main", horizontal=True)
                finance_term_a = st.selectbox("차량 A 금융 기간 (개월)", MAINTENANCE_FINANCE_TERM_OPTIONS, index=2, key="maintenance_finance_term_a_main", disabled=finance_type_a == "일시불")
        with pick_col_b:
            with st.container(border=True):
                st.markdown("#### 차량 B")
                car_b = car_picker(scored_df, key_prefix="shared_car_b", default_display_name=default_b)
                finance_type_b = st.radio("차량 B 구매 방식", ["일시불", "할부", "리스"], key="maintenance_finance_type_b_main", horizontal=True)
                finance_term_b = st.selectbox("차량 B 금융 기간 (개월)", MAINTENANCE_FINANCE_TERM_OPTIONS, index=2, key="maintenance_finance_term_b_main", disabled=finance_type_b == "일시불")

        if str(car_a["display_name"]) == str(car_b["display_name"]):
            st.warning("차량 A와 차량 B가 같습니다. 서로 다른 차량을 선택해주세요.")
            return

        sync_selected_car_state(car_a, car_b)

        image_col_a, image_col_b = st.columns(2)
        with image_col_a:
            render_car_panel(car_a, "차량 A")
        with image_col_b:
            render_car_panel(car_b, "차량 B")

        maintenance_summary_a = build_maintenance_summary(car_a, annual_distance, finance_type_a, finance_term_a, gasoline_price, diesel_price)
        maintenance_summary_b = build_maintenance_summary(car_b, annual_distance, finance_type_b, finance_term_b, gasoline_price, diesel_price)
        maintenance_peer_a = build_maintenance_peer_summary(scored_df, car_a, annual_distance, finance_type_a, finance_term_a, gasoline_price, diesel_price)
        maintenance_peer_b = build_maintenance_peer_summary(scored_df, car_b, annual_distance, finance_type_b, finance_term_b, gasoline_price, diesel_price)

        maintenance_col_a, maintenance_col_b = st.columns(2)
        with maintenance_col_a:
            with st.container(border=True):
                render_maintenance_panel("차량 A 유지비", car_a, maintenance_summary_a, maintenance_peer_a)
        with maintenance_col_b:
            with st.container(border=True):
                render_maintenance_panel("차량 B 유지비", car_b, maintenance_summary_b, maintenance_peer_b)

        st.markdown('<p class="section-title">유지비 비교 차트</p>', unsafe_allow_html=True)
        maintenance_fig = build_maintenance_compare_figure(car_a, maintenance_summary_a, car_b, maintenance_summary_b)
        st.plotly_chart(maintenance_fig, use_container_width=True)

        with st.expander("유지비 계산 지표 보기", expanded=False):
            maintenance_table = build_maintenance_detail_table(car_a, maintenance_summary_a, maintenance_peer_a, car_b, maintenance_summary_b, maintenance_peer_b)
            st.dataframe(maintenance_table, use_container_width=True, hide_index=True)

    else:
        selected_brands = st.session_state.get("top5_makers_sidebar", [])
        selected_segments = st.session_state.get("top5_segments_sidebar", [])
        selected_fuels = st.session_state.get("top5_fuels_sidebar", [])
        price_range = st.session_state.get("top5_budget_sidebar")
        priority_label = st.session_state.get("top5_priority_sidebar", list(TOP5_PRIORITY_OPTIONS.keys())[0])
        top5_priority_mode = TOP5_PRIORITY_OPTIONS[priority_label]

        if not selected_brands:
            st.markdown('<div class="top5-empty">제조사를 먼저 선택하면 추천 결과를 보여드립니다.</div>', unsafe_allow_html=True)
            return

        top5_filtered = scored_df.copy()
        if selected_brands:
            top5_filtered = top5_filtered[top5_filtered["maker"].isin(selected_brands)]
        if selected_segments:
            top5_filtered = top5_filtered[top5_filtered["segment"].isin(selected_segments)]
        if selected_fuels:
            top5_filtered = top5_filtered[top5_filtered["fuel_type"].isin(selected_fuels)]

        budget_min, budget_max = price_range if price_range is not None else (int(top5_filtered["price_krw"].min() // 10000), int(top5_filtered["price_krw"].max() // 10000))
        recommended_df = build_top5_recommendations(top5_filtered, (budget_min, budget_max), top5_priority_mode)

        st.markdown('<p class="section-title">추천 라인업 TOP 5</p>', unsafe_allow_html=True)
        st.caption(
            "연비는 100km 주행 비용, 경제성은 연간 유지비 기준으로 계산합니다. "
            "가솔린/디젤은 1,950원 기준이며, 경제성은 연 15,000km · 일시불 기준 유지비를 사용합니다."
        )
        render_top5_cards(recommended_df, top5_priority_mode)


if __name__ == "__main__":
    main()
