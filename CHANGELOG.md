# Changelog

## v0.3.0 — Core Fun Update

### Added
- Mana system.
- Ability hotkeys:
  - `1` Barrier
  - `2` Slow Time
  - `3` Arcane Blast
- Level-up upgrade screen with 3 rune choices.
- Spell types:
  - Normal
  - Hard
  - Boss
  - Curse
  - Mirror
  - Mana
- Error punishment:
  - Breaks combo
  - Burns mana
  - Every third typo can spawn a curse spell
- Local high score saved in `save_data.json`.
- Pause screen.
- Floating combat text.
- Enemy caster silhouette.

### Changed
- Balance now supports more pressure and recovery tools.
- Boss and special spells give extra score/mana.
- Game loop now has more states: menu, playing, upgrade, paused, gameover.

### Status
Experimental fun build. Many mechanics are intentionally added quickly for testing.

## v0.2.0 — Gameplay Balance MVP

### Added
- Difficulty selection: Easy, Normal, Hard
- Expanded word pools
- Boss spells with longer phrases
- Combo system
- Level scaling
- Spell limit on screen
- Highlighting for the currently typed spell

### Changed
- Rebalanced spell speed
- Rebalanced spawn frequency
- Health and difficulty settings moved into config
