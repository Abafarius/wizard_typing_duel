# Wizard Typing Duel v0.3.2

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

This is still a prototype. The goal of v0.3.2 is clarity: the player should understand abilities, pause menu, restart, and help without reading the source code.
