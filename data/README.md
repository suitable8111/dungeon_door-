# BitCrawler Design System

**Project:** BitCrawler (codename: `dungeon_door`)
**Genre:** 2D grid-based roguelike game
**Visual Style:** 16×16 / 32×32 pixel art — "Minecraft 2D" aesthetic
**Platform:** Python + Pygame-CE, targeting Steam release
**Language:** Korean (primary), English (secondary)
**Resolution:** 1024×768

---

## Sources

- **GitHub Repo:** `suitable8111/dungeon_door-` (branch: `main`)
  - `core/constants.py` — full color palette + layout constants
  - `core/game.py` — all sprite drawing functions (procedural pixel art)
  - `ui/hud.py` — all UI rendering (HUD, menus, shop, pause, game over)
  - `core/lang.py` — bilingual string table (Korean / English)
  - `data/enemies.json` — monster stats + colors
  - `data/items.json` — item definitions + colors
  - `roguelike_dev_plan.md` — dev plan, roadmap

No external image assets exist — all graphics are procedurally drawn with `pygame.draw`.

---

## Products

One product: **BitCrawler** — a single-player desktop roguelike game.

### Core Screens
1. **Main Menu** — Title "DUNGEON DOOR", New Game / Continue / Settings / Quit
2. **Gameplay** — Top bar (floor/gold/HP), game viewport (25×19 tiles), right panel (stats/inventory/skills/minimap), bottom message log
3. **Shop** — Overlay modal with gold-bordered panel
4. **Pause Menu** — Overlay with settings (volume, fullscreen, language)
5. **Game Over** — Black overlay with best records display

---

## CONTENT FUNDAMENTALS

### Tone & Voice
- **Direct and functional.** UI copy is terse — no fluff. "Floor 3에 도착했습니다." not "You have arrived at Floor 3!"
- **Korean-first.** All strings authored in Korean; English is a translation layer. Korean uses formal polite endings (합쇼체 / 해요체 mixed).
- **Action-focused.** Combat messages lead with the action: `▶ 고블린에게 5 피해` (Arrow glyph + target + damage).
- **Celebratory moments use unicode symbols:** `★` for crits/boss kills, `✓` for saves, `✦` for teleport, `⚡` for dash, `✨` for heal.
- **No emoji in core UI** — only emoji-style unicode in game log messages (`🌀` for whirlwind).
- **Numbers are always inline** with context: `+15 XP`, `-6 G`, `HP +30`.
- **Casing:** ALL CAPS for game-over/boss labels (`GAME OVER`, `★ BOSS`); Title Case for menu buttons; lowercase for stat labels (`ATK`, `DEF` are uppercase abbreviations).
- **I vs. You:** Third-person and second-person mixed. System messages use second person implied ("Floor 3에 도착했습니다" = "you arrived"). Items use first person implied.

### Copy Examples
| Context | Korean | English |
|---|---|---|
| Welcome | `Dungeon Door에 오신 걸 환영합니다!` | `Welcome to Dungeon Door!` |
| Level up | `레벨업! Lv.3  HP 회복!` | `Level Up! Lv.3  HP restored!` |
| Crit | `★ 치명타! 오크에게 18 피해!` | `★ Crit! Orc hit for 18!` |
| Shop empty | `품절입니다.` | `Sold out.` |
| Auto save | `✓ 자동 저장됨` | `✓ Auto-saved` |

---

## VISUAL FOUNDATIONS

### Color System
All colors defined in `core/constants.py`. Deep midnight navy/purple base, with gold as the primary accent.

**Background / Structure**
- UI Background: `#0E0E18` (rgb 14,14,24) — near-black with blue tint
- Top/Right panels: `#0A0A14` — slightly darker
- Panel border primary: `#41415F` (rgb 65,65,95) — muted indigo
- Panel border inner: `#1A1A30` — near-black inset

**Dungeon Tiles**
- Wall lit: `#46465C` | Wall dim: `#232332`
- Floor lit: `#2D2D3E` | Floor dim: `#191923`
- Floor edge: `#3A3A4E`
- Stairs: `#D2AF55` (gold) | dim: `#695828`

**Accent Colors**
- Gold (player/currency): `#EBB93C` — warm amber gold; highlight `#FFD769`
- HP bar: `#D73A3A` (red) on `#481414` (dark red bg)
- XP bar: `#3CA5E1` (sky blue) on `#123452` (dark blue bg)
- Skill ready: `#64B4FF` (light blue)
- Skill cooldown: `#3C3C5A` (dim indigo)
- Shop/Good events: `#3CD278` (green)
- Boss/Magic: `#C850DC` (vivid purple)

**Message Log Colors**
- Info: `#C8C8B4` (warm off-white)
- Warning/Combat: `#EBA532` (amber)
- Good/Pickup: `#5FD75F` (green)
- Bad/Damage: `#D74E4E` (red)

### Typography
No custom font — uses system Korean fonts (AppleSDGothicNeo on macOS, Malgun Gothic on Windows, NanumGothic on Linux). English fallback: `sans-serif`.

**Scale** (Pygame font sizes → CSS equivalent):
- `font_sm`: 13px — stat labels, message log, hints
- `font_md`: 15px — button labels, section headers, inventory
- `font_lg`: 30px — menu section titles, floor name, pause title
- `font_xl`: 46px — "DUNGEON DOOR" title, "GAME OVER"

For web/HTML design system: use **Press Start 2P** (pixel bitmap feel) for display/title, and **Noto Sans KR** for Korean body text.

### Layout
Fixed 1024×768 game window. Strict panel grid:
- Top bar: full width, 32px tall
- Right panel: 224px wide, full height
- Game viewport: 800×608px (25×19 tiles at 32px each)
- Bottom message log: 800×128px

