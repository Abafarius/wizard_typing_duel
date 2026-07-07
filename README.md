# Wizard Typing Duel

Версия: **v0.3.0 — Core Fun Update**

Маленькая олдскульная typing-аркада на Python + pygame: печатай слова летящих заклинаний, копи ману, кастуй способности и выбирай улучшения после повышения уровня.

## Запуск

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install pygame
python wizard_typing_duel.py
```

## Управление

### Меню

- `1` — Easy
- `2` — Normal
- `3` — Hard
- `Space` / `Enter` — старт
- `Esc` — выход

### Игра

- Печатай слова над заклинаниями
- `Backspace` — удалить символ
- `Enter` — очистить ввод
- `1` — Barrier, блокирует входящий удар
- `2` — Slow Time, замедляет все заклинания
- `3` — Arcane Blast, уничтожает несколько ближайших заклинаний
- `P` — пауза

### Level Up

После повышения уровня игра ставится на паузу и предлагает 3 руны:

- `A` — первая руна
- `S` — вторая руна
- `D` — третья руна

## Что нового в v0.3.0

- Мана
- Способности: Barrier, Slow Time, Arcane Blast
- Система апгрейдов после повышения уровня
- Новые типы заклинаний: Curse, Mirror, Mana
- Ошибки теперь ломают комбо, сжигают ману и могут вызвать curse-заклинание
- Локальный high score в `save_data.json`
- Пауза
- Больше эффектов и floating text

## Баланс

Главные настройки находятся в начале `wizard_typing_duel.py`:

```python
DIFFICULTIES = {...}
SHORT_WORDS = [...]
MEDIUM_WORDS = [...]
HARD_WORDS = [...]
BOSS_PHRASES = [...]
```

