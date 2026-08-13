# Changelog

## v2.17.5 — Archer ultimates rework

- **Crossbow Master** — fixed the homing shot actually flying in a straight line instead of tracking its target (the target search and the arrow's flight direction weren't fully wired together); it now genuinely locks on and turns to face whatever it hits.
- **Archer** gets two new signature ultimates:
  - **R — Deadeye**: for 14s, every basic shot auto-homes onto a random nearby enemy (no need to face them), and the basic-attack SP cost drops to almost nothing.
  - **Ctrl+R — Arrow Windmill**: fires a spinning burst of arrows in every direction, striking every visible enemy at once.
  - **Crossbow Master / Twin Bow** fire **ice arrows** for both ultimates — enemies hit get slowed.
- **Speed Mage** — *Flash Dash* SP cost cut even further again.

## v2.17.4 — Homing shot & SP tuning

- **Crossbow Master** — the post-*Evasive Load* homing shot now correctly **locks onto and flies toward the actual nearest target** (including diagonals), turns the character to face it, and won't lock onto enemies hidden behind walls.
- **Speed Mage** — *Flash Dash* SP cost cut even further — practically free.

## v2.17.3 — Skill fixes

- **Fixed:** the new advanced-class skills were accidentally overwriting the **base Warrior's default W/D skills** — Warrior's *Flash Dash* and *Judgment* are back where they belong. (Dual Blade's W and Magic Swordsman's W are now clearly different skills.)
- **Dual Blade** — *Flash Dash* landing now shows a **twin-blade cross flurry** (steel-blue slashes) instead of a magical burst, so it reads distinct from Magic Swordsman.
- **Speed Mage** — *Flash Dash* now costs **almost no SP**, so you can dash around freely.
- **Crossbow Master** — after *Evasive Load* (W), your next shot **homes onto the nearest enemy** (any direction) for a guaranteed critical + stun.

## v2.17.2 — Advanced class skills, reworked

Each second-tier class now has a **signature skill** that plays to its identity:
- **Dual Blade** — *Flash Dash* now **pierces through every enemy** in the path and unleashes an **area finisher** on landing (much wider damage).
- **Magic Swordsman** — new W skill **Elemental Burst**: sets off multiple **random elemental blasts** (lightning / fire / water / wind) around you, each with its own effect.
- **Speed Mage** — skills reworked to feel *fast*: **Flash Dash** (W) replaces the slow blink, and new **Arcane Barrage** (D) rapid-fires a volley of magic bolts.
- **Crossbow Master** — the **roll is now on W** (*Evasive Load*): roll to dodge, then your next attack is a **guaranteed critical** that stuns.

## v2.17.1 — Advanced class fixes & new skill

- **Dual Blade** now shows **both swords when moving left** (the off-hand blade no longer vanishes).
- **Magic Swordsman** now unleashes a **random elemental wave on every attack** — lightning (stagger), fire (burn), or ice/water (slow) — each with its own color.
- **Twin Archer** now visibly fires **two arrows** (a second arrow flies alongside the first).
- **Crossbow Master** gains a new skill **Evasive Load** (D): quickly roll to dodge, then your **next attack is a guaranteed critical that stuns** the target.

## v2.17.0 — Advanced classes fight differently (Phase 2)

Each second-tier class now has a **signature basic attack** — you feel the advancement every swing:
- **Dual Blade** — melee strikes **twice** (main hit + off-hand).
- **Magic Swordsman** — the finishing blow launches a **mid-range mana wave**.
- **Crossbow Master** — bolts **pierce** through every enemy in a line.
- **Twin Archer** — fires **two arrows** for double damage.
- **Battle Mage** — casts a **close-range magic burst** hitting everything within 2 tiles (+ burn).
- **Speed Mage** — the fastest caster alive (move, cast, and SP efficiency).

## v2.16.2 — Advanced weapon silhouettes

- Each advanced class now wields a **distinct weapon**: Dual Blade fights with **two swords**, Magic Swordsman glows with a **purple mana blade**, Crossbow Master carries a **golden crossbow**, Twin Archer draws a **double bow**, Battle Mage adds a **blade to the staff**, and Speed Mage channels a **blue orb**.

