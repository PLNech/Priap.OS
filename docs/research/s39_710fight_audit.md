# S39 Fight Audit — 710 Fights (Mar 22–Apr 4, 2026)

> Post-S38 deployment (Ferocity+getCooldown+RES66). 13 days of daemon operation.

## Headline

| Metric | Value |
|--------|-------|
| Total fights | 710 (IAdonis) + 5 (AnansAI) |
| Overall WR | **48.2%** (342W-350L-18D) |
| Matchmaking WR | 49.1% (696 fights) |
| Tournament WR | **0.0%** (0W-14L) |
| Level | L130→L145 (+15) |
| Talent | T377→T368 (-9 net, peaked T413) |
| Rank | #8231→#8404 (peaked #7610) |
| Capital | 12→87 (+75 unspent) |
| Habs | ~4K→202K |

## Daily Breakdown (IAdonis)

```
Date          W    L    D  Total    WR
──────────────────────────────────────
2026-03-22   24   25    2     51  47.1%
2026-03-23   25   26    0     51  49.0%
2026-03-24   21   22    3     46  45.7%
2026-03-25   26   27    3     56  46.4%
2026-03-26   25   26    0     51  49.0%
2026-03-27   27   24    0     51  52.9%
2026-03-28   23   27    1     51  45.1%
2026-03-29   25   25    1     51  49.0%
2026-03-30   24   26    1     51  47.1%
2026-03-31   25   23    3     51  49.0%
2026-04-01   25   24    2     51  49.0%
2026-04-02   24   27    0     51  47.1%
2026-04-03   24   26    1     51  47.1%
2026-04-04   24   22    1     47  51.1%
──────────────────────────────────────
TOTAL       342  350   18    710  48.2%
```

## Context Breakdown

| Context | W | L | D | Total | WR |
|---------|---|---|---|-------|-----|
| Matchmaking | 342 | 336 | 18 | 696 | 49.1% |
| Tournament | 0 | 14 | 0 | 14 | **0.0%** |

## Archetype WR (from Apr 4 GH Actions, 38-fight sample)

| Archetype | W | L | D | WR |
|-----------|---|---|---|-----|
| Aggro | 11 | 9 | 0 | 55% |
| Balanced | 5 | 4 | 0 | 56% |
| Kiter | 2 | 6 | 0 | **25%** |
| Healer | 0 | 0 | 1 | 0% (draw) |

## Talent Trajectory (from ranking DB)

```
Snapshot  Level  Talent  Rank     Delta
────────────────────────────────────────
 10       L130   T377    #8231    start
 12       L132   T376    #8249    -1
 13       L132   T375    #8266    -1
 14       L138   T364    #8493    -11
 15       L139   T380    #8185    +16
 16       L140   T361    #8542    -19
 17       L141   T395    #7902    +34
 18       L142   T413    #7610    +18 PEAK
 20       L144   T383    #8127    -30
 21       L145   T368    #8404    -15 CURRENT
```

52-point swing range (T361-T413). Net: -9 over 13 days.

## Tournament Losses (0W-14L)

All losses, daily at 10:00-11:00 UTC:

| Date | Opponent | Fight ID |
|------|----------|----------|
| 03-22 | PigDestoryer | 51905430 |
| 03-23 | KavaLeek3 | 51916082 |
| 03-24 | koe3 | 51924582 |
| 03-25 | Gaussian | 51934051 |
| 03-26 | Fantosynthèse | 51945047 |
| 03-27 | Gaussian | 51953636 |
| 03-28 | Nachi | 51965695 |
| 03-29 | KavaTropLoin | 51977810 |
| 03-30 | MichelTourniquet | 51983956 |
| 03-31 | PigDestoryer | 51993538 |
| 04-01 | DuskHope | 52003697 |
| 04-02 | lipitibouclier | 52018291 |
| 04-03 | Excellent | 52026515 |
| 04-04 | DawnFall | 52036632 |

## Nemesis Opponents (0% WR, 3+ encounters)

| Opponent | Record |
|----------|--------|
| ArrnArchi | 0W-3L |
| TerenceMyleek | 0W-3L |
| GeekOfSmourad | 0W-3L |
| ElCarotte | 0W-3L |
| Spounleek | 0W-3L |
| aarya | 0W-3L |

## Draws (18 total)

Notable: BudL33k (2 draws), multiple opponents with 170 HP (low-level timeouts?).

## Key Findings

1. **S38 Ferocity+RES66 had no visible WR impact**: 48.2% over 710 = same as S37's 48% over 200. Ferocity usage needs verification.
2. **Tournaments = ~70 talent drain**: 14 guaranteed losses × ~5 talent each. Single biggest improvement is stopping tournament registration.
3. **Kiter matchup is crisis**: 25% WR. Need dedicated anti-kiter logic.
4. **Draws are wasted fights**: 18 timeouts suggest stalemate detection needs improvement.
5. **Daemon has reporting bug**: 5 false crash positives on Apr 4 (actual: 5W-1L).
6. **AnansAI barely fighting**: Only 5 fights in 13 days — daemon not running fights for it.

## Level-Up Progression (31 events)

L130→L145 in 13 days. Average: ~1.15 levels/day. Each level grants capital — hence 75 capital accumulated.

## Recommendations

1. **Disable tournament registration** (immediate, ~70 talent saved)
2. **Spend 87 capital on RES** (66→150+, brings us to bracket standard)
3. **Build anti-kiter AI logic** (25% WR → target 45%+)
4. **Improve stalemate detection** (18 draws → target <5)
5. **Verify Ferocity fires** (explain no WR improvement)
6. **Fix daemon crash reporting** (operational trust)
7. **Deploy AI v15** with all fixes
