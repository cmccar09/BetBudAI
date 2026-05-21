#!/usr/bin/env python3
"""
run_prompt_with_betfair.py — unified runner (deep research + Betfair snapshots)
- Relaxed gates (min_back 1.2, min_overlay 0.02, auto-relax on)
- keepAlive preflight (via --keepalive_url or --keepalive_cmd)
- EW analysis (uses p_place, ew_places, ew_fraction if present)
- Defensive column alignment & canonicalization (market_name / venue / start_time_dublin)
"""

import os, sys, glob, argparse, subprocess, json
from datetime import date
import pandas as pd
import urllib.request

# ------------------------ HTTP util ------------------------

def _http_get(url: str, headers: dict[str,str] | None = None) -> tuple[int,str]:
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as e:
        return -1, str(e)

# ------------------------ Argparse ------------------------

def build_argparser():
    ap = argparse.ArgumentParser(description="Run racing model with Betfair snapshots (deep research, relaxed)")

    # Model / portfolio args
    ap.add_argument("--probs_csv", type=str, default="./my_probs.csv",
                    help="CSV of model probabilities (from your ML model or generated)")
    ap.add_argument("--auto", action="store_true",
                    help="Auto mode: run snapshot script then compute Top 5")
    ap.add_argument("--bf_script", type=str, default="./betfair_delayed_snapshots.py",
                    help="Path to snapshot script")
    ap.add_argument("--out_csv", type=str, default="./top5.csv",
                    help="Output CSV for Top 5 selections")

    # Saved prompt generation
    ap.add_argument("--use_saved_prompt", action="store_true",
                    help="Run your saved racing prompt first to generate probs_csv")
    ap.add_argument("--prompt_cmd", type=str, default="",
                    help="Custom shell command to generate probs_csv (use {out} token)")
    ap.add_argument("--prompt_workdir", type=str, default=".",
                    help="Working directory for the prompt command")

    # Snapshot pass-through args
    ap.add_argument("--once", action="store_true",
                    help="(snapshot) Single snapshot now")
    ap.add_argument("--snapshots", type=str, default="",
                    help="(snapshot) Comma-separated minutes BEFORE off to snapshot, e.g. '20,10,5,1'")
    ap.add_argument("--market_types", type=str, default="WIN,PLACE",
                    help="(snapshot) Market types, e.g. 'WIN,PLACE'")
    ap.add_argument("--countries", type=str, default="",
                    help="(snapshot) Restrict to countries, e.g. 'GB,IE,US'. Blank = ALL (recommended).")
    ap.add_argument("--window_hours", type=float, default=4.0,
                    help="(snapshot) Window length in hours (now to now+Xh)")
    ap.add_argument("--depth", type=int, default=3,
                    help="(snapshot) Best prices depth")
    ap.add_argument("--outfile_prefix", type=str, default="./snapshots",
                    help="(snapshot) Prefix for scheduled outputs")
    ap.add_argument("--outfile", type=str, default="",
                    help="(snapshot) Explicit output CSV path for --once")
    ap.add_argument("--ts", type=str, default="",
                    help="(snapshot) Timestamp token YYYYMMDD_HHMMSS -> ./snapshots/run_<ts>_once.csv")

    # Keep-alive / auth recovery (preflight only)
    ap.add_argument("--keepalive_cmd", type=str, default="",
                    help="Shell command to refresh Betfair session (runs BEFORE snapshot if provided)")
    ap.add_argument("--keepalive_url", type=str, default="",
                    help="HTTP(s) keep-alive endpoint to call (GET) with headers X-Application and X-Authentication; if set, called BEFORE snapshot")

    # Snapshot fallback controls
    ap.add_argument("--fallback_snapshots", action="store_true",
                    help="If zero markets returned, automatically retry with safer defaults")
    ap.add_argument("--fallback_window_hours", type=float, default=8.0,
                    help="Fallback window length (hours) if initial snapshot is empty")
    ap.add_argument("--fallback_market_types", type=str, default="WIN",
                    help="Fallback market types if initial snapshot is empty (e.g., 'WIN')")

    # Gating / relaxation (RELAXED DEFAULTS)
    ap.add_argument("--min_back", type=float, default=1.2, help="Minimum back price to consider")
    ap.add_argument("--min_overlay", type=float, default=0.02, help="Minimum overlay (e.g., 0.02 = +2%%)")
    ap.add_argument("--relax_if_empty", action="store_true", default=True, help="If no picks, relax overlay down stepwise")
    ap.add_argument("--relax_steps", type=int, default=5, help="How many relax iterations if empty")
    ap.add_argument("--relax_delta", type=float, default=0.01, help="Overlay decrement per relax step")

    # Reporting
    ap.add_argument("--debug_report", type=str, default="",
                    help="Write a markdown debug report explaining filters and counts")
    ap.add_argument("--analysis_report", type=str, default="./top5_analysis.md",
                    help="Write a human-readable Top 5 analysis with Win/EW calls")
    
    # Database integration
    ap.add_argument("--save_to_dynamodb", action="store_true",
                    help="Save selections to DynamoDB SureBetBets table")
    ap.add_argument("--dynamodb_table", type=str, default="SureBetBets",
                    help="DynamoDB table name")
    ap.add_argument("--dynamodb_region", type=str, default="eu-west-1",
                    help="AWS region for DynamoDB")
    return ap

