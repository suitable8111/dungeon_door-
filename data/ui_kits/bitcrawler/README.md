# BitCrawler UI Kit

A high-fidelity interactive HTML prototype of the BitCrawler roguelike game UI.

## Files

- `index.html` — Main interactive prototype (all screens clickable)
- `components/` — JSX component files loaded by index.html

## Screens Covered

1. **Main Menu** — Title, New Game / Continue / Settings / Quit, starfield bg
2. **Gameplay** — Top bar, dungeon viewport (procedural tile grid), right HUD panel, message log
3. **Shop Modal** — Gold-bordered overlay on gameplay
4. **Pause Menu** — Semi-transparent overlay with settings
5. **Game Over** — Black overlay with records

## Design Notes

- All colors from `../../colors_and_type.css`
- Sprites drawn via HTML Canvas (pixel art, image-rendering: pixelated)
- No external image assets — fully procedural
- Resolution: 1024×768 (scaled to fit viewport)
- Korean/English bilingual UI
