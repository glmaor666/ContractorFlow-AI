from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd


@dataclass(frozen=True)
class IngestionConfig:
    xlsx_path: Path
    sheet_name: Optional[str] = None
    # Dynamic header detection: we'll scan the first N rows of each sheet.
    header_scan_rows: int = 40

    # Structural/grouping columns are the ONLY columns eligible for forward-fill.
    # This prevents accidental semantic changes in transactional columns (status, dates, etc.).
    grouping_columns: tuple[str, ...] = ("Contractor Name",)

    # Optional semantic fill: if provided, fill empty status cells with this value.
    # Leave as None to keep missing values as NaN/NA.
    fill_missing_status_with: Optional[str] = None

    # Column name (or common variants) that should receive the optional status fill.
    status_column_candidates: tuple[str, ...] = ("Status", "סטטוס")


def _as_missing(series: pd.Series) -> pd.Series:
    """Convert blank/whitespace-only strings to missing values (pd.NA)."""
    s = series.astype("string")
    # Some Excel exports include hidden RTL/LTR marks that break equality/stripping.
    # This is a hack to get around the issue.
    s = s.str.replace("\u200e", "", regex=False).str.replace("\u200f", "", regex=False)
    # Replace blank/whitespace-only strings with missing values.
    return s.replace(r"^\s*$", pd.NA, regex=True)


def _score_header_row(values: Sequence[object]) -> float:
    """
    Heuristic score for selecting the header row from a preview grid.

    A good header row typically:
    - has many non-empty cells (lots of column names)
    - is mostly text (not mostly numbers/dates)
    - has high uniqueness (headers aren't all the same value)
    """
    non_empty = 0
    textish = 0
    numericish = 0
    uniques: set[str] = set()

    for v in values:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        s = str(v).strip()
        if not s:
            continue
        non_empty += 1
        uniques.add(s.lower())
        # Very rough numeric detection; Excel metadata rows often include dates/numbers too,
        # but true headers are overwhelmingly text.
        try:
            float(s.replace(",", ""))
            numericish += 1
        except ValueError:
            textish += 1

    if non_empty == 0:
        return -1e9

    unique_ratio = len(uniques) / max(non_empty, 1)
    # Weight: prefer more non-empty and more text; penalize numeric-heavy rows.
    return (non_empty * 2.0) + (textish * 1.5) + (unique_ratio * 3.0) - (numericish * 2.5)


def detect_header_row(
    xlsx_path: Path,
    sheet: str,
    *,
    scan_rows: int = 40,
) -> int:
    """
    Find the most likely header row in a sheet that contains metadata/logos above the table.

    Implementation:
    - Read a small preview (top `scan_rows` rows) with `header=None`, so we get raw cells.
    - Score each preview row with `_score_header_row`.
    - Pick the best scoring row as the header index.
    """
    preview = pd.read_excel(
        xlsx_path,
        sheet_name=sheet,
        header=None,
        nrows=scan_rows,
        dtype="string",
        engine="openpyxl",
    )

    best_idx = 0
    best_score = -1e9
    for i in range(len(preview.index)):
        score = _score_header_row(preview.iloc[i].tolist())
        if score > best_score:
            best_score = score
            best_idx = int(i)

    # Production logging (commented out for now; keep prints for local testing):
    # import logging
    # logging.info("Detected header row %s for sheet '%s'", best_idx, sheet)
    return best_idx


def read_sheet_with_dynamic_header(
    config: IngestionConfig,
    *,
    sheet: str,
) -> pd.DataFrame:
    """
    Step 1 (Technical Data Flow): load the raw .xlsx into a DataFrame.

    Notes:
    - Real-world sheets often have floating headers (metadata rows above the table).
      We detect the header row dynamically per sheet.
    - We read everything as text initially to avoid pandas guessing types too early.
    """
    header_row = detect_header_row(
        config.xlsx_path, sheet, scan_rows=config.header_scan_rows
    )

    df = pd.read_excel(
        config.xlsx_path,
        sheet_name=sheet,
        header=header_row,
        dtype="string",
        engine="openpyxl",
    )

    # Normalize column labels a bit (whitespace is a common source of surprises).
    df.columns = [
        str(c).replace("\u200e", "").replace("\u200f", "").strip() for c in df.columns
    ]

    # Drop columns that are completely empty (common when the sheet has a wide template).
    df = df.dropna(axis=1, how="all")
    return df