# ------------------------ Utilities ------------------------

def debug(msg: str):
    print(msg, flush=True)

def ensure_parent_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def construct_expected_snapshot_path(ts: str) -> str:
    return f"./snapshots/run_{ts}_once.csv"

def discover_snapshot_path(explicit_outfile: str, ts: str) -> str | None:
    if explicit_outfile:
        return explicit_outfile
    if ts:
        return construct_expected_snapshot_path(ts)
    matches = sorted(glob.glob("./snapshots/run_*_once.csv"))
    return matches[-1] if matches else None

def csv_rows(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f) - 1  # minus header
    except Exception:
        return -1

def _ensure_columns(df, cols, fill=None):
    import pandas as _pd
    if df is None or getattr(df, "empty", True):
        return _pd.DataFrame(columns=cols)
    missing = [c for c in cols if c not in df.columns]
    for c in missing:
        df[c] = fill
    return df.reindex(columns=cols)

def _coalesce_columns(df: pd.DataFrame, bases: list[str]) -> pd.DataFrame:
    """
    For each base name, fill a canonical column from any of:
      base, base_prob, base_snap, or known aliases where applicable.
    """
    import pandas as _pd
    d = df.copy()
    alias_map = {
        "market_name": ["market", "marketname"],
        "venue": ["event_venue", "course", "track"],
        "start_time_dublin": ["market_start_time", "market_start_time_utc", "start_time_local", "start_time"],
        "runner_name": ["runner", "selection_name"],
        "market_id": ["marketid"],
    }
    for base in bases:
        # Build candidate list in priority order
        candidates = [c for c in [base, f"{base}_prob", f"{base}_snap"] if c in d.columns]
        # Add aliases
        for alias in alias_map.get(base, []):
            if alias in d.columns:
                candidates.append(alias)
        if not candidates:
            # Ensure column exists
            if base not in d.columns:
                d[base] = _pd.NA
            continue
        # Start with first candidate, then backfill missing from others
        out = d[candidates[0]]
        for c in candidates[1:]:
            out = out.where(out.notna(), d[c])
        d[base] = out
    return d

def _canonicalize_snapshots(snaps: pd.DataFrame) -> pd.DataFrame:
    """Try to alias common snapshot column variants to canonical names."""
    s = snaps.copy()
    s.columns = [c.strip().lower() for c in s.columns]
    # If canonical columns missing, create from common aliases
    if "market_name" not in s.columns:
        for a in ("market", "marketname"):
            if a in s.columns:
                s["market_name"] = s[a]
                break
    if "venue" not in s.columns:
        for a in ("event_venue", "course", "track"):
            if a in s.columns:
                s["venue"] = s[a]
                break
    if "start_time_dublin" not in s.columns:
        for a in ("market_start_time", "market_start_time_utc", "start_time_local", "start_time"):
            if a in s.columns:
                s["start_time_dublin"] = s[a]
                break
    if "runner_name" not in s.columns:
        for a in ("runner", "selection_name"):
            if a in s.columns:
                s["runner_name"] = s[a]
                break
    return s

