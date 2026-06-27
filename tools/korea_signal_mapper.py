#!/usr/bin/env python3
"""Map Korean university/industry signals to KRX watchlist baskets.

This is a research-question generator, not a trading signal. It joins a
university signal registry with the Korea watchlist and emits conservative event
packets for the summary/research loop.

Examples:
    python3 tools/korea_signal_mapper.py
    python3 tools/korea_signal_mapper.py --output data/korea_signal_events.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIGNALS = ROOT / "data" / "korea_university_signals.json"
DEFAULT_WATCHLIST = ROOT / "data" / "korea_watchlist.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def map_signals(signals: dict, watchlist: dict) -> dict:
    events = []
    for source in signals.get("sources", []):
        mapped_baskets = []
        tickers = []
        for tag, baskets in source.get("basket_mapping", {}).items():
            for basket in baskets:
                if basket not in watchlist:
                    continue
                if basket not in mapped_baskets:
                    mapped_baskets.append(basket)
                for item in watchlist[basket]:
                    key = (item.get("code"), basket)
                    existing = next((r for r in tickers if (r.get("code"), r.get("basket")) == key), None)
                    if existing:
                        existing.setdefault("linked_tags", [])
                        if tag not in existing["linked_tags"]:
                            existing["linked_tags"].append(tag)
                        continue
                    tickers.append({
                        "code": item.get("code"),
                        "name": item.get("name"),
                        "basket": basket,
                        "theme": item.get("theme"),
                        "linked_tags": [tag],
                        "watch_reason": item.get("watch_reason"),
                    })
        events.append({
            "event_type": "university_industry_signal",
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_url": source.get("url"),
            "observed_at_kst": source.get("observed_at_kst"),
            "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
            "action_label": source.get("action_label", "signal_only"),
            "tags": source.get("tags", []),
            "mapped_baskets": mapped_baskets,
            "mapped_tickers": tickers,
            "research_questions": build_questions(source, mapped_baskets),
            "verification_gate": source.get("verification_gate"),
            "evidence": source.get("evidence", []),
        })
    return {
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "scope": "research question generation only; no buy/sell/position instructions",
        "event_count": len(events),
        "events": events,
    }


def build_questions(source: dict, baskets: list[str]) -> list[str]:
    questions = [
        "Which listed companies can show this signal in orders, backlog, hiring, capex, or R&D disclosures?",
        "Is the signal visible in DART filings or company IR, or only in education/program language?",
        "Does the signal point to durable demand or a one-off policy/program cycle?",
    ]
    if "kr_power_grid" in baskets:
        questions.extend([
            "Are grid, transformer, switchgear, ESS, inverter, or power-quality topics increasing in capstone/industry projects?",
            "Do LS ELECTRIC, HD Hyundai Electric, or Hyosung Heavy Industries disclose matching order/backlog evidence?",
        ])
    if "kr_export_quality" in baskets:
        questions.extend([
            "Do semiconductor, mobility, AI, or digital-transformation signals map to Samsung Electronics, SK hynix, Hyundai Motor, or Kia fundamentals?",
            "Is the signal structural enough to matter through the next export/currency cycle?",
        ])
    return questions


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--signals", default=str(DEFAULT_SIGNALS))
    p.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST))
    p.add_argument("--output")
    args = p.parse_args(argv)
    out = map_signals(load_json(Path(args.signals)), load_json(Path(args.watchlist)))
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