def structural_preprocess_step2(
    df: pd.DataFrame,
    *,
    grouping_columns: Iterable[str] = ("Contractor Name",),
    status_column_candidates: Iterable[str] = ("Status", "סטטוס"),
    fill_missing_status_with: Optional[str] = None,
) -> pd.DataFrame:
    """
    Step 2 (Technical Data Flow): structural pre-processing.

    - Drop completely empty rows.
    - Forward-fill ONLY the grouping columns (e.g., Contractor Name) to resolve merged cells.

    Crucial business logic:
    - We intentionally do NOT forward-fill transactional columns like status/progress/dates.
      Empty cells there are meaningful (often "not performed yet").
    """
    if df.empty:
        return df.copy()

    out = df.copy()

    # Drop rows where *every* cell is missing.
    out = out.dropna(how="all").reset_index(drop=True)

    # Build a case-insensitive lookup for user-provided grouping/status candidate names.
    lowered = {
        str(c).replace("\u200e", "").replace("\u200f", "").strip().lower(): c
        for c in out.columns
    }

    # Targeted forward-fill: only for grouping columns.
    for desired in grouping_columns:
        key = str(desired).strip().lower()
        if key not in lowered:
            # If the sheet doesn't have this grouping column, just skip it (multi-sheet reality).
            continue
        col = str(lowered[key])
        out[col] = _as_missing(out[col]).ffill()

    # Optional semantic fill for status: keep NaN by default unless configured.
    if fill_missing_status_with is not None:
        for cand in status_column_candidates:
            key = str(cand).strip().lower()
            if key in lowered:
                col = str(lowered[key])
                out[col] = _as_missing(out[col]).fillna(fill_missing_status_with)
                break

    return out


def get_schema_context(df: pd.DataFrame) -> str:
    """
    Step 3 (Technical Data Flow): schema context payload for the LLM.

    Returns a JSON string containing:
    - columns: list of column names
    - sample_rows: 3 representative rows with non-null data
    """
    columns = [str(c) for c in df.columns]
    if df.empty:
        payload = {"columns": columns, "sample_rows": []}
        return json.dumps(payload, ensure_ascii=False, indent=2)

    # Prefer rows that actually contain values (not all-null), and pick the "most filled" ones.
    non_empty = df.dropna(how="all")
    if non_empty.empty:
        payload = {"columns": columns, "sample_rows": []}
        return json.dumps(payload, ensure_ascii=False, indent=2)

    row_scores = non_empty.notna().sum(axis=1).sort_values(ascending=False)
    sample = non_empty.loc[row_scores.index[:3]]

    # Make the JSON stable and easy to inspect: convert pandas missing values to None.
    sample_rows = sample.where(sample.notna(), None).to_dict(orient="records")

    payload = {"columns": columns, "sample_rows": sample_rows}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_args(argv: Optional[list[str]] = None) -> IngestionConfig:
    parser = argparse.ArgumentParser(description="ContractorFlow AI ingestion (Step 1–2).")
    parser.add_argument("xlsx", type=str, help="Path to the raw .xlsx report")
    parser.add_argument(
        "--scan-rows",
        dest="header_scan_rows",
        type=int,
        default=40,
        help="How many top rows to scan for detecting the header row per sheet",
    )
    parser.add_argument(
        "--grouping-col",
        dest="grouping_columns",
        action="append",
        default=None,
        help=(
            "Grouping column to forward-fill (repeatable). "
            "Example: --grouping-col 'Contractor Name'"
        ),
    )
    parser.add_argument(
        "--fill-missing-status-with",
        dest="fill_missing_status_with",
        default=None,
        help="If set, fills empty status cells with this value (e.g. 'Not Started')",
    )
    args = parser.parse_args(argv)
    return IngestionConfig(
        xlsx_path=Path(args.xlsx),
        header_scan_rows=int(args.header_scan_rows),
        grouping_columns=tuple(args.grouping_columns) if args.grouping_columns else ("Contractor Name",),
        fill_missing_status_with=args.fill_missing_status_with,
    )


def main(argv: Optional[list[str]] = None) -> int:
    config = parse_args(argv)

    # Production logging setup (commented out for now; keep prints for local testing):
    # import logging
    # logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not config.xlsx_path.exists():
        raise FileNotFoundError(f"Excel file not found: {config.xlsx_path}")

    # Multi-sheet iteration: read each sheet, detect its header, and concatenate.
    xls = pd.ExcelFile(config.xlsx_path, engine="openpyxl")
    frames: list[pd.DataFrame] = []
    for sheet in xls.sheet_names:
        df_sheet = read_sheet_with_dynamic_header(config, sheet=sheet)
        if df_sheet.dropna(how="all").empty:
            continue
        # Production logging (commented out for now; keep prints for local testing):
        # logging.info("Ingesting sheet '%s' (%s rows, %s cols)", sheet, len(df_sheet), len(df_sheet.columns))
        df_sheet["Source_Sheet"] = sheet
        df_sheet = structural_preprocess_step2(
            df_sheet,
            grouping_columns=config.grouping_columns,
            status_column_candidates=config.status_column_candidates,
            fill_missing_status_with=config.fill_missing_status_with,
        )
        frames.append(df_sheet)

    df_struct = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # Temporary: show a small preview so you can verify ffill worked.
    # Later steps will hand off headers + first rows to the LLM mapping stage.
    with pd.option_context("display.max_columns", 50, "display.width", 120):
        print(df_struct.head(10))
        # Production logging (commented out for now; keep prints for local testing):
        # logging.info("Preview (first 10 rows):\n%s", df_struct.head(10).to_string(index=False))

    # Step 3: payload we will send to the LLM for schema mapping.
    schema_context = get_schema_context(df_struct)
    print(schema_context)
    # Production logging (commented out for now; keep prints for local testing):
    # logging.info("Schema context payload:\n%s", schema_context)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