# ------------------------ Data handling ------------------------

def standardize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def coerce_numeric(series: pd.Series):
    return pd.to_numeric(series, errors="coerce")

def parse_dublin_date(s: str | None):
    if not s or not isinstance(s, str):
        return None
    try:
        dt = pd.to_datetime(s, errors="coerce")
        return None if pd.isna(dt) else dt.date()
    except Exception:
        return None

def filter_today_only(snaps: pd.DataFrame) -> pd.DataFrame:
    s = standardize_cols(snaps)
    if "start_time_dublin" in s.columns:
        s["_start_date"] = s["start_time_dublin"].apply(parse_dublin_date)
        s = s[s["_start_date"] == date.today()].copy()
        s.drop(columns=["_start_date"], inplace=True)
    return s

def merge_probs_with_snaps(probs: pd.DataFrame, snaps: pd.DataFrame) -> pd.DataFrame:
    p = standardize_cols(probs)
    s = standardize_cols(snaps)

    if "p_win" not in p.columns:
        for alt in ("prob_win", "win_prob", "p(win)", "pwin"):
            if alt in p.columns:
                p = p.rename(columns={alt: "p_win"})
                break

    if "selection_id" in p.columns:
        p["selection_id"] = coerce_numeric(p["selection_id"])
    if "selection_id" in s.columns:
        s["selection_id"] = coerce_numeric(s["selection_id"])

    if "market_type" in s.columns:
        s_win = s[s["market_type"].astype(str).str.upper() == "WIN"].copy()
        if s_win.empty:
            s_win = s.copy()
    else:
        s["market_type"] = "WIN"
        s_win = s

    if "runner_name" in p.columns:
        p["runner_name_key"] = p["runner_name"].astype(str).str.strip().str.casefold()
    if "runner_name" in s_win.columns:
        s_win["runner_name_key"] = s_win["runner_name"].astype(str).str.strip().str.casefold()

    merged = None
    if "selection_id" in p.columns and "selection_id" in s_win.columns:
        if "market_id" in p.columns and "market_id" in s_win.columns:
            merged = p.merge(s_win, on=["selection_id","market_id"], how="left", suffixes=("_prob","_snap"))
        else:
            merged = p.merge(s_win, on="selection_id", how="left", suffixes=("_prob","_snap"))

    if merged is None and "runner_name_key" in p.columns and "runner_name_key" in s_win.columns:
        merged = p.merge(s_win, on="runner_name_key", how="left", suffixes=("_prob","_snap"))

    if merged is None:
        merged = p.copy()

    if "market_id" not in merged.columns and "market_id" in s_win.columns:
        merged["market_id"] = merged.get("market_id_snap", None)

    if "market_id" not in merged.columns:
        merged["market_id"] = "UNKNOWN"

    if "runner_name" not in merged.columns:
        rn_cols = [c for c in merged.columns if c.startswith("runner_name")]
        merged["runner_name"] = merged[rn_cols[0]] if rn_cols else ""

    return merged

# ------------------------ EV / gating ------------------------

