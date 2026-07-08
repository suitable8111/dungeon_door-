# Changelog

## v1.6.0 — Full Localization: 5 Languages

The game now ships in **English, 한국어, 日本語, 简体中文, and Русский** — and English is the new default.

### Localization
- **Default language is now English** (first launch). Cycle languages anytime in Settings — the UI, fonts, and all in-game text switch instantly, mid-run included.
- **Everything is translated**: all 319 UI strings, 10 equippable skills (names, descriptions, per-level stats), 4 combo skills, 2 ultimates, 4 enchants, 20 floor themes, 31 items, and 52 monsters.
- **Fixed**: skill names/descriptions and item names previously showed Korean even in English mode.
- **Per-language fonts**: Korean/English/Russian keep the bundled pixel font (it covers Cyrillic!); Japanese and Chinese fall back to system CJK fonts (Hiragino/PingFang on macOS, Yu Gothic/YaHei on Windows — preinstalled on both).

## v1.5.0 — The Dopamine Update (Game Feel 2.0)

Every kill, crit, and level-up now *feels* like a reward. No balance changes — pure feedback juice.

### Kill Combos, Amplified
- **Rising-pitch kill chimes**: every kill in a combo chain plays a pentatonic note one step higher than the last (8-step ladder) — chaining kills literally sounds like a melody building up.
- **Combo tiers with callouts**: reaching x5 / x10 / x15 / x20 triggers **RAMPAGE! → DOMINATING! → UNSTOPPABLE! → GODLIKE!!** — a full-width banner punches in, a tier-colored particle burst erupts from the player, a fanfare plays, and the screen kicks.
- **Living combo counter**: the COMBO counter now grows with your streak, takes on the tier color, pulses with a glow halo, and pops on every kill.

### Impact & Reward Feedback
- **Punch zoom**: critical hits, boss kills, and tier-ups snap the camera in for a split second — hits land with real weight.
- **Level-up celebration**: golden screen flash, a fountain of gold particles from the player, a "LEVEL UP!" banner, a richer fanfare, and a brief hit-stop. You will not miss a level-up again.
- **Gold popups**: enemies now pop a floating "+N G" on death, right after the damage number.
- **Crit shake**: critical hits add a short screen shake on top of the existing hit-stop.

### Tension
- **Heartbeat vignette**: below 25% HP the screen edge pulses red like a heartbeat — clutch escapes feel like clutch escapes.

## v1.3.0 — Elite Variants, Kill Combos & Achievements

### New Content
- **Elite monster variants**: from floor 4, monsters have a 5–15% chance (scaling with depth) to spawn as elites with a colored aura and a name prefix:
  - **Swift** — moves 35% faster, attacks 20% faster
  - **Ironhide** — double defense, 1.6× HP
  - **Berserk** — 1.5× attack
  - **Vampiric** — heals for 50% of damage dealt
  - **Volatile** — explodes on death (1-tile radius) — melee kills are risky!
  - Elites grant 2.5× XP, 3× gold, and a 70% item drop chance (vs 28%)
- **Kill combo**: chaining kills within 4 seconds builds a combo that grants bonus Arcane SP (up to +8 per kill) with an on-screen COMBO counter — aggressive play now feeds your ultimate faster.
- **Achievements** (16): floor milestones, boss hunts, elite hunts, kill combos, enhancement mastery, and more. Tracked locally; Steam sync activates automatically once Steam libraries ship with the build.

### Localization
- All 52 monsters now have proper English names (previously shown in Korean).

## v1.2.0 — Combat Rebalance & Game Feel Update

### Balance
- **Reworked XP curve** with a soft cap (was ×1.6 exponential; now ×1.33, easing to ×1.15 after Lv20). Leveling no longer stalls in the mid-teens — reaching Lv20 now takes ~29k cumulative XP instead of ~280k.
- **New damage formula** with 18% minimum armor penetration and ±10–15% variance, applied consistently to basic attacks, all skills, enemies, and bosses. Eliminates both one-shot-everything early floors and the "1 damage wall" on deep floors.
- **Potions scale**: healing potions now restore a percentage of max HP (small 25% / large 50%) when that exceeds the flat amount.
- **Level-up HP gain scales** with level (+8 + level/3).
- **Enemy defense scaling softened** (0.55× rate) so deep-floor enemies stay killable while HP/attack keep scaling.
- **Fixed**: enemy gold drops now actually scale with floor depth (field-name bug).
- Rooms from floor 3 onward always contain at least one enemy.
- **Shop prices**: stepped tier pricing (every 50 floors) replaced with a smooth curve that rises slower than gold income — the deeper you go, the relatively cheaper shopping gets.

### Game Feel & Animation
- **Enemies slide between tiles** instead of teleporting.
- **Attack telegraphs**: enemies wind up for 280 ms (ranged 400 ms) with a "!" marker and shake before striking — step away to dodge.
- **Boss danger zones**: Charge / Whirlwind / Death Nova now channel for 750 ms while the affected tiles pulse red. Charge locks onto your position at wind-up, so you can sidestep it.
- **Hit reactions**: white damage flash, knockback nudge, brief stagger, and hit-stop (30 ms normal / 60–70 ms on crits and kills).
- **Death animation**: enemies collapse and fade with color-matched debris particles instead of vanishing instantly.
- **Player damage feedback**: red screen vignette plus screen shake scaled to damage taken.
- **Crit numbers** pop larger in yellow; damage numbers jitter horizontally so rapid hits don't overlap.
- Snappier movement interpolation for the player.

### Localization
- All enemy and boss combat messages are now fully localized (KO/EN) — previously hardcoded in Korean.
