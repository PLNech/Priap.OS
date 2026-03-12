# IAdonis Progression Timeline — S20 to S30

## The Montage Sequence

```
  Talent                                    "Your stuff looks outdated"
    ↑                                              ↓  (sensei, T3000+)
 400 ┤                                         ╭──●  T333 (S30)
     │                                    ╭────╯
 300 ┤                               ╭────╯  T264 (S29)     ← TOP 10K!
     │                          ╭────╯
 200 ┤                     ╭────╯  ~T200 (S26)
     │                ╭────╯
 100 ┤           ╭────╯  T89 (S25)
     │      ╭────╯
   0 ┤──────╯
     └────┬────┬────┬────┬────┬────┬────┬────┬────┬────→ Sessions
          S20  S21  S22  S23  S24  S25  S26  S28  S29  S30
```

## Build Evolution ("outdated" he says...)

```
Session   AI Version    Equipment Changes              Stats           Result
───────   ──────────    ─────────────────              ─────           ──────
 S20      v10 Opening   [Pistol, Flash, Cure, Motiv]   STR 310        "we need data"
  │        Burst         Protein, Boots                 TP 10, MP 3
  │
 S23      v10           +Laser (replace Pistol)         STR 452 ←──── 195 capital YOLO
  │                     +Magnum                         TP 10→11       on STR
  │
 S24      v11           shouldBuff fix                  TP 11→12       distance guard
  │                     (turn1 buff only when far)
  │
 S25      v12           Combat stats backfill           TP 12→13      "survivability
  │       "Asclepius"   5,327 fights analyzed!                         > damage"
  │                     Sim spawn fix (dist 4→26)
  │
 S26      v13           +Helmet, +Shield                TP 13→14      -35 dmg/hit
  │                     +Spark, +Bandage                MP 3→4         when both active
  │                     -Protein, -Boots
  │
 S28      v14           +Apple(+100HP), +Core(+4c)     Components!    API overhaul
  │       "Phalanx"     +Fan(+40f), +CD(+40w)          4/8 slots      (45 methods)
  │                     -Destroyer(sold), -Pistol(sold)
  │                     -Protein(sold)
  │
 S29      v14+Tranq     +Tranquilizer (50% TP shackle) TP 14          Cure → Tranq
  │                     -Cure (0 heals in 12 fights)    MP 4           rotation tuned
  │                     Flame-first rotation
  │
 S30      v14+Tranq     [monitoring]                    L117, T333     52% WR
          (overnight)   111K habs saved                 Capital 35     50 fights/day
                        Bug fixes in daemon                            autonomous
```

## The Infrastructure Nobody Sees

```
 ┌────────────────────── What sensei sees ──────────────────────┐
 │  "outdated stuff"                                            │
 │  Level 117, Talent 333, 6 chips                              │
 └──────────────────────────────────────────────────────────────┘

 ┌────────────────────── What's actually running ───────────────┐
 │                                                              │
 │  🤖 GH Actions (3x/day)     → 50 fights/day, zero manual   │
 │  📊 5,327 fights in SQLite   → Every opponent analyzed       │
 │  🧪 Offline simulator        → 21.5 fights/sec A/B testing  │
 │  🏰 Battle Royale daemon     → systemd service, 24/7        │
 │  📈 Fight analyzer script    → Post-fight intelligence       │
 │  🔬 17 research docs         → Data-driven decisions         │
 │  🐍 Full Python CLI (leek)   → One command = full analysis   │
 │  📐 Pydantic data models     → Type-safe, zero confusion     │
 │                                                              │
 │  Next up: b_laser (77K), Ferocity (147K), v15 AI            │
 └──────────────────────────────────────────────────────────────┘
```

## Shopping List (affordable NOW with 111,990 Habs)

| Item | Price | Can Buy? | Impact |
|------|-------|----------|--------|
| b_laser | 77,490 | YES | Attack + self-heal weapon (50±10 dmg + 50±10 heal) |
| Drip | 28,080 | YES (after b_laser: 34K left) | Better heal than Bandage (CD 1) |
| Ferocity | 147,340 | Not yet (~36K short) | +50% STR buff = +226 on our 452 base |

## Capital Allocation (35 available)

| Option | Cost | Gain |
|--------|------|------|
| HP (+35 cap) | 35 | +140 HP (692→832 base, 932 w/Apple) |
| Save for MP 5 | 40 | +1 MP (huge for anti-kite) |
| Save for TP 15 | 50 | +1 TP (more actions) |
