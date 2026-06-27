#!/usr/bin/env python3
"""Korean market watcher for AI Berkshire.

Zero-dependency helper for Korea-focused value-investing triage. It deliberately
stops at "watch / research / verify" signals and does not produce trade orders.

Examples:
    python3 tools/korea_market.py quote 005930
    python3 tools/korea_market.py index KOSPI
    python3 tools/korea_market.py scan --watchlist data/korea_watchlist.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHLIST = ROOT / "data" / "korea_watchlist.json"

INDEX_CODES = {
    "KOSPI": "KOSPI",
    "KOSDAQ": "KOSDAQ",
    "KPI200": "KPI200",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (AI Berkshire Korea Market Watcher)"}


def _fetch(url: str, encoding: str = "euc-kr") -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=15) as res:
        raw = res.read()
    for enc in (encoding, "cp949", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode(encoding, errors="replace")


def _num(text: str):
    text = html.unescape(str(text)).strip().replace(",", "")
    if text in {"", "N/A", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _blind_values(fragment: str):
    return [html.unescape(x).strip() for x in re.findall(r'<span class="blind">([^<]+)</span>', fragment)]


def fetch_quote(code: str) -> dict:
    code = re.sub(r"\D", "", code)[:6]
    if len(code) != 6:
        raise ValueError("Korean stock code must be 6 digits, e.g. 005930")
    url = "https://finance.naver.com/item/main.naver?" + "code=" + code
    page = _fetch(url)

    price_block = re.search(r'<p class="no_today">\s*<em class="no_[^>]+">(.*?)</em>', page, re.S)
    price_vals = _blind_values(price_block.group(1)) if price_block else []
    price = _num(price_vals[0]) if price_vals else None

    # Company names in Naver HTML can be mojibake-prone from some terminals, so
    # watchlist metadata is the canonical name source. Keep parsed name best-effort.
    title = re.search(r"<title>\s*(.*?)\s*:", page, re.S)
    parsed_name = html.unescape(title.group(1)).strip() if title else code

    # Analyst-consensus table rows are tagged with stable class suffixes even
    # when Korean labels are encoding-sensitive in terminals.
    table = {}
    row_classes = {
        "EPS": "th_cop_anal17",
        "BPS": "th_cop_anal18",
        "PER": "th_cop_anal20",
        "PBR": "th_cop_anal21",
    }
    for field, cls in row_classes.items():
        m = re.search(r'<th[^>]*class="[^"]*' + cls + r'[^"]*".*?</th>(.*?)</tr>', page, re.S)
        if not m:
            continue
        cells = re.findall(r'<td[^>]*>(.*?)</td>', m.group(1), re.S)
        nums = []
        for cell in cells:
            text = re.sub(r"<.*?>", " ", cell)
            text = html.unescape(text).replace("\xa0", " ").strip()
            n = _num(text)
            if n is not None:
                nums.append(n)
        if nums:
            table[field] = nums[0]

    rate = None
    rate_block = re.search(r'<p class="no_exday">(.*?)</p>', page, re.S)
    if rate_block:
        vals = _blind_values(rate_block.group(1))
        if len(vals) >= 2:
            rate = vals[-1]

    return {
        "code": code,
        "parsed_name": parsed_name,
        "price": price,
        "change_rate_raw": rate,
        "per": table.get("PER"),
        "pbr": table.get("PBR"),
        "eps": table.get("EPS"),
        "bps": table.get("BPS"),
        "dividend_yield": None,
        "source": url,
        "fetched_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }


def fetch_index(index: str) -> dict:
    key = index.upper()
    if key not in INDEX_CODES:
        raise ValueError(f"Unsupported index: {index}; choose {', '.join(INDEX_CODES)}")
    url = "https://finance.naver.com/sise/sise_index.naver?" + "code=" + INDEX_CODES[key]
    page = _fetch(url)
    val = re.search(r'id\s*=\s*"now_value"[^>]*>([^<]+)</em>', page)
    chg = re.search(r'id\s*=\s*"change_value_and_rate"[^>]*>(.*?)</span>', page, re.S)
    return {
        "index": key,
        "value": _num(val.group(1)) if val else None,
        "change_raw": re.sub(r"<.*?>", " ", chg.group(1)).strip() if chg else None,
        "source": url,
        "fetched_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }


def triage_signal(q: dict) -> dict:
    """Buffett-style first-pass triage, not an investment recommendation."""
    flags = []
    risks = []
    pbr = q.get("pbr")
    per = q.get("per")
    div = q.get("dividend_yield")

    if pbr is not None and pbr <= 1.0:
        flags.append("low_pbr_valueup_candidate")
    if per is not None and 0 < per <= 12:
        flags.append("reasonable_reported_per")
    if div is not None and div >= 3:
        flags.append("shareholder_return_visible")
    if per is None or pbr is None:
        risks.append("missing_or_unparsed_valuation_fields")
    if per is not None and per <= 0:
        risks.append("negative_or_not_meaningful_earnings")

    if "low_pbr_valueup_candidate" in flags and not risks:
        action = "research_capital_allocation"
    elif flags:
        action = "watch_verify_with_filings"
    else:
        action = "watch_only"
    return {"action": action, "flags": flags, "risks": risks}


def load_watchlist(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def cmd_quote(args):
    print(json.dumps(fetch_quote(args.code), ensure_ascii=False, indent=2))


def cmd_index(args):
    print(json.dumps(fetch_index(args.index), ensure_ascii=False, indent=2))


def cmd_scan(args):
    watch = load_watchlist(Path(args.watchlist))
    rows = []
    for basket, items in watch.items():
        for item in items:
            q = fetch_quote(item["code"])
            q.update({
                "basket": basket,
                "name": item.get("name"),
                "theme": item.get("theme"),
                "watch_reason": item.get("watch_reason"),
                "triage": triage_signal(q),
            })
            rows.append(q)
    out = {
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "market": "KRX",
        "source": "Naver Finance HTML; verify fundamentals with filings before decisions",
        "count": len(rows),
        "rows": rows,
    }
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quote")
    q.add_argument("code")
    q.set_defaults(func=cmd_quote)
    i = sub.add_parser("index")
    i.add_argument("index", choices=sorted(INDEX_CODES))
    i.set_defaults(func=cmd_index)
    s = sub.add_parser("scan")
    s.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST))
    s.add_argument("--output")
    s.set_defaults(func=cmd_scan)
    args = p.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
