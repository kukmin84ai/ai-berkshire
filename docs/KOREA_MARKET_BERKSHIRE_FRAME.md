# Korea Market Extension — Berkshire Lens

This extension adapts AI Berkshire to the Korean market without changing the original China/US/HK research framework.

## Core thesis

Korea is a **cheap but governance-sensitive** market:

- Many businesses are globally competitive and statistically inexpensive.
- The persistent discount usually comes from capital allocation, holding-company complexity, low payout, succession issues, and cyclicality.
- A Korea-specific AI Berkshire flow should therefore screen for **business quality + shareholder-return improvement**, not low PBR alone.

## First-pass baskets

1. `kr_export_quality`
   - Samsung Electronics, SK hynix, Hyundai Motor, Kia
   - Purpose: global scale, cash generation, semiconductor/auto cyclicality.

2. `kr_power_grid`
   - HD Hyundai Electric, Hyosung Heavy Industries, LS ELECTRIC
   - Purpose: grid capex, transformers, data-center/electrification bottlenecks.

3. `kr_shipbuilding_defense`
   - HD Hyundai Heavy Industries, Hanwha Ocean, Hanwha Aerospace, LIG Nex1
   - Purpose: shipbuilding cycle + structural defense export demand.

4. `kr_valueup_financials`
   - Shinhan, KB, Woori financial groups
   - Purpose: value-up / capital-return sensitivity.

## Buffett-style Korea checklist

Use the normal AI Berkshire master checklist, but add these Korea gates:

1. **Capital allocation gate**
   - Dividend trend, buyback cancellation, ROE target, excess capital policy.
   - Red flag: cash hoarding or treasury-share buybacks without cancellation.

2. **Governance gate**
   - Related-party transactions, holding-company discount, succession overhang.
   - Red flag: controlling-shareholder benefit at minority-shareholder cost.

3. **Cycle-position gate**
   - Semiconductor, shipbuilding, chemical, steel, battery, and auto must be judged by cycle position.
   - Red flag: buying statistically cheap late-cycle earnings.

4. **FX/export gate**
   - KRW/USD, China demand, US capex cycle, and global inventory must be explicit.

5. **Filing verification gate**
   - Naver/portal data is only a watch trigger.
   - Before research conclusions: verify with DART filings, company IR, and at least one independent market-data source.

## University / industry signal layer

Korean equity work should also track a small number of university-industry signal sources. These are not investable assets, but they can show where talent, capstone projects, patent competitions, and industry mentoring are clustering before the signal appears in financial statements.

Initial signal note:

- `reports/한국장/한양대-산학클러스터-신호-20260628.md` — Hanyang ERICA as a semiconductor / AI / advanced mobility / renewable energy / digital transformation signal source.

Use this layer only to generate better research questions. Any company-level conclusion still requires DART/company IR verification.

## Tooling

- Watchlist: `data/korea_watchlist.json`
- Quote/index/scan helper: `tools/korea_market.py`

Examples:

```bash
python3 tools/korea_market.py quote 005930
python3 tools/korea_market.py index KOSPI
python3 tools/korea_market.py scan --output data/korea_market_snapshot.json
```

## Output discipline

The Korea watcher only emits:

- `watch_only`
- `watch_verify_with_filings`
- `research_capital_allocation`

It must not emit automatic buy/sell instructions. A research memo is required before any investable conclusion.
