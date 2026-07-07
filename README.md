# Wizard Typing Duel v0.4.0

A tiny old-school magical typing duel made with Python + pygame.

## What changed in v0.4.0

- Full visual UI overhaul inspired by the polished mockups.
- Better main menu with stronger title, difficulty cards, footer controls and clear start button.
- Better gameplay HUD with structured HP, score, combo, mana, ability cards and input command bar.
- Ability buttons clearly show hotkeys `1`, `2`, `3`, effect and mana cost.
- Spell lanes moved lower so the HUD no longer fights with incoming spells.
- Fullscreen scaling now uses crisp pixel scaling instead of blurry smooth scaling.


A tiny old-school pygame typing duel prototype.

Type spell words before they reach your wizard. Destroy spells, build combo, gain mana, cast abilities, survive longer, and defeat boss spells.

## Install

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python wizard_typing_duel.py
```

## Controls

### In game
- Type spell words to destroy incoming spells.
- `1` — Barrier: blocks the next incoming spell.
- `2` — Slow Time: slows enemy spells.
- `3` — Arcane Blast: hits several spells on screen.
- `Esc` — pause menu.
- `F1` — help / controls.
- `F11` — fullscreen / windowed.
- `Backspace` — delete last typed character.
- `Enter` — clear input.

### Pause menu
- Continue
- Restart Run
- Main Menu
- Quit Game

Keyboard shortcuts in pause menu:
- `Esc`, `Enter`, `Space` — continue
- `R` — restart run
- `M` — main menu
- `Q` — quit game

### Level Up
- Click an upgrade card or press `A`, `S`, `D`.

## Notes

This is still a prototype. The goal of v0.4.0 is clarity: the player should understand abilities, pause menu, restart, and help without reading the source code.


## Display

- The window is resizable.
- The game keeps a fixed 16:9 virtual canvas and scales it to the current window.
- Black/ dark borders may appear on ultrawide or tall monitors to preserve proportions.
- Mouse clicks are converted correctly after resizing.
- `F11` toggles fullscreen/windowed mode.