### Backgrounds
- **Menu background:** Procedurally generated starfield (random 1×1 white dots on `#05050C`) + dungeon floor tiles in lower 2/5 (dark stone grid with subtle grouting)
- **In-game:** Pure black canvas (`#000000`) with tile-rendered dungeon
- **Overlays (shop/pause/game-over):** Semi-transparent black `rgba(0,0,0,0.78)` over gameplay
- No photography, no textures, no gradients (except HP bar color interpolation)

### Animation & Motion
- **Floor transition:** Fade to black → load → fade back in. Speed: 12 alpha/frame at 60fps ≈ 21 frames (~350ms)
- **Screen shake:** Random pixel offset, intensity 2–6px, duration 150–400ms, fades linearly
- **Lunge anim:** Attack direction offset, 240ms
- **Slash anim:** Fan of 5 lines + impact ring, 280ms. Normal = `#FFEB50` (yellow), Crit = `#FF5050` (red)
- **Hit flash:** Tile color flash + floating damage number, 480ms
- **Bolt anim:** Ranged attack projectile (wizard/dragon), color-coded
- No easing specified — linear timing implied throughout
- No idle/ambient animations

### Hover & Interaction States
Buttons use three states defined in `_btn_colors()`:
- **Default:** `#0E0E1A` bg, `#2E2C46` border, `#A0A0B4` text
- **Hovered:** `#16162A` bg, `#696494` border, white text
- **Active/Selected:** `#2A240A` bg, `#EBB93C` (gold) border, gold text — always shows `▶` arrow prefix
- **Danger (quit):** Red tints — default `#120A0A` bg, `#501E1E` border; hover darker red; active bright red

### Borders & Cards
- All panels: 2px solid border, color `#41415F`, border-radius 0 (square pixel-art corners) or `border_radius=4` for buttons
- Double-border pattern: outer 2px primary, inner 1px darker (`#1A1A30`) offset by 3px — creates inset bevel
- Section headers: 20px tall dark strip (`#16162A`) with bottom line separator
- No drop shadows on panels — instead solid dark borders create depth

### Corner Radii
- Panels/modals: **0px** (sharp pixel-art)
- Buttons: **4px** (slight rounding only)
- Bars (HP/XP/skill): **0px** (flat rectangles)

### Item Colors
- Consumables (potions): Reds `#D23C3C`–`#E65050`
- Weapons: Silver `#B4B9CD`–`#CDD2E6`
- Armor: Browns `#A07846` / Silvers `#A0A5B9`–`#C8CDD7`
- Gold/Currency: `#EBB93C`
- Special/Magic: Purple `#B464DC`, Teal `#64C8A0`

### Use of Transparency & Blur
- **Transparency:** Modal overlays only — `rgba(0,0,0,200/255)` ≈ 78% opacity
- **No blur** anywhere — crisp pixel rendering throughout
- Panel backgrounds use `SRCALPHA` surfaces with alpha 222/255 ≈ 87%

### Imagery
All graphics procedural — no photographs, no illustrations, no external assets. Sprites are 32×32 pixel art drawn with basic shapes (rect, polygon, circle, ellipse). Color palette per entity is warm (player: gold), cool (dungeon: blue-gray), and vivid per monster type.

---

## ICONOGRAPHY

No icon font or SVG icon set. All iconography is:
1. **Unicode glyphs** used as inline icons in text: `▶` (selection cursor), `★` (boss/crit), `✓` (save), `▲`/`▼` (minimap stairs), `⚡`, `🌀`, `✨`, `✦`
2. **Procedurally drawn icons** in Python (gear icon `_draw_gear()`, X icon `_draw_x_icon()`)
3. **Pixel-art sprites** for all game entities (player, monsters, items) — purely code-generated

For the HTML design system, we substitute with matching CDN icons from **Lucide Icons** (thin stroke, clean) where needed for UI chrome, and use the same unicode glyphs for in-game message styling.

No logo SVG exists — the game "logo" is the title text `DUNGEON` + `DOOR` rendered in the xl font (46px) with gold color on the menu screen, plus a 32×32 procedural pixel icon (gold knight helmet + sword).

---

## File Index

```
README.md                        — This file; full design system documentation
colors_and_type.css              — CSS variables for all colors, typography, spacing
SKILL.md                         — Agent skill definition

assets/                          — Visual assets (procedurally-sourced)
  icon_helmet.svg                — 32×32 knight helmet icon (SVG recreation)
  icon_sword.svg                 — Sword icon
  icon_shield.svg                — Shield icon

preview/                         — Design system card previews (registered in Design System tab)
  colors_base.html               — Base color palette
  colors_dungeon.html            — Dungeon tile colors
  colors_semantic.html           — Semantic / message colors
  colors_items.html              — Item type colors
  type_scale.html                — Typography scale specimen
  type_specimens.html            — In-game text specimens
  spacing_layout.html            — Layout grid + spacing tokens
  spacing_bars.html              — HP/XP/skill bar patterns
  components_buttons.html        — Button states
  components_panels.html         — Panel / modal chrome
  components_hud.html            — HUD right panel
  components_messages.html       — Message log component
  brand_title.html               — Main menu title treatment
  brand_sprites.html             — Entity sprite showcase

ui_kits/
  bitcrawler/
    README.md                    — UI kit notes
    index.html                   — Interactive game UI prototype
    components/
      HUD.jsx                    — Right panel HUD
      TopBar.jsx                 — Top bar
      MessageLog.jsx             — Bottom message log
      MenuScreen.jsx             — Main menu
      GameOverScreen.jsx         — Game over overlay
      ShopModal.jsx              — Shop overlay
      PauseMenu.jsx              — Pause menu overlay
      DungeonView.jsx            — Tile grid renderer
```