def compute_ev(df: pd.DataFrame, commission: float = 0.02) -> pd.DataFrame:
    out = df.copy()
    out["p_win"] = pd.to_numeric(out.get("p_win", float("nan")), errors="coerce")

    for k in ("best_back","best_lay","decimal_odds","price"):
        if k in out.columns:
            out[k] = pd.to_numeric(out[k], errors="coerce")

    if "best_back" not in out.columns:
        out["best_back"] = float("nan")
    if "decimal_odds" in out.columns:
        out["best_back"] = out["best_back"].fillna(out["decimal_odds"])

    out["fair_price"] = 1.0 / out["p_win"]
    out.loc[~out["p_win"].gt(0), "fair_price"] = float("nan")

    out["ev_win"] = out["p_win"] * out["best_back"] * (1.0 - commission) - 1.0
    out.loc[out["best_back"].isna() | ~out["p_win"].gt(0), "ev_win"] = float("nan")

    out["overlay"] = (out["best_back"] - out["fair_price"]) / out["fair_price"]
    out.loc[out["best_back"].isna() | ~out["p_win"].gt(0), "overlay"] = float("nan")

    return out

def best_per_market(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    df = df.copy()
    df["market_id"] = df["market_id"].astype(str)
    return (df.sort_values(["ev_win","overlay","p_win"], ascending=False)
              .groupby("market_id", as_index=False)
              .head(1))

def shortlist(df: pd.DataFrame, min_back: float, min_overlay: float) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    x = df.copy()
    if "runner_name" not in x.columns:
        rn_cols = [c for c in x.columns if c.startswith("runner_name")]
        x["runner_name"] = x[rn_cols[0]] if rn_cols else ""
    x = x[x["p_win"].fillna(0) > 0]
    x = x[x["best_back"].fillna(0) >= min_back]
    x = x[x["overlay"].fillna(-9e9) >= min_overlay]
    return x

# ------------------------ EW helpers ------------------------

def compute_place_terms(row):
    # Try to source place terms from probs if present; else fallback heuristics
    places = row.get("ew_places")
    frac = row.get("ew_fraction")
    try:
        places = int(places) if pd.notna(places) else None
    except Exception:
        places = None
    try:
        frac = float(frac) if pd.notna(frac) else None
    except Exception:
        frac = None
    return places, frac

def compute_ew_ev_row(row, commission=0.02):
    p_win = row.get("p_win")
    best_back = row.get("best_back")
    p_place = row.get("p_place") if "p_place" in row.index else None
    if pd.isna(p_win) or pd.isna(best_back):
        return None, None, None
    places, frac = compute_place_terms(row)
    if places is None or frac is None or p_place is None or pd.isna(p_place):
        # Cannot calculate without place inputs
        return None, None, None
    # Rough EW EV: half stake on win part, half on place part at fraction
    ev_win_half = 0.5 * (p_win * best_back * (1.0 - commission) - 1.0)
    # Place odds as fraction of win odds (book terms), net of commission
    place_odds = max((best_back - 1.0) * frac + 1.0, 1.0)
    ev_place_half = 0.5 * (p_place * place_odds * (1.0 - commission) - 1.0)
    ev_ew = ev_win_half + ev_place_half
    return ev_place_half, ev_ew, place_odds

def decide_bet_type(row):
    # Default: Win bet
    best_back = row.get("best_back")
    ev_win = row.get("ev_win")
    ev_place_half, ev_ew, place_odds = compute_ew_ev_row(row)
    if ev_place_half is not None and ev_ew is not None and ev_win is not None and best_back is not None:
        # EW if odds <= 9.0 (≈8/1) AND EV_place >= 1.2× EV_win (half-stake comp) AND >=3 places
        places, frac = compute_place_terms(row)
        if places and places >= 3 and best_back <= 9.0 and ev_place_half >= 1.2 * (0.5 * ev_win):
            return "EW", ev_place_half, ev_ew, place_odds, places, frac
    return "WIN", None, None, None, None, None

# ------------------------ Prompt & snapshots orchestration ------------------------

def run_saved_prompt_if_needed(args) -> None:
    if not args.use_saved_prompt:
        return
    if not args.prompt_cmd:
        # Use local run_saved_prompt.py script with same Python interpreter
        default_cmd = f"{sys.executable} run_saved_prompt.py --prompt ./prompt.txt --out {{out}}"
    else:
        default_cmd = args.prompt_cmd
    cmd = default_cmd.format(out=args.probs_csv)
    debug(f"[PROMPT] Running saved prompt -> {args.probs_csv}\n CMD: {cmd}")
    ensure_parent_dir(args.probs_csv)
    ret = subprocess.run(cmd, cwd=args.prompt_workdir, shell=True)
    if ret.returncode != 0 or not os.path.exists(args.probs_csv):
        debug(f"[ERROR] Prompt failed or {args.probs_csv} missing")
        sys.exit(3)

def _build_snapshot_cmd(args, *, override: dict | None = None):
    """Construct the bf_script command, optionally overriding some flags (used for fallbacks)."""
    od = override or {}
    cmd = [sys.executable, args.bf_script]
    # decide once vs snapshots
    if args.once or not args.snapshots or od.get("force_once", False):
        cmd += ["--once"]
    if args.snapshots and not od.get("force_once", False):
        cmd += ["--snapshots", od.get("snapshots", args.snapshots)]
    # pass-through
    market_types = od.get("market_types", args.market_types)
    if market_types:
        cmd += ["--market_types", market_types]
    depth = od.get("depth", args.depth)
    if depth:
        cmd += ["--depth", str(depth)]
    outfile_prefix = od.get("outfile_prefix", args.outfile_prefix)
    if outfile_prefix:
        cmd += ["--outfile_prefix", outfile_prefix]
    outfile = od.get("outfile", args.outfile)
    if outfile:
        cmd += ["--outfile", outfile]
    ts = od.get("ts", args.ts)
    if ts:
        cmd += ["--ts", ts]
    countries = od.get("countries", args.countries)
    if countries is not None:
        # Note: empty string means ALL countries (preferred)
        cmd += ["--countries", countries]
    window_hours = od.get("window_hours", args.window_hours)
    if window_hours:
        cmd += ["--window_hours", str(window_hours)]
    return cmd

def _run_snapshot_cmd(cmd) -> int:
    debug("[SNAPSHOT] " + " ".join(cmd))
    ret = subprocess.run(cmd)
    return ret.returncode

def _preflight_keepalive(args):
    if args.keepalive_cmd:
        debug(f"[AUTH] Running keepalive_cmd: {args.keepalive_cmd}")
        ret = subprocess.run(args.keepalive_cmd, shell=True)
        if ret.returncode != 0:
            debug(f"[AUTH] keepalive_cmd failed with code {ret.returncode}")
    elif args.keepalive_url:
        app_key = os.environ.get("BETFAIR_APP_KEY", "").strip()
        session = os.environ.get("BETFAIR_SESSION", "").strip()
        if not app_key or not session:
            debug("[AUTH] keepalive_url provided but BETFAIR_APP_KEY or BETFAIR_SESSION missing")
        else:
            headers = {"X-Application": app_key, "X-Authentication": session, "Accept": "application/json"}
            code, body = _http_get(args.keepalive_url, headers=headers)
            debug(f"[AUTH] keepAlive HTTP status={code}")
            if body:
                preview = body if len(body) < 300 else body[:300]
                debug(f"[AUTH] keepAlive body (first 300): {preview}")

def run_snapshots_if_needed(args) -> str | None:
    snap_csv = None
    if args.auto:
        debug("Collecting Betfair delayed snapshots...")
        _preflight_keepalive(args)
        cmd = _build_snapshot_cmd(args)
        rc = _run_snapshot_cmd(cmd)
        if rc != 0:
            debug(f"[ERROR] Snapshot script failed with code {rc}")
            sys.exit(rc)
        snap_csv = discover_snapshot_path(args.outfile, args.ts)
        if not snap_csv or not os.path.exists(snap_csv):
            debug(f"[ERROR] Expected snapshot file not found: {snap_csv}")
            sys.exit(1)

        # If zero rows, optionally fallback with safer defaults
        rows = csv_rows(snap_csv)
        if args.fallback_snapshots and (rows <= 0):
            debug("[WARN] Snapshot has zero rows. Retrying with safer defaults (no countries, WIN only, longer window)…")
            # Try a temp outfile so we don't overwrite the previous one
            tmp_outfile = os.path.join(args.outfile_prefix, "run_fallback_once.csv")
            od = {
                "force_once": True,
                "countries": "",                 # ALL countries
                "market_types": args.fallback_market_types,
                "window_hours": args.fallback_window_hours,
                "outfile": tmp_outfile,
            }
            cmd2 = _build_snapshot_cmd(args, override=od)
            rc2 = _run_snapshot_cmd(cmd2)
            if rc2 == 0 and os.path.exists(tmp_outfile) and csv_rows(tmp_outfile) > 0:
                debug(f"[OK] Fallback snapshot succeeded -> {tmp_outfile}")
                # replace snap_csv for downstream
                snap_csv = tmp_outfile
            else:
                debug("[WARN] Fallback snapshot also empty or failed. Proceeding with model-only prices (if any).")
    else:
        snap_csv = discover_snapshot_path(args.outfile, args.ts)
        if snap_csv and not os.path.exists(snap_csv):
            debug(f"[WARN] Snapshot path provided but not found: {snap_csv}")
            snap_csv = None
    return snap_csv

# ------------------------ Reporting ------------------------

def write_debug_report(path: str, sections: list[tuple[str, str]]):
    if not path:
        return
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        for title, body in sections:
            f.write(f"## {title}\n\n{body}\n\n")
    debug(f"[OK] Wrote debug report -> {path}")

# ------------------------ Main flow ------------------------

def main():
    ap = build_argparser()
    args = ap.parse_args()
    report_sections = []

    # Sanity: helpful echo of key envs (not secrets), for debugging tokens
    for var in ["BETFAIR_APP_KEY", "BETFAIR_SESSION"]:
        if os.environ.get(var):
            debug(f"[ENV] {var}=<set>")
        else:
            debug(f"[ENV] {var}=<missing>")

    if args.use_saved_prompt:
        run_saved_prompt_if_needed(args)

    snap_csv = run_snapshots_if_needed(args)

    if not os.path.exists(args.probs_csv):
        debug(f"[ERROR] probs_csv not found: {args.probs_csv}")
        sys.exit(2)
    probs = pd.read_csv(args.probs_csv)
    report_sections.append(("Probs CSV loaded", f"Rows: {len(probs)} | Path: {args.probs_csv}"))

    if snap_csv and os.path.exists(snap_csv):
        snaps_raw = pd.read_csv(snap_csv)
        snaps = _canonicalize_snapshots(snaps_raw)
        snaps = filter_today_only(snaps)
        report_sections.append(("Snapshots loaded", f"Rows(raw): {len(snaps_raw)} | Rows(today): {len(snaps)} | Path: {snap_csv}"))
    else:
        snaps = pd.DataFrame(columns=["timestamp_europe_dublin","market_type","market_id","market_name","venue","country","start_time_dublin","selection_id","runner_name","best_back"])
        report_sections.append(("Snapshots loaded", "No snapshot file present; proceeding with probs-only prices if available"))

    merged = merge_probs_with_snaps(probs, snaps)
    # Coalesce descriptive fields so market_name/venue/start_time_dublin are populated
    merged = _coalesce_columns(merged, ["market_name","venue","start_time_dublin","runner_name","market_id"])
    scored = compute_ev(merged, commission=0.02)

    # Initialize final_top5 to avoid NameError on any path
    final_top5 = pd.DataFrame()

    step, min_overlay, explain = 0, args.min_overlay, []
    while step <= (args.relax_steps if args.relax_if_empty else 0):
        filtered = shortlist(scored, args.min_back, min_overlay)
        bpm = best_per_market(filtered)
        top5 = bpm.sort_values(["ev_win","overlay","p_win"], ascending=False).head(5)
        explain.append(f"Step {step}: min_back>={args.min_back}, min_overlay>={min_overlay:.3f} -> candidates={len(filtered)}, markets={bpm['market_id'].nunique() if not bpm.empty else 0}, top5={len(top5)}")
        if not top5.empty:
            final_top5 = top5
            break
        step += 1
        min_overlay -= args.relax_delta

    report_sections.append(("Gating summary", "\n".join(explain)))
    cols_out = ["market_id","market_name","venue","start_time_dublin","runner_name","p_win","best_back","ev_win","fair_price","overlay"]
    for c in cols_out:
        if c not in scored.columns:
            scored[c] = None

    # Ensure existence before writing
    ensure_parent_dir(args.out_csv)
    if final_top5.empty:
        pd.DataFrame(columns=cols_out).to_csv(args.out_csv, index=False)
        report_sections.append(("Outcome","No qualifying selections after relaxation. Wrote empty Top 5 with headers."))
        debug("[INFO] No qualifying selections (empty Top 5 written).")
    else:
        final_top5 = _ensure_columns(final_top5, cols_out, fill=None)
        final_top5.to_csv(args.out_csv, index=False)
        report_sections.append(("Outcome", f"Wrote {len(final_top5)} selections to {args.out_csv}"))
        debug(f"[OK] Wrote Top {len(final_top5)} picks to {args.out_csv}")

    # Write human-readable analysis report
    if args.analysis_report:
        lines = []
        lines.append("# Top selections — analysis\n")
        if final_top5.empty:
            lines.append("No qualifying selections. Thresholds may be tight or model implied prices ≥ market.\n")
        else:
            for _, r in final_top5.iterrows():
                bet_type, ev_place_half, ev_ew, place_odds, places, frac = decide_bet_type(r)
                fp = r.get("fair_price")
                tags = r.get("tags") if "tags" in r.index else ""
                why = r.get("why_now") if "why_now" in r.index else r.get("why now?") if "why now?" in r.index else ""
                lines.append(f"## {r.get('runner_name','(runner)')} — {bet_type}\n")
                lines.append(f"- Market: {r.get('market_name','')} @ {r.get('venue','')} — off {r.get('start_time_dublin','')}\n")
                try:
                    lines.append(f"- P(win): {float(r.get('p_win')):.3f} | Fair: {float(fp):.2f} | Best back: {r.get('best_back')} | Overlay: {float(r.get('overlay')):.3f}\n")
                except Exception:
                    lines.append(f"- P(win): {r.get('p_win')} | Fair: {fp} | Best back: {r.get('best_back')} | Overlay: {r.get('overlay')}\n")
                if bet_type == "EW":
                    lines.append(f"- P(place): {r.get('p_place','?')} | EW terms: {places} places @ {frac} | Place odds≈ {place_odds:.2f}\n")
                    lines.append(f"- EV(win): {r.get('ev_win'):.3f} | EV(place half): {ev_place_half:.3f} | EV(EW): {ev_ew:.3f}\n")
                else:
                    lines.append(f"- EV(win): {r.get('ev_win'):.3f}\n")
                if tags: lines.append(f"- Tags: {tags}\n")
                if why: lines.append(f"- Why now?: {why}\n")
                lines.append("")
        ensure_parent_dir(args.analysis_report)
        with open(args.analysis_report, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        debug(f"[OK] Wrote analysis -> {args.analysis_report}")
    
    # Save to DynamoDB if requested
    if args.save_to_dynamodb and not final_top5.empty:
        debug("\n[DYNAMODB] Saving selections to database...")
        cmd = f"python save_selections_to_dynamodb.py --selections {args.out_csv} --table {args.dynamodb_table} --region {args.dynamodb_region} --min_roi 0.0"
        ret = subprocess.run(cmd, shell=True)
        if ret.returncode == 0:
            debug(f"[OK] Saved {len(final_top5)} selections to DynamoDB")
        else:
            debug(f"[ERROR] Failed to save to DynamoDB (code {ret.returncode})")

    if args.debug_report:
        schema = {"probs_cols": list(probs.columns), "snaps_cols": list(snaps.columns)}
        report_sections.insert(0, ("Schema", "```json\n" + json.dumps(schema, indent=2) + "\n```"))
        write_debug_report(args.debug_report, report_sections)

if __name__ == "__main__":
    main()