## v2.16.1 — Advanced classes look the part

- Advanced classes now **look different**: each subclass has its own **outfit colors**, a pulsing **aura** in its signature color, and **colored basic-attack effects** (Dual Blade & Twin Archer even strike twice). Now it actually feels like an advancement!

## v2.16.0 — Class Advancement (Phase 1)

- **Second-tier classes!** At **level 40**, complete the advancement quest (slay 300 monsters + 3 bosses after Lv40), then visit the new **Class Master** in town to choose your path. **The choice is permanent.**
  - **Warrior** → Dual Blade / Magic Swordsman
  - **Archer** → Crossbow Master / Twin Archer
  - **Mage** → Battle Mage / Speed Mage
  - *(Axeman advancement coming soon)*
- Each advancement grants permanent stat gains suited to its style (HP / ATK / DEF / speed / evasion / SP efficiency) and changes your displayed class.
- *(Phase 2 will add each subclass's unique skills & ultimate.)*

## v2.15.1 — Ultimate timing & readout

- **Cooldown now starts *after* the effect ends** — the ultimate's cooldown timer only begins once its duration (15s / 60s) runs out, so total downtime is duration + cooldown.
- **Active-ultimate label** — while an ultimate is running, a banner at the top shows its name and a live remaining-time countdown with a shrinking bar. Re-activating is blocked until it ends.

## v2.15.0 — Warrior ultimates reforged

- **R — Annihilator** — for **15 seconds, SP is unlimited**. Spam every skill nonstop, like an endless engine of destruction.
- **Ctrl+R — Superhuman** — for **60 seconds**: unlimited SP, **double damage**, and **maxed-out move & attack speed** — plus an instant hit dealing **50% of max HP to every enemy on the floor**.

## v2.14.0 — Gear, vision & UI polish

- **Vision helmets** — new head gear grants extended sight (Scout Helm, +4), and the rare **Helm of True Sight** reveals the entire floor.
- **No more fixed slow/curse traps or pressure plates** — those predictable, always-avoided hazards are gone. In their place, more **Mystery Runes** (random buff/debuff gambles).
- **No forced deposit** — returning to town no longer dumps your inventory into storage. Use storage manually when you want.
- **Item tooltips & comparison** — in the inventory, hover or select an item to see its full stats, and equipment shows a **green/red comparison** vs what you have equipped.
- **Detailed equipment screen** — the gear screen now lays out your full character stats (HP · ATK · DEF · EVA · Move · Attack Speed · Sight).

## v2.13.0 — Quality of life & dopamine

- **Soft death** — dying no longer ends your run. Press **R** to revive in town, then dive back to the floor you reached and try again.
- **Potion quick slots** — the quick bar (1–5) now holds **consumables only**, and identical potions **stack with a count** (no more wasted slots). Equip gear from the inventory (I).
- **Start with 5 Town Portals** — new characters carry 5 return scrolls (one stacked slot) to hop between town and dungeon.
- **Mystery Runes** — new gamble tiles scattered around: step on one for a **random** buff or debuff (speed↑ / attack↑ / slow / attack↓). Risk it?
- **Easier early bosses** — floor-5 boss dialed down to ~55% (ramping back to full by floor 25).

## v2.12.3 — Steam integration (achievements & leaderboards actually connect)

- **Bundled the missing Steam native libraries** (`steam_api64.dll`, `libsteam_api.dylib`, and a freshly-built universal `SteamworksPy.dylib` for macOS). Previously the builds shipped *without* these, so Steam never connected — achievements stayed local-only and leaderboards were always "offline".
- **Auto-writes `steam_appid.txt`** at startup (required by the Steam binding) and installs SteamworksPy on the macOS build.
- With this, Steam achievements should pop and global leaderboards should populate on a Steam-launched build.

## v2.12.2 — Ranking polish & Steam fix

- **Ranking arrows** now draw as real ◀▶ / ▲▼ icons (previously showed as boxes in the pixel font). ◀▶ changes the leaderboard, ▲▼ toggles Global/Friends.
- **Steam leaderboards** now reuse the achievements' Steam connection instead of initializing a second time (which likely caused the "offline" state), and Steam callbacks are pumped each frame so global results can arrive.

## v2.12.1 — Fix

- **Fixed** the Hall of Fame monument rendering as a long stretched pillar down the screen (a draw-height bug). It's now a compact marble stand.

## v2.12.0 — Global rankings (Hall of Fame)

Compare your runs with the whole world.

### Hall of Fame 🏆 (in town)
- A new **Hall of Fame** monument in town — press **E** to open the global rankings.
- **Leaderboards**: Deepest Floor (overall), Deepest Floor per class (Warrior / Archer / Mage), and Highest Level. Switch with **◀▶**, toggle **Global / Friends** with **▲▼**.
- Your best run is submitted automatically as you descend; your row is highlighted in the list.
- Powered by **Steam Leaderboards** — works offline too (shows your own record).

### Quality of life
- **Version shown on the title screen** (bottom-right) so you always know which build you're on.
- **Save in town, resume in town** — quitting from the village now brings you back to the village, not the dungeon.
- **A dedicated, peaceful town theme** now plays in the village instead of dungeon music.

## v2.11.0 — More achievements & full localization

Lots more to chase, in every language.

### 14 new achievements 🏆
- **Level milestones** — Seasoned (40), Elite (60), Champion (80), Pinnacle (max 99).
- **Deep descent** — Centurion Depth (100), Deep Delver (250), Halfway Down (500), The Bottom (999).
- **Village life** — First Harvest, Green Thumb (100 crops), First Catch, Master Angler (50 fish), Ranch Hand, and Homesteader (farm + fish + ranch).
- Brings the total to **38 achievements**, each with a hand-drawn icon (unlocked + locked).

### Localized 🌏
- All achievement names & descriptions localized to **Korean, Japanese, Simplified Chinese, and Russian** (via Steam localization tokens).

## v2.10.0 — Co-op content & Achievements

Playing together now has stakes, goals, and bragging rights.

### Never leave a friend behind 🩹
- **Downed & revive.** In co-op, dropping to 0 HP no longer ends your run — you're **downed** with a 45-second timer. A partner just has to **stand next to you** and a revive meter fills; you're back on your feet at 40% HP.
- **Second chances.** If the timer runs out you become a **spectator** instead of dying outright — and you **revive automatically when the party descends** to the next floor.
- **Party wipe only when everyone's down.** The run ends only if the whole party is downed/out at once.

### Mercenary Guild Board 📜 (multiplayer only)
- A new **board in town** hands out **co-op-only contracts** — active only while you're in a party:
  - **Party Bounty** — slay 50 monsters together → gold + enhancement stones
  - **Bond of Brothers** — revive fallen allies 3 times → accessory
  - **Descent Together** — reach floor 5 as a party → big reward
- Contracts unlock in a chain and their progress rides along in your save.

### Steam Achievements 🏆
- **8 new achievements**, most of them co-op:
  - *Hundred Together* (100 co-op kills), *Brother in Arms* (first revive), *Leave No One Behind* (10 revives)
  - *An Hour Together / Steadfast Duo / Party Forever* (1h / 3h / 5h of co-op)
  - *Guild's Trust* (first board contract), *Giant Slayers* (kill a boss in co-op)

> Achievements unlock locally and sync to Steam automatically. New API names must be registered on the Steamworks partner site: `ACH_COOP_KILLS_100`, `ACH_REVIVE`, `ACH_REVIVE_10`, `ACH_COOP_1H`, `ACH_COOP_3H`, `ACH_COOP_5H`, `ACH_COOP_QUEST`, `ACH_COOP_BOSS`.

## v2.9.5 — Multiplayer (beta): See your ally fight

- **Party combat effects are now shared** — when your co-op partner swings, shoots, or casts, you see their attack pose and the swing/bolt effect, not just a standing avatar. Makes fighting side by side feel alive.

## v2.9.4 — Multiplayer (beta): Recent codes & help

- **Remembers your recent invite codes** — they're saved between sessions, pre-filled on the multiplayer screen, and one click re-enters one.
- **How-to-play window** — tap the ⓘ on the multiplayer screen for a quick guide to hosting, joining, and playing together.

## v2.9.3 — Multiplayer (beta): Friendlier join

- **Character-select popup** after hosting or joining — pick your hero from a focused window. No characters yet? It tells you to create one first (and lets you).
- **Invite codes auto-uppercase** as you type, so they're easier to enter.

## v2.9.2 — Multiplayer (beta): Co-op join fix

- **Fixed** co-op joining via **Continue** (an existing character): the town and dungeon could render on top of each other and players couldn't see one another. Continuing a save now resets the scene cleanly before entering the shared town.

## v2.9.1 — Multiplayer (beta): Invite Codes & Easy Join

Joining a friend just got a lot friendlier.

### Invite codes 🎟️
- **Share a 13-character code instead of an IP.** Host a game and your invite code appears on screen — hand it to a friend, they paste it in, done.
- **Auto internet access (UPnP).** When you host, the game asks your router to open the door automatically. If it works, your code is reachable **over the internet**; if not, you'll see it's same-network only. No manual port forwarding.

### Join anytime 🚪
- **Join from inside the town** — no need to be on the title screen. Open the pause menu (**ESC**) → **Join a friend** → paste the code, and you're pulled straight into co-op.
- **Copy your code from the pause menu** — hosts can grab their invite code again mid-game with one click.

> Still LAN / direct-connect under the hood; UPnP extends it to the internet on supported routers. True everywhere-play (CGNAT, no port-forward) arrives with Steam networking.

## v2.9.0 — Multiplayer (beta): Dungeon Co-op

Take the fight downstairs together. The dungeon is now a two-player hunt.

### Descend as a party ⚔️
- From the shared town, the **host steps through the portal** and the whole party drops into the dungeon — at the **lowest floor** anyone in the party has reached, so no one is left behind.
- **Host leads the descent** — step through the door and everyone travels to the next floor together, on the exact same map.
- **Shared vision** — the fog of war lifts around every party member, on the map and the minimap.

### Hunt together 🩸
- **Enemies are in sync** — you both see the same monsters in the same place, and you both chip them down. Whoever lands the blow, the kill counts for the party.
- **Enemies fight back on both fronts** — monsters chase the nearest hero, so split up at your own risk.
- **Tougher by design** — dungeon monsters hit harder and take more punishment in co-op, and **bosses are extra beefy**.

### Share the spoils 💰
- **Loot drops for everyone to see** — walk over an item to grab it; no double-picks, first one there keeps it.
- **Gold and XP are shared** — every kill pays out to the whole party, so you both level up together.
- **Destructible cracked walls stay in sync** — bomb one open and the passage appears for both of you.

> Dungeon co-op is beta and runs over LAN / direct connect (`mp-host` / `mp-join`). Steam friend-invites are still on the way.

## v2.8.0 — Multiplayer (beta): Town Co-op

Bring a friend into town. The homestead is better with two.

### Play together 🤝
- **Multiplayer (beta)** button on the main menu — **Host a game** or **Join a friend** by IP, then pick your save character and drop into a shared town.
- **LAN / direct connect** — no dedicated server needed. Host and join over the same network (TCP), with your friend appearing right beside you, nameplate and all.
- Also launchable from the terminal: `mp-host` / `mp-join <ip>`.

### Shared homestead 🌱🐄
- **One farm, tended together** — plant, water, and harvest the same plots. Whoever harvests keeps the crop; the field stays in sync for both of you.
- **Shared ranch** — buy, feed, and sell livestock together; pens update live for everyone.
- The host owns the world state, so crops and animals never desync.

### Town chat 💬
- Press **T** to chat — messages pop as **speech bubbles** over each hero's head and scroll in a feed at the bottom.

> Multiplayer is an early beta focused on the town. Dungeon co-op and Steam friend-invites are on the way.

## v2.7.0 — Homestead: Farm, Fish & Ranch

The town becomes a life of its own — grow crops, cast a line, and raise a barnyard of your own.

### Interactive Farm 🌱
- **Tend your plots** from a popup menu: sow, water, harvest, or uproot. Watered crops grow each time you return to town.
- **Harvest into food** — wheat/tomato/pumpkin/carrot become healing dishes (bread, soup, pie, stew), plus gold and a farming milestone bonus every few harvests.
- **Seeds** drop from harvests — use a seed on an empty plot to plant that exact crop.
- **Rare plants** occasionally sprout at harvest (higher-value crops = better odds).
- **Ancient Altar** — offer rare plants for **permanent ATK / DEF / EVA boosts** that survive death and carry across runs, or exchange a stockpile for a tier of **ancient weapons**.

### Fishing 🎣
- **Riverbank fishing** — a two-beat minigame: hook on the bite, then **reel by landing the cursor in the green band**. Rarer fish reel faster and narrower.
- **6 species across 4 grades** (common → legendary Ancient Fish), with weighted rarity and grade payouts.
- **Grilled fish** joins your harvest stash as a healing food.
- **Old Angler** by the river trades your catch (by grade) for **ancient relic accessories**.

### Ranch & Chicken Farm 🐄🐔
- **A fenced ranch** on the east side — buy livestock (chicken, sheep, pig, cow), feed them, and **collect eggs, milk, mutton, and pork belly**. Animals stay for renewable production.
- **A lively chicken farm** next door with a wandering flock.
- Pen animals now **mill about** their pens instead of standing still — and none of them escape the fence anymore.

### Inventory Categories 📦
- **Category tabs** — All / Gear / Items / Harvest, with count badges and per-item accents. Switch by mouse, Tab, or the arrow keys.
- **Real item icons** — fish, seeds, bread, pie, egg, milk, and meat no longer all look like potions.

## v2.6.0 — The Axeman & a Living Town

A brand-new class, and a town that finally feels like a real place to call home.

### New Class: Axeman 🪓
- **Axeman** — a fourth class wielding a two-handed axe: massive damage but a slow, weighty swing. Unlock him by reaching **Level 30** and clearing **floor 40**.
  - **W · Axe Throw**: hurl your axe in a line; it sticks in the ground. Walk over it to **recall it (+SP) and throw again instantly** — or throw a fresh one and eat a 10s cooldown.
  - **S · Berserk**: surge your attack speed + lifesteal to offset the slow swing.
  - **D · Leap Smash**: leap in and smash the landing zone.
  - **R · Ragnarok**: a few seconds of **full invincibility** — boosted move speed, a burning aura that damages everything you touch, and mid-range sweeping swings.
  - Physical enhanced skills replacing the mage combos: **Axe Storm**, **Earthbreaker**, **Berserker's Charge**.
  - Heavy dedicated axe-swing animation with dust and shockwaves.
- **Pet summon key (V)** — summon or dismiss your pet on demand.

### A Living Town 🏘️
- **Massively expanded town** (roughly 4× bigger) with districts, streets, a **river crossed by bridges**, a central fountain and hero **statue**, and crowds of wandering townsfolk.
- **Farm** with crop fields and animals — chickens, cows, sheep, and pigs roaming about.
- **Varied houses**: triangular roofs, doors, and big windows — some L-shaped, each with a unique interior. Walk through the door and the roof lifts to reveal the room inside.
- **Themed interiors**: the inn, smithy (forge & anvil), the market stocked like a grocery, and the warehouse loaded with crates — each looks the part. **Shop signs** mark every store.

### Your Home 🏡
- **My Home** — your own house by the farm. Interact with the planning board to **redecorate** (5 interior styles: cozy, noble, rustic, study, garden), saved permanently.
- **Home storage** — stash up to **100 items** right from home.
- **Boss trophies** — clear boss floors and watch a shelf of trophies fill your home, one gem-topped cup per boss floor conquered.

### Quality of life
- **Storage stacking** — identical items now stack with a count (×N) on both the carried and stored sides.
- **Minimap** auto-scales for the big town and shows NPC markers.

## v2.5.0 — The Ever-Changing Depths

No two floors alike anymore — the dungeon now reshapes its very skeleton, hides gambles and vaults, and can collapse under your feet.

### A dungeon that's never the same twice
- **Alternate layout archetypes**: every floor is built from one of four skeletons — scattered **rooms**, organic **caverns**, a central **arena** with satellite rooms, or a grand **hall** gallery. Themes lean toward fitting shapes (nature → caves, fortresses → halls, tombs → arenas).
- **Loop connections**: extra corridors weave cycles into the map, so there's always a way to circle around, kite, and escape — no more dead-end trees.
- **Biome terrain**: swamps and sunken cities grow **water lakes**, forests scatter **trees and ponds**, and castles raise **pillared halls** — all guaranteed traversable.
- **Prefab set-pieces**: hand-built special rooms drop in occasionally — a rounded **arena**, a **pillar cross-hall** of cover, or a **moat treasure room** (island loot across a water moat with a bridge).

### Risk, reward, and ruin
- **Mystery Box (collapse altar)**: touch it and gamble — **jackpot** (a gold windfall or a rare weapon) or **collapse**, where the floor caves in from the far edges and you sprint for the stairs. Escape to claim gold, stones, and gear; an exit arrow and a fully revealed map keep you oriented.
- **Keys & locked vaults**: find a **Vault Key** on the floor to open a sealed treasure room packed with premium gear. Optional, and never in your way to the exit.
- **Bombs & cracked walls**: throw bombs to blast open **cracked walls**, revealing hidden treasure rooms and secret shortcuts — and your finishers and ultimates shatter them too.

### Quality of life
- **Small name labels** (localized) on interactive objects — Mystery Boxes, locked vaults, shops, and nearby items — so you always know what you're looking at.

## v2.4.0 — The Mage & the Living Dungeon

A whole new class, dungeons that fight back, and a reason to descend forever.

### New Class: Mage 🧙
- **Mage** — a fragile, high-ceiling ranged caster built around **damage-over-time and summons**.
  - **Arcane bolts**: free elemental attacks that ignite enemies (burn DoT).
  - **W · Arcane Blink**: teleport *through walls* up to range — at a high SP cost.
  - **A · Flame Pool**: lay a burning zone on the ground; enemies inside keep taking damage.
  - **D · Summon Familiar**: conjure spirits that auto-attack nearby foes for a while.
  - **R · Inferno**: blanket the whole screen in flame zones, ignite every enemy, and call in extra familiars.
  - Robe-and-staff look on the creation screen and in the dungeon.
- **New systems** powering it: enemy **burn** status, ground **DoT zones**, and temporary **summons**.

### Class Unlocks
- **Archer and Mage are now earned**: start as the Warrior, reach **Level 20** and **clear floor 20**, and both advanced classes unlock permanently — with a celebratory banner.
- The character creation screen shows locked classes with their unlock requirement.

### The Living Dungeon (dynamic hazards)
- **Shifting walls**: real-time gates in corridors open and close on a rhythm — read the pattern and dash through. Get caught and you're crushed (and shoved aside).
- **Cyclic spike traps** in narrow passages: they rise and retract — time your run or take the hit.
- **Web** (slow) and **curse** (attack-down) traps in open rooms.
- **Pressure plates**: step on one for a gold + power reward that also flings every shifting wall open for a few seconds.
- **Conveyor belts** are faster and stronger — and can shove you straight into a trap.

### Dungeon Journal, reimagined
- The conquest journal (**J**) is now a **visual gallery**: each region is a palette-driven mini dungeon-door scene, with clear counts, region colors, and locked regions shown behind a padlock.

### Descend deeper, grow stronger
- **Dungeon Tokens**: every floor cleared grants a token (Attack / Haste / Guard) that passively boosts your stats while held (with sensible caps).
- **Class supply**: every 10 floors drops a piece of class-appropriate gear, scaled to your depth.

### Fixes & polish
- Fixed a **purple rectangle artifact** behind the COMBO label (and the quest-clear banner) on some systems.
- Refreshed all **Steam store art** with 2D pixel key art of the real hero and enemy roster.

## v2.1.0 — Quests & the Living Town

The town comes alive, and the villagers have stories to tell.

### Quests
- **Quest chains**: villagers now offer follow-up quests as you complete their first — Little Hans and Farmer Bram each have a two-part chain.
- **Villagers arrive as you descend**: new townsfolk appear as you reach deeper floors — Garo the Hunter (floor 5, elite bounties) and Scholar Isolde (floor 8, reach floor 20).
- **New objective type**: elite-variant bounties (`kill_elite`).
- **Classified Quest Log** (Q): grouped into In Progress / Available / Locked (with `???` teasers showing unlock conditions) / Completed.
- **Flashy quest clear**: reporting a finished quest triggers a full-screen QUEST CLEAR celebration — golden radial burst, reward banner, gold flash, slow motion, particle fountain, and fanfare.

### A Living Town
- **5× bigger town** (66×49): multiple shops and houses, a central fountain, a park, lamps, flower beds, market stalls, benches, and barrels. The camera pans as you explore.
- **NPCs wander naturally** around their homes, pausing to look your way when you come close.
- **Small talk**: chat with villagers even when they have no quest — each has their own personality, fully localized in all 5 languages.
- **Fixed**: the return portal and an NPC could occupy the same tile.

## v2.0.0 — The Town & Action Overhaul

The biggest update yet: real action combat, a living town hub, quests, durability, and a full loot-dopamine layer. The game loop is transformed.

### Action Combat 2.0
- **3-hit combo chains**: rapid Space attacks flow slash → reverse slash → **finisher** (160% + knockback + impact frame). Bump attacks join the chain.
- **Command actions**: forward+Space = **Lunge Thrust** (dash-in, 2-tile pierce), back+Space = **Backstep Slash** (hit & retreat with afterimages).
- **Drive Cancel**: 3-pip gauge — cancel attack recovery into any skill for +15% damage. "CANCEL!" callout, afterimages, spark.
- **Stamina (SP) system**: every attack/skill costs SP shown next to HP; regen is delayed 0.9s (spam = exhaustion). **Kills refund SP** (15% / elite 30% / boss 100%) — skilled aggression sustains itself. W/A/S/D skills now cost SP instead of cooldowns; Efficiency enchant reduces SP costs; SP cost reduction also scales with level and light gear.
- Procedural action poses + sword smear frames + screen-wide impact flash — no sprite sheets needed.

### Town Hub & Quests
- **Town**: buildings, well, lamps, trees — Inn (rest + max-HP meal buff), Smithy (gold enhance + repair), General Store (cheap consumables), and a **Personal Stash** (permanent storage that survives death, expandable 30→90 slots).
- **Portals**: Return Scrolls or boss kills open a town portal; your dungeon (enemies, map, position) is preserved exactly and resumes on re-entry. Loot auto-banks on arrival.
- **Quests**: villagers offer story quests via a dialogue box (accept/decline, typewriter text) — monster culling, centipede menace, rescue the girl on floor 10. Press **Q** for the quest log; objectives track in real time on screen.

### Durability
- Armor wears when you get hit (dodges don't), weapons wear when you land hits. Broken gear stays but stops working until repaired (smith gold repair / field Repair Kits). Durability bars everywhere: equipment screen, side panel, smithy, inventory, stash.

### Dopamine Layer
- Loot explosions with **coin magnetism** and rolling gold counter; item drops reveal with **rarity ceremonies** (common→epic light pillars, chimes, colored name pops) and magnet pickup.
- **Treasure Goblins** (catch before they flee = JACKPOT), breakable pots/crates, **OVERKILL!** callouts, boss/last-kill **slow motion**, soft radial glow particles.

### Balance & Misc
- Arcane SP gauge removed (superseded by Stamina); arcane chain now costs 50 SP.
- Equipment overlay visuals removed per feedback — replaced by equip burst effects.
- New sounds (14), new items (Return Scroll, Repair Kit), 374 UI strings × 5 languages.

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
