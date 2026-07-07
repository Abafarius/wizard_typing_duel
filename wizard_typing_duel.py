import json
import math
import os
import random
import sys
from dataclasses import dataclass

import pygame

# Wizard Typing Duel — v0.4.0 Visual UI Overhaul
# Controls:
# - Menu: 1 = Easy, 2 = Normal, 3 = Hard
# - Type spell words before they hit the wizard.
# - Playing: 1 = Barrier, 2 = Slow Time, 3 = Arcane Blast
# - Esc = pause menu
# - F1 = help / controls
# - F11 = fullscreen / windowed
# - Pause menu: Continue, Restart, Main Menu, Quit Game
# - Upgrade screen: A / S / D or mouse click = choose upgrade
# - Backspace = delete input, Enter = clear input

WIDTH, HEIGHT = 960, 540
FPS = 60
PLAYER_X = 120
CENTER_Y = HEIGHT // 2
SAVE_FILE = "save_data.json"

DIFFICULTIES = {
    "easy": {
        "label": "EASY",
        "health": 8,
        "base_spawn_delay": 1.90,
        "min_spawn_delay": 0.78,
        "speed_min": 58,
        "speed_max": 96,
        "speed_per_level": 6,
        "max_spells": 5,
        "level_every": 8,
        "boss_every": 13,
        "error_damage": 0,
    },
    "normal": {
        "label": "NORMAL",
        "health": 6,
        "base_spawn_delay": 1.55,
        "min_spawn_delay": 0.60,
        "speed_min": 76,
        "speed_max": 124,
        "speed_per_level": 9,
        "max_spells": 6,
        "level_every": 7,
        "boss_every": 10,
        "error_damage": 0,
    },
    "hard": {
        "label": "HARD",
        "health": 5,
        "base_spawn_delay": 1.22,
        "min_spawn_delay": 0.46,
        "speed_min": 98,
        "speed_max": 154,
        "speed_per_level": 12,
        "max_spells": 7,
        "level_every": 6,
        "boss_every": 8,
        "error_damage": 1,
    },
}

SHORT_WORDS = [
    "mana", "fire", "bolt", "hex", "nova", "rune", "mist", "frost", "spark",
    "curse", "ward", "ember", "blink", "flare", "void", "orb", "moon", "star",
    "ash", "ice", "doom", "light", "chaos", "glyph", "magic", "soul", "focus",
]

MEDIUM_WORDS = [
    "shield", "arcane", "fireball", "moonlight", "starlance", "crystal",
    "phantom", "thunder", "nightfall", "sunburst", "wardstone", "soulbind",
    "spellbreak", "witchfire", "runeblade", "dreamdust", "bloodmoon",
]

HARD_WORDS = [
    "astral prison", "silver eclipse", "forbidden rune", "mirror curse",
    "celestial spear", "shadow covenant", "obsidian circle", "dragon sigil",
    "forgotten spell", "crown of ashes", "silent cathedral",
]

BOSS_PHRASES = [
    "ancient dragon flame",
    "the moon obeys me",
    "break the cursed sigil",
    "storm above the tower",
    "no magic without sacrifice",
    "stars fall when i speak",
    "your keyboard betrays you",
]

CURSE_WORDS = [
    "backfire", "miscast", "panic", "silence", "doom mark", "red curse",
    "bad omen", "hex wound", "pain rune",
]

MANA_WORDS = [
    "ether", "clarity", "channel", "flow", "charge", "blue flame", "inner spark",
]

LANES = [245, 285, 325, 365]

SPELL_COLORS = {
    "normal": ((90, 70, 180), (185, 140, 255), (245, 235, 255)),
    "hard": ((70, 135, 190), (90, 195, 255), (210, 245, 255)),
    "boss": ((190, 55, 135), (255, 100, 185), (255, 190, 230)),
    "curse": ((165, 30, 45), (255, 80, 90), (255, 210, 210)),
    "mirror": ((45, 145, 125), (70, 230, 200), (220, 255, 245)),
    "mana": ((185, 145, 35), (255, 215, 80), (255, 245, 190)),
}

UPGRADE_POOL = [
    {
        "key": "ward",
        "title": "WARD HEART",
        "desc": "+1 max HP and heal 1",
    },
    {
        "key": "deep_mana",
        "title": "DEEP MANA",
        "desc": "+20 max mana and gain 20 mana",
    },
    {
        "key": "cheap_magic",
        "title": "CHEAP MAGIC",
        "desc": "Abilities cost 10% less",
    },
    {
        "key": "blast_mastery",
        "title": "BLAST MASTERY",
        "desc": "Arcane Blast hits +1 spell",
    },
    {
        "key": "barrier_mastery",
        "title": "BARRIER MASTERY",
        "desc": "Barrier lasts +2 seconds",
    },
    {
        "key": "chronomancy",
        "title": "CHRONOMANCY",
        "desc": "Slow Time lasts +1.5 seconds",
    },
    {
        "key": "focus",
        "title": "FOCUS",
        "desc": "More score and mana from combo",
    },
    {
        "key": "calm_mind",
        "title": "CALM MIND",
        "desc": "Spell spawn pressure reduced",
    },
    {
        "key": "vampiric_rune",
        "title": "VAMPIRIC RUNE",
        "desc": "Every 10 combo heals 1 HP",
    },
]


@dataclass
class Spell:
    text: str
    x: float
    y: float
    speed: float
    radius: int
    wobble: float
    spell_type: str = "normal"  # normal / hard / boss / curse / mirror / mana
    life_time: float = 0.0

    def update(self, dt: float, time_scale: float):
        self.life_time += dt
        self.x -= self.speed * dt * time_scale
        self.y += math.sin(pygame.time.get_ticks() * 0.004 + self.wobble) * 0.25

    def draw(self, screen, font, small_font, tiny_font, typed):
        is_targeted = bool(typed) and self.text.startswith(typed)
        aura_color, core_color, border_color = SPELL_COLORS.get(self.spell_type, SPELL_COLORS["normal"])

        pulse = 2 + math.sin(pygame.time.get_ticks() * 0.012 + self.wobble) * 2
        if self.spell_type == "curse":
            pulse += math.sin(pygame.time.get_ticks() * 0.03) * 3
        pygame.draw.circle(screen, aura_color, (int(self.x), int(self.y)), self.radius + int(pulse), 2)
        pygame.draw.circle(screen, core_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, border_color, (int(self.x - 4), int(self.y - 5)), max(3, self.radius // 4))

        if self.spell_type == "mirror":
            pygame.draw.line(screen, (220, 255, 245), (int(self.x - 18), int(self.y)), (int(self.x + 18), int(self.y)), 2)
            pygame.draw.line(screen, (220, 255, 245), (int(self.x), int(self.y - 18)), (int(self.x), int(self.y + 18)), 2)

        if is_targeted:
            pygame.draw.circle(screen, (255, 245, 170), (int(self.x), int(self.y)), self.radius + 8, 3)

        label_font = tiny_font if len(self.text) > 17 else small_font
        label = self.text
        text_color = (255, 245, 210)
        text = label_font.render(label, True, text_color)
        rect = text.get_rect(center=(int(self.x), int(self.y - self.radius - 18)))
        pad = 6
        bg = rect.inflate(pad * 2, pad)
        bg_color = (25, 18, 45) if not is_targeted else (60, 48, 25)
        border = (100, 85, 190) if not is_targeted else (255, 220, 120)
        pygame.draw.rect(screen, bg_color, bg, border_radius=8)
        pygame.draw.rect(screen, border, bg, 1, border_radius=8)
        screen.blit(text, rect)

        if self.spell_type in ("boss", "curse", "mirror", "mana"):
            tag = {
                "boss": "BOSS",
                "curse": "CURSE",
                "mirror": "MIRROR",
                "mana": "MANA",
            }[self.spell_type]
            tag_surf = tiny_font.render(tag, True, border_color)
            screen.blit(tag_surf, tag_surf.get_rect(center=(int(self.x), int(self.y + self.radius + 16))))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wizard Typing Duel v0.4.0")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.window_w, self.window_h = self.screen.get_size()
        self.scale = 1.0
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_w = WIDTH
        self.viewport_h = HEIGHT
        self.fullscreen = False
        self.last_window_size = (WIDTH, HEIGHT)
        self.update_viewport()
        self.clock = pygame.time.Clock()
        # Use common system fonts. They stay readable on most Windows machines.
        self.font_logo = pygame.font.SysFont("georgia", 56, bold=True)
        self.font_big = pygame.font.SysFont("verdana", 34, bold=True)
        self.font = pygame.font.SysFont("verdana", 22, bold=True)
        self.font_small = pygame.font.SysFont("verdana", 15, bold=True)
        self.font_tiny = pygame.font.SysFont("verdana", 12, bold=True)
        self.selected_difficulty = "normal"
        self.best_score = self.load_best_score()
        self.reset(keep_menu=True)

    def update_viewport(self):
        self.window_w, self.window_h = self.screen.get_size()
        self.scale = min(self.window_w / WIDTH, self.window_h / HEIGHT)
        self.scale = max(0.1, self.scale)
        self.viewport_w = max(1, int(WIDTH * self.scale))
        self.viewport_h = max(1, int(HEIGHT * self.scale))
        self.viewport_x = (self.window_w - self.viewport_w) // 2
        self.viewport_y = (self.window_h - self.viewport_h) // 2

    def screen_to_world(self, pos):
        sx, sy = pos
        if (
            sx < self.viewport_x
            or sy < self.viewport_y
            or sx > self.viewport_x + self.viewport_w
            or sy > self.viewport_y + self.viewport_h
        ):
            return None
        wx = int((sx - self.viewport_x) / self.scale)
        wy = int((sy - self.viewport_y) / self.scale)
        return max(0, min(WIDTH - 1, wx)), max(0, min(HEIGHT - 1, wy))

    def mouse_world_pos(self):
        pos = self.screen_to_world(pygame.mouse.get_pos())
        return pos if pos is not None else (-9999, -9999)

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.last_window_size, pygame.RESIZABLE)
            self.fullscreen = False
        else:
            self.last_window_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        self.update_viewport()

    def save_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), SAVE_FILE)

    def load_best_score(self):
        try:
            with open(self.save_path(), "r", encoding="utf-8") as f:
                return int(json.load(f).get("best_score", 0))
        except Exception:
            return 0

    def save_best_score(self):
        try:
            with open(self.save_path(), "w", encoding="utf-8") as f:
                json.dump({"best_score": self.best_score}, f, indent=2)
        except Exception:
            pass

    def reset(self, keep_menu=False):
        self.settings = DIFFICULTIES[self.selected_difficulty]
        self.spells = []
        self.particles = []
        self.float_texts = []
        self.typed = ""
        self.score = 0
        self.max_health = self.settings["health"]
        self.health = self.max_health
        self.level = 1
        self.destroyed = 0
        self.combo = 0
        self.best_combo = 0
        self.spawn_timer = 0
        self.spawn_delay = self.settings["base_spawn_delay"]
        self.spawn_delay_bonus = 0.0
        self.shake = 0
        self.wrong_flash = 0
        self.error_count = 0
        self.next_boss_at = self.settings["boss_every"]
        self.last_upgrade_level = 1
        self.upgrade_choices = []
        self.pause_message_timer = 0
        self.show_help = False

        self.mana_cap = 100
        self.mana = 25
        self.cost_discount = 0.0
        self.combo_score_bonus = 0
        self.blast_targets = 3
        self.shield_duration_bonus = 0
        self.slow_duration_bonus = 0
        self.vampiric_rune = False

        self.shield_timer = 0
        self.slow_timer = 0
        self.blast_cooldown = 0
        self.state = "menu" if keep_menu else "playing"

    def add_float_text(self, text, x, y, color=(255, 235, 180)):
        self.float_texts.append([text, x, y, 0.85, color])

    def ability_cost(self, base):
        return max(10, int(base * (1 - self.cost_discount)))

    def gain_mana(self, amount):
        self.mana = min(self.mana_cap, self.mana + amount)

    def spend_mana(self, amount):
        if self.mana < amount:
            self.add_float_text("NO MANA", PLAYER_X + 105, CENTER_Y - 40, (255, 100, 130))
            self.wrong_flash = 0.12
            return False
        self.mana -= amount
        return True

    def choose_word(self):
        if self.destroyed >= self.next_boss_at:
            self.next_boss_at += self.settings["boss_every"]
            return random.choice(BOSS_PHRASES), "boss"

        roll = random.random()

        # Bonus mana spells become a little more common after level 2.
        if self.level >= 2 and roll < 0.075:
            return random.choice(MANA_WORDS), "mana"
        if self.level >= 3 and roll < 0.145:
            return random.choice(CURSE_WORDS), "curse"
        if self.level >= 5 and roll < 0.215:
            base = random.choice(SHORT_WORDS + MEDIUM_WORDS)
            return base[::-1], "mirror"

        if self.level <= 2:
            return random.choice(SHORT_WORDS), "normal"
        if self.level <= 4:
            if roll < 0.72:
                return random.choice(SHORT_WORDS), "normal"
            return random.choice(MEDIUM_WORDS), "normal"
        if self.level <= 6:
            if roll < 0.43:
                return random.choice(SHORT_WORDS), "normal"
            if roll < 0.86:
                return random.choice(MEDIUM_WORDS), "normal"
            return random.choice(HARD_WORDS), "hard"

        if roll < 0.30:
            return random.choice(SHORT_WORDS), "normal"
        if roll < 0.74:
            return random.choice(MEDIUM_WORDS), "normal"
        return random.choice(HARD_WORDS), "hard"

    def get_spawn_y(self):
        random.shuffle(LANES)
        for lane in LANES:
            too_close = any(abs(spell.y - lane) < 38 and spell.x > WIDTH - 260 for spell in self.spells)
            if not too_close:
                return lane
        return random.choice(LANES)

    def spawn_spell(self, forced_type=None):
        if len(self.spells) >= self.settings["max_spells"]:
            return

        if forced_type == "curse":
            word, spell_type = random.choice(CURSE_WORDS), "curse"
        else:
            word, spell_type = self.choose_word()

        base_min = self.settings["speed_min"]
        base_max = self.settings["speed_max"]
        level_speed = self.level * self.settings["speed_per_level"]

        if spell_type == "boss":
            radius = 30
            speed = base_min * 0.70 + self.level * 5
        elif spell_type == "hard":
            radius = 23
            speed = random.randint(base_min, base_max) * 0.88 + level_speed
        elif spell_type == "curse":
            radius = 20
            speed = random.randint(base_min, base_max) * 1.13 + level_speed
        elif spell_type == "mirror":
            radius = 21
            speed = random.randint(base_min, base_max) * 0.96 + level_speed
        elif spell_type == "mana":
            radius = 18
            speed = random.randint(base_min, base_max) * 0.82 + level_speed
        else:
            radius = 18
            speed = random.randint(base_min, base_max) + level_speed

        self.spells.append(
            Spell(
                text=word,
                x=WIDTH + random.randint(40, 170),
                y=self.get_spawn_y(),
                speed=speed,
                radius=radius,
                wobble=random.random() * 10,
                spell_type=spell_type,
            )
        )

    def explode(self, x, y, amount=18, color_hint=(180, 180, 255)):
        for _ in range(amount):
            angle = random.random() * math.tau
            speed = random.uniform(70, 230)
            self.particles.append([
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.25, 0.72), random.randint(2, 5), color_hint
            ])

    def create_upgrade_choices(self):
        pool = UPGRADE_POOL[:]
        if self.vampiric_rune:
            pool = [u for u in pool if u["key"] != "vampiric_rune"]
        self.upgrade_choices = random.sample(pool, min(3, len(pool)))
        self.state = "upgrade"
        self.typed = ""

    def apply_upgrade(self, index):
        if not (0 <= index < len(self.upgrade_choices)):
            return
        upgrade = self.upgrade_choices[index]
        key = upgrade["key"]

        if key == "ward":
            self.max_health += 1
            self.health = min(self.max_health, self.health + 1)
        elif key == "deep_mana":
            self.mana_cap += 20
            self.gain_mana(20)
        elif key == "cheap_magic":
            self.cost_discount = min(0.30, self.cost_discount + 0.10)
        elif key == "blast_mastery":
            self.blast_targets += 1
        elif key == "barrier_mastery":
            self.shield_duration_bonus += 2
        elif key == "chronomancy":
            self.slow_duration_bonus += 1.5
        elif key == "focus":
            self.combo_score_bonus += 6
        elif key == "calm_mind":
            self.spawn_delay_bonus += 0.06
        elif key == "vampiric_rune":
            self.vampiric_rune = True

        self.add_float_text(upgrade["title"], WIDTH // 2, HEIGHT // 2 - 90, (255, 235, 160))
        self.upgrade_choices = []
        self.spawn_timer = 0
        self.state = "playing"

    def cast_barrier(self):
        cost = self.ability_cost(35)
        if not self.spend_mana(cost):
            return
        self.shield_timer = 8.0 + self.shield_duration_bonus
        self.add_float_text("BARRIER", PLAYER_X + 95, CENTER_Y + 10, (160, 220, 255))

    def cast_slow_time(self):
        cost = self.ability_cost(45)
        if not self.spend_mana(cost):
            return
        self.slow_timer = 5.0 + self.slow_duration_bonus
        self.add_float_text("SLOW TIME", WIDTH // 2, 80, (170, 240, 255))

    def cast_arcane_blast(self):
        cost = self.ability_cost(70)
        if not self.spend_mana(cost):
            return
        self.shake = 0.18
        self.blast_cooldown = 0.45
        targets = sorted(self.spells, key=lambda s: s.x)[:self.blast_targets]
        removed = 0
        for spell in targets[:]:
            self.explode(spell.x, spell.y, 28, SPELL_COLORS.get(spell.spell_type, SPELL_COLORS["normal"])[2])
            if spell.spell_type == "boss":
                spell.speed *= 0.62
                self.add_float_text("BOSS SLOWED", spell.x, spell.y - 55, (255, 170, 220))
            else:
                if spell in self.spells:
                    self.spells.remove(spell)
                    removed += 1
        self.score += removed * 60
        self.add_float_text(f"BLAST x{removed}", WIDTH // 2, CENTER_Y, (255, 230, 160))

    def difficulty_rects(self):
        card_w, card_h, gap = 218, 122, 22
        total_w = card_w * 3 + gap * 2
        start_x = WIDTH // 2 - total_w // 2
        y = 240
        return {
            "easy": pygame.Rect(start_x, y, card_w, card_h),
            "normal": pygame.Rect(start_x + card_w + gap, y, card_w, card_h),
            "hard": pygame.Rect(start_x + (card_w + gap) * 2, y, card_w, card_h),
        }

    def start_button_rect(self):
        return pygame.Rect(WIDTH // 2 - 170, 382, 340, 62)

    def ability_rects(self):
        card_w, card_h, gap = 146, 102, 12
        x = WIDTH // 2 - (card_w * 3 + gap * 2) // 2
        y = 86
        return {
            "barrier": pygame.Rect(x, y, card_w, card_h),
            "slow": pygame.Rect(x + card_w + gap, y, card_w, card_h),
            "blast": pygame.Rect(x + (card_w + gap) * 2, y, card_w, card_h),
        }

    def pause_button_rect(self):
        return pygame.Rect(WIDTH - 156, 108, 132, 42)

    def pause_menu_rects(self):
        button_w = 280
        button_h = 46
        gap = 14
        x = WIDTH // 2 - button_w // 2
        start_y = 250
        return {
            "continue": pygame.Rect(x, start_y, button_w, button_h),
            "restart": pygame.Rect(x, start_y + (button_h + gap), button_w, button_h),
            "menu": pygame.Rect(x, start_y + (button_h + gap) * 2, button_w, button_h),
            "quit": pygame.Rect(x, start_y + (button_h + gap) * 3, button_w, button_h),
        }

    def resume_button_rect(self):
        return pygame.Rect(WIDTH // 2 - 125, 326, 250, 48)

    def gameover_restart_rect(self):
        return pygame.Rect(WIDTH // 2 - 250, 398, 230, 48)

    def gameover_menu_rect(self):
        return pygame.Rect(WIDTH // 2 + 20, 398, 230, 48)

    def upgrade_card_rects(self):
        card_w, card_h = 260, 166
        start_x = WIDTH // 2 - card_w - 18 - card_w // 2
        y = 214
        return [pygame.Rect(start_x + i * (card_w + 36), y, card_w, card_h) for i in range(3)]

    def restart_run(self):
        self.reset(keep_menu=False)

    def draw_glow_panel(self, surf, rect, fill=(16, 13, 34), border=(92, 76, 154), accent=None, width=1, radius=10, glow=False):
        """Reusable crisp fantasy UI panel."""
        if glow and accent:
            for grow, alpha_color in ((10, accent), (5, accent)):
                glow_rect = rect.inflate(grow, grow)
                pygame.draw.rect(surf, alpha_color, glow_rect, 1, border_radius=radius + 2)
        pygame.draw.rect(surf, fill, rect, border_radius=radius)
        pygame.draw.rect(surf, accent or border, rect, width, border_radius=radius)

    def draw_center_text(self, surf, text, font, center, color, shadow=True):
        if shadow:
            sh = font.render(text, True, (8, 6, 18))
            surf.blit(sh, sh.get_rect(center=(center[0] + 2, center[1] + 2)))
        txt = font.render(text, True, color)
        surf.blit(txt, txt.get_rect(center=center))
        return txt.get_rect(center=center)

    def draw_keycap(self, surf, x, y, text, w=36, h=28, accent=(145, 120, 220)):
        rect = pygame.Rect(x, y, w, h)
        self.draw_glow_panel(surf, rect, fill=(22, 18, 42), border=(80, 70, 130), accent=accent, width=1, radius=6)
        self.draw_center_text(surf, text, self.font_small, rect.center, (235, 230, 255), shadow=False)
        return rect

    def draw_gem(self, surf, center, size, color=(160, 95, 255)):
        x, y = center
        points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        pygame.draw.polygon(surf, color, points)
        pygame.draw.polygon(surf, (235, 220, 255), points, 1)
        pygame.draw.line(surf, (245, 235, 255), (x, y - size + 3), (x + size - 4, y), 1)

    def draw_star_icon(self, surf, center, color=(255, 220, 120), radius=13):
        x, y = center
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = radius if i % 2 == 0 else radius * 0.45
            pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (255, 245, 210), pts, 1)

    def draw_panel_button(self, surf, rect, title, subtitle="", selected=False, disabled=False, accent=(145, 120, 220), small=False):
        mouse = self.mouse_world_pos()
        hover = rect.collidepoint(mouse) and not disabled
        tick = pygame.time.get_ticks() * 0.001
        lift = -3 if hover else 0
        draw_rect = rect.move(0, lift)

        base = (18, 14, 38) if not disabled else (15, 13, 26)
        border = accent if (hover or selected) else (82, 68, 135)
        if selected:
            border = (255, 220, 105)
        if hover:
            pulse = 3 + int(2 * (1 + math.sin(tick * 8)))
            pygame.draw.rect(surf, border, draw_rect.inflate(pulse * 3, pulse * 3), 1, border_radius=16)

        self.draw_glow_panel(surf, draw_rect, fill=base, border=(70, 60, 120), accent=border, width=2 if (hover or selected) else 1, radius=13)

        if selected:
            tag_rect = pygame.Rect(draw_rect.centerx - 48, draw_rect.y - 1, 96, 24)
            pygame.draw.rect(surf, (245, 196, 72), tag_rect, border_radius=7)
            self.draw_center_text(surf, "SELECTED", self.font_tiny, tag_rect.center, (32, 20, 18), shadow=False)

        font_title = self.font_small if small else self.font
        title_col = (250, 246, 255) if not disabled else (125, 122, 145)
        sub_col = (184, 188, 225) if not disabled else (100, 98, 118)
        title_y = draw_rect.centery - (10 if subtitle else 0) + (11 if selected else 0)
        self.draw_center_text(surf, title, font_title, (draw_rect.centerx, title_y), title_col, shadow=True)

        if subtitle:
            sub_surf = self.font_tiny.render(subtitle, True, sub_col)
            surf.blit(sub_surf, sub_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + 25)))
        return hover

    def handle_mouse(self, event):
        if event.button != 1:
            return
        pos = self.screen_to_world(event.pos)
        if pos is None:
            return

        # Click anywhere on the help overlay to close it.
        if self.show_help:
            self.show_help = False
            return

        if self.state == "menu":
            for difficulty, rect in self.difficulty_rects().items():
                if rect.collidepoint(pos):
                    self.selected_difficulty = difficulty
                    self.settings = DIFFICULTIES[self.selected_difficulty]
                    self.add_float_text(self.settings["label"], rect.centerx, rect.y - 8, (255, 230, 160))
                    return
            if self.start_button_rect().collidepoint(pos):
                self.reset(keep_menu=False)
                return

        elif self.state == "playing":
            ability_rects = self.ability_rects()
            if ability_rects["barrier"].collidepoint(pos):
                self.cast_barrier()
                return
            if ability_rects["slow"].collidepoint(pos):
                self.cast_slow_time()
                return
            if ability_rects["blast"].collidepoint(pos):
                self.cast_arcane_blast()
                return
            if self.pause_button_rect().collidepoint(pos):
                self.state = "paused"
                self.show_help = False
                return

        elif self.state == "upgrade":
            for i, rect in enumerate(self.upgrade_card_rects()):
                if i < len(self.upgrade_choices) and rect.collidepoint(pos):
                    self.apply_upgrade(i)
                    return

        elif self.state == "paused":
            buttons = self.pause_menu_rects()
            if buttons["continue"].collidepoint(pos):
                self.state = "playing"
                self.show_help = False
                return
            if buttons["restart"].collidepoint(pos):
                self.restart_run()
                return
            if buttons["menu"].collidepoint(pos):
                self.reset(keep_menu=True)
                return
            if buttons["quit"].collidepoint(pos):
                pygame.quit()
                sys.exit()

        elif self.state == "gameover":
            if self.gameover_restart_rect().collidepoint(pos):
                self.reset(keep_menu=False)
                return
            if self.gameover_menu_rect().collidepoint(pos):
                self.reset(keep_menu=True)
                return

    def handle_key(self, event):
        if event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return

        if event.key == pygame.K_F1:
            self.show_help = not self.show_help
            return

        if event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
                return
            if self.state == "playing":
                self.state = "paused"
                return
            if self.state == "paused":
                self.state = "playing"
                return
            if self.state in ("menu", "gameover"):
                pygame.quit()
                sys.exit()

        # When help is visible, only F1/Esc should act on the game.
        if self.show_help:
            return

        if self.state == "menu":
            if event.key == pygame.K_1:
                self.selected_difficulty = "easy"
                self.settings = DIFFICULTIES[self.selected_difficulty]
            elif event.key == pygame.K_2:
                self.selected_difficulty = "normal"
                self.settings = DIFFICULTIES[self.selected_difficulty]
            elif event.key == pygame.K_3:
                self.selected_difficulty = "hard"
                self.settings = DIFFICULTIES[self.selected_difficulty]
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset(keep_menu=False)
            return

        if self.state == "gameover":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset(keep_menu=False)
            elif event.key == pygame.K_m:
                self.reset(keep_menu=True)
            return

        if self.state == "paused":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "playing"
            elif event.key == pygame.K_r:
                self.restart_run()
            elif event.key == pygame.K_m:
                self.reset(keep_menu=True)
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            return

        if self.state == "upgrade":
            if event.key == pygame.K_a:
                self.apply_upgrade(0)
            elif event.key == pygame.K_s:
                self.apply_upgrade(1)
            elif event.key == pygame.K_d:
                self.apply_upgrade(2)
            return

        if self.state != "playing":
            return

        # Ability hotkeys. Spell words do not contain digits, so this does not conflict with typing.
        if event.key == pygame.K_1:
            self.cast_barrier()
            return
        if event.key == pygame.K_2:
            self.cast_slow_time()
            return
        if event.key == pygame.K_3:
            self.cast_arcane_blast()
            return

        if event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif event.key == pygame.K_RETURN:
            self.typed = ""
        elif event.unicode and event.unicode.isprintable():
            ch = event.unicode.lower()
            if ch.isalnum() or ch == " ":
                self.typed += ch
                self.check_typing()

    def update_balance_after_kill(self):
        old_level = self.level
        self.level = 1 + self.destroyed // self.settings["level_every"]
        base = self.settings["base_spawn_delay"]
        minimum = self.settings["min_spawn_delay"]
        self.spawn_delay = max(minimum, base - self.level * 0.105 + self.spawn_delay_bonus)

        if self.level > old_level and self.level > self.last_upgrade_level:
            self.last_upgrade_level = self.level
            self.create_upgrade_choices()

    def spell_points(self, spell):
        base_points = 100 + len(spell.text) * 12
        if spell.spell_type == "hard":
            base_points += 90
        elif spell.spell_type == "boss":
            base_points += 350
        elif spell.spell_type == "curse":
            base_points += 140
        elif spell.spell_type == "mirror":
            base_points += 120
        elif spell.spell_type == "mana":
            base_points += 40
        combo_bonus = min(350, self.combo * (12 + self.combo_score_bonus))
        return base_points + combo_bonus

    def kill_spell(self, spell, typed_by_player=True):
        color = SPELL_COLORS.get(spell.spell_type, SPELL_COLORS["normal"])[2]
        self.explode(spell.x, spell.y, 38 if spell.spell_type == "boss" else 22, color)
        self.score += self.spell_points(spell)
        self.destroyed += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)

        mana_gain = 8 + min(12, self.combo // 3)
        if spell.spell_type == "hard":
            mana_gain += 5
        elif spell.spell_type == "boss":
            mana_gain += 22
        elif spell.spell_type == "curse":
            mana_gain += 4
        elif spell.spell_type == "mirror":
            mana_gain += 7
        elif spell.spell_type == "mana":
            mana_gain += 22
        self.gain_mana(mana_gain)

        if self.vampiric_rune and self.combo > 0 and self.combo % 10 == 0:
            if self.health < self.max_health:
                self.health += 1
                self.add_float_text("+1 HP", PLAYER_X + 90, CENTER_Y - 20, (150, 255, 170))

        self.update_balance_after_kill()
        if spell in self.spells:
            self.spells.remove(spell)
        self.typed = ""

    def wrong_input(self):
        self.wrong_flash = 0.20
        self.combo = 0
        self.error_count += 1
        self.mana = max(0, self.mana - 4)
        self.typed = ""
        self.shake = 0.08

        if self.settings["error_damage"] and self.error_count % 4 == 0:
            self.health -= self.settings["error_damage"]
            self.add_float_text("ERROR DAMAGE", PLAYER_X + 120, CENTER_Y - 20, (255, 100, 130))
            if self.health <= 0:
                self.trigger_gameover()
                return

        if self.error_count % 3 == 0:
            self.spawn_spell(forced_type="curse")
            self.add_float_text("MISCAST!", WIDTH - 180, 70, (255, 100, 130))

    def check_typing(self):
        if not self.typed:
            return

        matching_prefix = False
        for spell in sorted(self.spells, key=lambda s: s.x):
            if spell.text.startswith(self.typed):
                matching_prefix = True
            if self.typed == spell.text:
                self.kill_spell(spell)
                return

        if not matching_prefix:
            self.wrong_input()

    def spell_damage(self, spell):
        if spell.spell_type == "boss":
            return 2
        if spell.spell_type == "curse":
            return 2
        return 1

    def spell_reaches_player(self, spell):
        self.spells.remove(spell)
        self.combo = 0
        self.typed = ""
        self.shake = 0.24
        self.explode(PLAYER_X, spell.y, 16 if spell.spell_type in ("boss", "curse") else 10,
                     SPELL_COLORS.get(spell.spell_type, SPELL_COLORS["normal"])[1])

        if self.shield_timer > 0 and spell.spell_type != "curse":
            self.shield_timer = max(0, self.shield_timer - 2.5)
            self.add_float_text("BLOCKED", PLAYER_X + 90, spell.y, (160, 220, 255))
            return

        if self.shield_timer > 0 and spell.spell_type == "curse":
            self.shield_timer = 0
            self.add_float_text("SHIELD BROKEN", PLAYER_X + 130, spell.y, (255, 110, 130))

        self.health -= self.spell_damage(spell)
        if self.health <= 0:
            self.trigger_gameover()

    def trigger_gameover(self):
        self.state = "gameover"
        if self.score > self.best_score:
            self.best_score = self.score
            self.save_best_score()

    def update(self, dt):
        if self.state != "playing":
            return

        self.shield_timer = max(0, self.shield_timer - dt)
        self.slow_timer = max(0, self.slow_timer - dt)
        self.blast_cooldown = max(0, self.blast_cooldown - dt)

        time_scale = 0.42 if self.slow_timer > 0 else 1.0

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.spawn_spell()

        for spell in self.spells[:]:
            spell.update(dt, time_scale)
            if spell.x < PLAYER_X + 20:
                self.spell_reaches_player(spell)

        self.update_particles_and_text(dt)
        self.shake = max(0, self.shake - dt)
        self.wrong_flash = max(0, self.wrong_flash - dt)

    def update_particles_and_text(self, dt):
        for p in self.particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            if p[4] <= 0:
                self.particles.remove(p)

        for txt in self.float_texts[:]:
            txt[2] -= 35 * dt
            txt[3] -= dt
            if txt[3] <= 0:
                self.float_texts.remove(txt)

    def draw_background(self, surf):
        # Vertical night gradient instead of flat fill.
        top = (6, 7, 24)
        bottom = (19, 11, 44)
        for y in range(HEIGHT):
            t = y / HEIGHT
            col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (WIDTH, y))

        ticks = pygame.time.get_ticks() * 0.001
        for i in range(120):
            x = (i * 137 + 17) % WIDTH
            y = (i * 83 + 29) % (HEIGHT - 75)
            pulse = 70 + int(80 * (0.5 + 0.5 * math.sin(ticks * 1.4 + i)))
            color = (pulse, pulse, min(255, pulse + 65))
            surf.set_at((x, y), color)
            if i % 17 == 0:
                pygame.draw.line(surf, color, (x - 2, y), (x + 2, y), 1)
                pygame.draw.line(surf, color, (x, y - 2), (x, y + 2), 1)

        # Distant skyline.
        pygame.draw.polygon(surf, (11, 10, 30), [(0, 425), (120, 392), (230, 430), (330, 398), (455, 426), (585, 386), (720, 430), (850, 390), (960, 415), (960, 540), (0, 540)])
        pygame.draw.rect(surf, (34, 22, 54), (0, HEIGHT - 74, WIDTH, 74))
        pygame.draw.line(surf, (88, 62, 145), (0, HEIGHT - 74), (WIDTH, HEIGHT - 74), 2)
        for x in range(0, WIDTH, 48):
            pygame.draw.rect(surf, (42, 29, 65), (x, HEIGHT - 64, 44, 18), border_radius=3)
            pygame.draw.rect(surf, (28, 20, 45), (x, HEIGHT - 45, 44, 13), border_radius=2)

        # Enemy caster silhouette and magic ring.
        ex, ey = WIDTH - 118, CENTER_Y + 82
        pygame.draw.circle(surf, (74, 38, 95), (ex, ey - 100), 70, 1)
        pygame.draw.arc(surf, (118, 55, 145), pygame.Rect(ex - 78, ey - 178, 156, 156), -1.0, 2.1, 2)
        pygame.draw.polygon(surf, (63, 27, 76), [(ex - 42, ey + 48), (ex, ey - 78), (ex + 46, ey + 48)])
        pygame.draw.circle(surf, (106, 50, 125), (ex, ey - 92), 22)
        pygame.draw.circle(surf, (255, 82, 165), (ex - 7, ey - 94), 3)
        pygame.draw.circle(surf, (255, 82, 165), (ex + 7, ey - 94), 3)
        pygame.draw.line(surf, (120, 58, 122), (ex - 34, ey - 25), (ex - 76, ey - 92), 5)
        pygame.draw.circle(surf, (244, 84, 196), (ex - 78, ey - 96), 8)

    def draw_wizard(self, surf):
        x, y = PLAYER_X, CENTER_Y + 78
        pygame.draw.circle(surf, (62, 45, 135), (x + 4, y - 105), 78, 1)
        pygame.draw.arc(surf, (92, 70, 186), pygame.Rect(x - 80, y - 184, 160, 160), 1.1, 4.4, 2)
        pygame.draw.rect(surf, (27, 20, 48), (x - 62, y + 46, 124, 12), border_radius=3)
        pygame.draw.rect(surf, (38, 26, 62), (x - 56, y + 56, 112, 12), border_radius=2)
        pygame.draw.polygon(surf, (72, 55, 158), [(x - 42, y + 44), (x, y - 88), (x + 42, y + 44)])
        pygame.draw.polygon(surf, (92, 75, 190), [(x - 22, y + 44), (x, y - 72), (x + 16, y + 44)])
        pygame.draw.circle(surf, (234, 215, 190), (x, y - 96), 22)
        pygame.draw.polygon(surf, (51, 43, 132), [(x - 36, y - 110), (x + 7, y - 168), (x + 34, y - 110)])
        pygame.draw.line(surf, (195, 154, 88), (x + 34, y - 39), (x + 78, y - 102), 5)
        pygame.draw.circle(surf, (211, 180, 255), (x + 80, y - 106), 8)
        pygame.draw.circle(surf, (160, 105, 255), (x + 80, y - 106), 17, 1)

        if self.shield_timer > 0:
            shield_alpha = 120 + int(70 * math.sin(pygame.time.get_ticks() * 0.015))
            pygame.draw.circle(surf, (120, 190, 255), (x + 6, y - 48), 88, 3)
            pygame.draw.circle(surf, (shield_alpha, shield_alpha, 255), (x + 6, y - 48), 72, 1)

    def draw_bar(self, surf, x, y, w, h, value, max_value, fill_color, label):
        value = max(0, min(max_value, value))
        ratio = value / max_value if max_value else 0
        panel = pygame.Rect(x, y, w, h)
        self.draw_glow_panel(surf, panel, fill=(18, 14, 36), border=(82, 70, 135), radius=7)
        label_rect = pygame.Rect(x + 8, y + 7, 52, h - 14)
        pygame.draw.rect(surf, fill_color, label_rect, border_radius=4)
        self.draw_center_text(surf, label, self.font_tiny, label_rect.center, (245, 248, 255), shadow=False)
        bar_rect = pygame.Rect(x + 68, y + 9, w - 78, h - 18)
        pygame.draw.rect(surf, (9, 8, 22), bar_rect, border_radius=4)
        pygame.draw.rect(surf, fill_color, (bar_rect.x, bar_rect.y, int(bar_rect.w * ratio), bar_rect.h), border_radius=4)
        pygame.draw.rect(surf, (135, 125, 190), bar_rect, 1, border_radius=4)
        txt = self.font_tiny.render(f"{int(value)} / {int(max_value)}", True, (240, 240, 255))
        surf.blit(txt, txt.get_rect(center=bar_rect.center))

    def draw_hud(self, surf):
        # Top-left status cluster.
        hp_rect = pygame.Rect(14, 14, 244, 38)
        self.draw_glow_panel(surf, hp_rect, fill=(15, 12, 31), border=(92, 76, 150), radius=8)
        hp_label = self.font_small.render("HP", True, (235, 226, 255))
        surf.blit(hp_label, (hp_rect.x + 14, hp_rect.y + 10))
        for i in range(self.max_health):
            cx = hp_rect.x + 58 + i * 20
            col = (255, 104, 150) if i < self.health else (62, 43, 75)
            self.draw_center_text(surf, "♥", self.font, (cx, hp_rect.y + 20), col, shadow=False)

        stats_y = 60
        stat_w = 78
        labels = [("SCORE", self.score, (255, 218, 105)), ("COMBO", self.combo, (170, 215, 255)), ("BEST", self.best_combo, (210, 190, 255))]
        for i, (label, value, accent) in enumerate(labels):
            r = pygame.Rect(14 + i * (stat_w + 5), stats_y, stat_w, 58)
            self.draw_glow_panel(surf, r, fill=(15, 12, 31), border=(74, 62, 120), accent=accent, radius=7)
            self.draw_center_text(surf, label, self.font_tiny, (r.centerx, r.y + 15), accent, shadow=False)
            self.draw_center_text(surf, str(value), self.font, (r.centerx, r.y + 39), (245, 238, 255), shadow=True)

        hs = self.font_tiny.render(f"♛ High Score: {self.best_score}", True, (172, 160, 216))
        surf.blit(hs, (18, 126))
        self.draw_bar(surf, 14, 148, 244, 38, self.mana, self.mana_cap, (82, 137, 255), "MANA")

        # Ability cards in the top center.
        header = self.font_small.render("YOUR ABILITIES", True, (184, 178, 230))
        surf.blit(header, header.get_rect(center=(WIDTH // 2, 62)))
        pygame.draw.line(surf, (88, 65, 145), (WIDTH // 2 - 210, 62), (WIDTH // 2 - 92, 62), 1)
        pygame.draw.line(surf, (88, 65, 145), (WIDTH // 2 + 92, 62), (WIDTH // 2 + 210, 62), 1)
        self.draw_gem(surf, (WIDTH // 2, 62), 8, (142, 88, 242))

        shield_cost = self.ability_cost(35)
        slow_cost = self.ability_cost(45)
        blast_cost = self.ability_cost(70)
        ability_data = [
            ("barrier", "1", "BARRIER", "Block next", "hit spell", shield_cost, (145, 108, 255), "◈"),
            ("slow", "2", "SLOW TIME", "Slow spells", "for 5 sec", slow_cost, (95, 190, 255), "⌛"),
            ("blast", "3", "BLAST", "Hit enemy", "spells", blast_cost, (255, 178, 72), "✦"),
        ]
        rects = self.ability_rects()
        for key, hotkey, title, line1, line2, cost, accent, icon in ability_data:
            rect = rects[key]
            disabled = self.mana < cost
            hover = rect.collidepoint(self.mouse_world_pos()) and not disabled
            border = accent if hover or not disabled else (64, 55, 90)
            fill = (17, 14, 35) if not disabled else (13, 12, 24)
            self.draw_glow_panel(surf, rect, fill=fill, border=(72, 60, 115), accent=border, width=2 if hover else 1, radius=10, glow=hover)
            self.draw_keycap(surf, rect.x + 12, rect.y + 12, hotkey, w=30, h=28, accent=border)
            self.draw_center_text(surf, title, self.font_tiny, (rect.x + 86, rect.y + 26), (245, 240, 255) if not disabled else (120, 118, 140), shadow=False)
            self.draw_center_text(surf, icon, self.font_big, (rect.x + 38, rect.y + 63), border if not disabled else (72, 66, 88), shadow=False)
            dcol = (203, 205, 235) if not disabled else (100, 98, 118)
            surf.blit(self.font_tiny.render(line1, True, dcol), (rect.x + 70, rect.y + 48))
            surf.blit(self.font_tiny.render(line2, True, dcol), (rect.x + 70, rect.y + 66))
            self.draw_center_text(surf, f"{cost} MANA", self.font_tiny, (rect.centerx, rect.bottom - 16), (95, 170, 255) if not disabled else (92, 90, 110), shadow=False)

        hint = self.font_tiny.render("Type words to cast spells  •  1 / 2 / 3 to use abilities", True, (170, 164, 210))
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, 204)))

        # Top-right cluster.
        lvl_rect = pygame.Rect(WIDTH - 164, 16, 56, 58)
        diff_rect = pygame.Rect(WIDTH - 98, 16, 84, 58)
        self.draw_glow_panel(surf, lvl_rect, fill=(15, 12, 31), border=(92, 76, 150), radius=8)
        self.draw_center_text(surf, "LVL", self.font_tiny, (lvl_rect.centerx, lvl_rect.y + 15), (190, 185, 230), shadow=False)
        self.draw_center_text(surf, str(self.level), self.font, (lvl_rect.centerx, lvl_rect.y + 39), (245, 238, 255), shadow=True)
        self.draw_glow_panel(surf, diff_rect, fill=(15, 12, 31), border=(92, 76, 150), radius=8)
        self.draw_center_text(surf, "MODE", self.font_tiny, (diff_rect.centerx, diff_rect.y + 15), (190, 185, 230), shadow=False)
        self.draw_center_text(surf, self.settings["label"], self.font_tiny, (diff_rect.centerx, diff_rect.y + 39), (255, 222, 105), shadow=False)
        self.draw_panel_button(surf, self.pause_button_rect(), "ESC MENU", "F1 HELP", accent=(160, 128, 230), small=True)

        # Active timers.
        timer_parts = []
        if self.shield_timer > 0:
            timer_parts.append(f"Barrier {self.shield_timer:.1f}s")
        if self.slow_timer > 0:
            timer_parts.append(f"Slow {self.slow_timer:.1f}s")
        if timer_parts:
            timers = self.font_tiny.render("  |  ".join(timer_parts), True, (255, 235, 160))
            surf.blit(timers, (WIDTH // 2 - timers.get_width() // 2, 222))

        # Bottom input command bar.
        input_panel = pygame.Rect(20, HEIGHT - 78, WIDTH - 40, 62)
        self.draw_glow_panel(surf, input_panel, fill=(13, 10, 31), border=(88, 64, 150), accent=(180, 140, 255), width=2, radius=9)
        icon_rect = pygame.Rect(input_panel.x + 12, input_panel.y + 10, 42, 42)
        self.draw_glow_panel(surf, icon_rect, fill=(27, 18, 52), border=(95, 72, 155), accent=(255, 212, 95), radius=7)
        self.draw_center_text(surf, "✦", self.font, icon_rect.center, (255, 224, 105), shadow=False)
        boss_rect = pygame.Rect(input_panel.right - 120, input_panel.y + 10, 102, 42)
        self.draw_glow_panel(surf, boss_rect, fill=(20, 15, 36), border=(95, 72, 155), accent=(255, 212, 95), radius=7)
        kills_to_boss = max(0, self.next_boss_at - self.destroyed)
        self.draw_center_text(surf, "BOSS IN", self.font_tiny, (boss_rect.centerx, boss_rect.y + 12), (184, 174, 225), shadow=False)
        self.draw_center_text(surf, f"{kills_to_boss} SPELLS", self.font_tiny, (boss_rect.centerx, boss_rect.y + 29), (245, 238, 255), shadow=False)

        color = (255, 90, 100) if self.wrong_flash > 0 else (240, 238, 255)
        input_text = self.typed if self.typed else "Type spell here..."
        prompt_color = color if self.typed else (150, 142, 190)
        pygame.draw.line(surf, (245, 238, 255), (input_panel.x + 74, input_panel.y + 17), (input_panel.x + 74, input_panel.bottom - 17), 2)
        prompt = self.font_big.render(input_text, True, prompt_color)
        surf.blit(prompt, (input_panel.x + 90, input_panel.y + 13))

    def draw_menu(self, surf):
        # Dark translucent center stage so menu is readable over the scene.
        pygame.draw.rect(surf, (4, 4, 16), pygame.Rect(0, 0, WIDTH, HEIGHT), 0)
        self.draw_background(surf)
        self.draw_wizard(surf)

        self.draw_gem(surf, (WIDTH // 2, 54), 14, (166, 91, 255))
        pygame.draw.line(surf, (211, 157, 61), (WIDTH // 2 - 135, 54), (WIDTH // 2 - 22, 54), 2)
        pygame.draw.line(surf, (211, 157, 61), (WIDTH // 2 + 22, 54), (WIDTH // 2 + 135, 54), 2)
        self.draw_center_text(surf, "WIZARD", self.font_logo, (WIDTH // 2, 104), (255, 225, 126), shadow=True)
        self.draw_center_text(surf, "TYPING DUEL", self.font_big, (WIDTH // 2, 155), (226, 199, 255), shadow=True)
        self.draw_center_text(surf, "Type spells. Spend mana. Survive the duel.", self.font_small, (WIDTH // 2, 198), (185, 215, 238), shadow=False)

        pygame.draw.line(surf, (92, 68, 150), (WIDTH // 2 - 225, 222), (WIDTH // 2 - 86, 222), 2)
        pygame.draw.line(surf, (92, 68, 150), (WIDTH // 2 + 86, 222), (WIDTH // 2 + 225, 222), 2)
        self.draw_center_text(surf, "CHOOSE DIFFICULTY", self.font_small, (WIDTH // 2, 222), (176, 168, 230), shadow=False)

        subtitles = {
            "easy": ("Calmer spells", "8 HP", (125, 155, 255)),
            "normal": ("Intended balance", "6 HP", (255, 221, 100)),
            "hard": ("Errors can hurt", "5 HP", (255, 100, 178)),
        }
        accents = {
            "easy": (125, 155, 255),
            "normal": (255, 221, 100),
            "hard": (255, 100, 178),
        }
        for difficulty, rect in self.difficulty_rects().items():
            selected = self.selected_difficulty == difficulty
            accent = accents[difficulty]
            hover = rect.collidepoint(self.mouse_world_pos())
            self.draw_glow_panel(surf, rect, fill=(18, 14, 38), border=(82, 68, 135), accent=(255, 220, 105) if selected else accent, width=2 if selected or hover else 1, radius=11, glow=selected or hover)
            if selected:
                tag = pygame.Rect(rect.centerx - 50, rect.y - 1, 100, 24)
                pygame.draw.rect(surf, (246, 197, 74), tag, border_radius=7)
                self.draw_center_text(surf, "SELECTED", self.font_tiny, tag.center, (36, 22, 18), shadow=False)
            self.draw_star_icon(surf, (rect.centerx, rect.y + 34), accent, radius=15)
            self.draw_center_text(surf, DIFFICULTIES[difficulty]["label"], self.font, (rect.centerx, rect.y + 68), (250, 246, 255), shadow=True)
            self.draw_center_text(surf, subtitles[difficulty][0], self.font_tiny, (rect.centerx, rect.y + 94), (180, 190, 230), shadow=False)
            pygame.draw.line(surf, (65, 52, 103), (rect.x + 18, rect.y + 102), (rect.right - 18, rect.y + 102), 1)
            self.draw_center_text(surf, "♥  " + subtitles[difficulty][1], self.font_small, (rect.centerx, rect.y + 114), accent, shadow=False)

        start_rect = self.start_button_rect()
        hover = start_rect.collidepoint(self.mouse_world_pos())
        self.draw_glow_panel(surf, start_rect, fill=(43, 25, 88), border=(132, 75, 210), accent=(226, 106, 255) if hover else (180, 114, 255), width=3, radius=13, glow=True)
        self.draw_center_text(surf, "✦  START DUEL", self.font_big, start_rect.center, (252, 246, 255), shadow=True)
        self.draw_center_text(surf, "Press Space / Enter", self.font_small, (WIDTH // 2, start_rect.bottom + 28), (175, 195, 225), shadow=False)

        footer = pygame.Rect(18, HEIGHT - 58, WIDTH - 36, 42)
        self.draw_glow_panel(surf, footer, fill=(12, 10, 28), border=(78, 64, 120), radius=8)
        sections = [("Esc", "Pause / Menu"), ("F1", "Help"), ("F11", "Fullscreen")]
        x = footer.x + 145
        for i, (key, label) in enumerate(sections):
            self.draw_keycap(surf, x, footer.y + 8, key, w=46 if len(key) > 2 else 36, h=26, accent=(116, 95, 170))
            surf.blit(self.font_small.render(label, True, (190, 184, 220)), (x + 58, footer.y + 11))
            if i < 2:
                pygame.draw.line(surf, (74, 60, 108), (x + 190, footer.y + 9), (x + 190, footer.bottom - 9), 1)
            x += 270

    def draw_upgrade(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 210))
        surf.blit(overlay, (0, 0))
        title = self.font_big.render("LEVEL UP — CHOOSE A RUNE", True, (255, 230, 160))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 105)))

        keys = ["A", "S", "D"]
        card_rects = self.upgrade_card_rects()
        for i, upgrade in enumerate(self.upgrade_choices):
            rect = card_rects[i]
            hover = rect.collidepoint(self.mouse_world_pos())
            draw_rect = rect.move(0, -6 if hover else 0)
            tick = pygame.time.get_ticks() * 0.001
            border = (255, 220, 120) if hover else (145, 120, 220)
            if hover:
                glow = 5 + int(3 * (1 + math.sin(tick * 9)))
                pygame.draw.rect(surf, border, draw_rect.inflate(glow * 3, glow * 3), 2, border_radius=18)

            pygame.draw.rect(surf, (24, 18, 48), draw_rect, border_radius=14)
            pygame.draw.rect(surf, border, draw_rect, 3 if hover else 2, border_radius=14)

            rune_y = draw_rect.y + 38
            pygame.draw.circle(surf, (58, 45, 96), (draw_rect.centerx, rune_y), 26)
            pygame.draw.circle(surf, border, (draw_rect.centerx, rune_y), 26, 2)
            key_surf = self.font.render(keys[i], True, (255, 230, 160))
            surf.blit(key_surf, key_surf.get_rect(center=(draw_rect.centerx, rune_y)))

            title_surf = self.font_small.render(upgrade["title"], True, (230, 225, 255))
            desc_surf = self.font_tiny.render(upgrade["desc"], True, (185, 190, 225))
            click_surf = self.font_tiny.render("click or press " + keys[i], True, (255, 225, 140) if hover else (145, 145, 180))
            surf.blit(title_surf, title_surf.get_rect(center=(draw_rect.centerx, draw_rect.y + 86)))
            surf.blit(desc_surf, desc_surf.get_rect(center=(draw_rect.centerx, draw_rect.y + 122)))
            surf.blit(click_surf, click_surf.get_rect(center=(draw_rect.centerx, draw_rect.y + 150)))

        hint = self.font_small.render("The duel is paused. Pick one upgrade with mouse or keyboard.", True, (175, 180, 220))
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, 440)))

    def draw_gameover(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 190))
        surf.blit(overlay, (0, 0))
        title = self.font_big.render("GAME OVER", True, (255, 120, 150))
        score = self.font.render(f"Final score: {self.score}", True, (245, 230, 170))
        best = self.font.render(f"High score: {self.best_score}", True, (180, 230, 255))
        combo = self.font.render(f"Best combo: {self.best_combo}", True, (255, 220, 120))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 145)))
        surf.blit(score, score.get_rect(center=(WIDTH // 2, 215)))
        surf.blit(best, best.get_rect(center=(WIDTH // 2, 255)))
        surf.blit(combo, combo.get_rect(center=(WIDTH // 2, 295)))
        self.draw_panel_button(surf, self.gameover_restart_rect(), "RESTART", "Space / Enter", accent=(120, 220, 180))
        self.draw_panel_button(surf, self.gameover_menu_rect(), "MENU", "M", accent=(180, 160, 255))

    def draw_pause(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 190))
        surf.blit(overlay, (0, 0))

        title = self.font_big.render("PAUSED", True, (245, 230, 170))
        subtitle = self.font_small.render("Esc to continue · F1 for controls", True, (180, 230, 255))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 172)))
        surf.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 214)))

        buttons = self.pause_menu_rects()
        self.draw_panel_button(surf, buttons["continue"], "CONTINUE", "Esc / Enter / Click", accent=(120, 220, 180))
        self.draw_panel_button(surf, buttons["restart"], "RESTART RUN", "R / Click", accent=(255, 220, 120))
        self.draw_panel_button(surf, buttons["menu"], "MAIN MENU", "M / Click", accent=(180, 160, 255))
        self.draw_panel_button(surf, buttons["quit"], "QUIT GAME", "Q / Click", accent=(255, 120, 150))

    def draw_help(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 225))
        surf.blit(overlay, (0, 0))

        panel = pygame.Rect(WIDTH // 2 - 330, 70, 660, 410)
        pygame.draw.rect(surf, (22, 18, 46), panel, border_radius=18)
        pygame.draw.rect(surf, (150, 125, 230), panel, 2, border_radius=18)

        title = self.font.render("HOW TO PLAY", True, (245, 230, 170))
        surf.blit(title, title.get_rect(center=(panel.centerx, panel.y + 38)))

        lines = [
            "Type spell words before they reach your wizard.",
            "Correct full word = destroy spell and gain mana.",
            "Wrong input = combo breaks and mana is lost.",
            "",
            "Abilities:",
            "1 - Barrier: blocks the next incoming spell.",
            "2 - Slow Time: slows enemy spells for a few seconds.",
            "3 - Arcane Blast: hits several spells on screen.",
            "",
            "Controls:",
            "Esc - pause menu",
            "F1 - close this help",
            "F11 - fullscreen / windowed",
            "Backspace - delete character",
            "Enter - clear input",
        ]

        y = panel.y + 82
        for line in lines:
            color = (255, 230, 160) if line in ("Abilities:", "Controls:") else (215, 210, 245)
            font = self.font_small if line in ("Abilities:", "Controls:") else self.font_tiny
            text = font.render(line, True, color)
            surf.blit(text, (panel.x + 34, y))
            y += 25 if line else 14

        close = self.font_small.render("Press F1 / Esc or click to close", True, (180, 230, 255))
        surf.blit(close, close.get_rect(center=(panel.centerx, panel.bottom - 30)))

    def draw_float_texts(self, surf):
        for text, x, y, life, color in self.float_texts:
            alpha_color = color
            s = self.font_small.render(text, True, alpha_color)
            surf.blit(s, s.get_rect(center=(int(x), int(y))))

    def draw(self):
        offset_x = random.randint(-5, 5) if self.shake > 0 else 0
        offset_y = random.randint(-4, 4) if self.shake > 0 else 0

        self.update_viewport()
        world = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(world)
        self.draw_wizard(world)

        for spell in self.spells:
            spell.draw(world, self.font_small, self.font_small, self.font_tiny, self.typed)

        for x, y, vx, vy, life, size, color_hint in self.particles:
            alpha = max(0, min(255, int(life * 420)))
            c = tuple(min(255, int((base + alpha) / 2)) for base in color_hint)
            pygame.draw.circle(world, c, (int(x), int(y)), size)

        self.draw_float_texts(world)

        if self.state == "playing":
            self.draw_hud(world)
        elif self.state == "menu":
            self.draw_menu(world)
        elif self.state == "upgrade":
            self.draw_hud(world)
            self.draw_upgrade(world)
        elif self.state == "paused":
            self.draw_hud(world)
            self.draw_pause(world)
        elif self.state == "gameover":
            self.draw_hud(world)
            self.draw_gameover(world)

        if self.show_help:
            self.draw_help(world)

        if self.shake > 0:
            shaken_world = pygame.Surface((WIDTH, HEIGHT))
            shaken_world.fill((12, 10, 28))
            shaken_world.blit(world, (offset_x, offset_y))
            world = shaken_world

        self.screen.fill((4, 3, 12))
        if self.viewport_w == WIDTH and self.viewport_h == HEIGHT:
            scaled_world = world
        else:
            scaled_world = pygame.transform.scale(world, (self.viewport_w, self.viewport_h))
        self.screen.blit(scaled_world, (self.viewport_x, self.viewport_y))

        # Thin frame around the scaled game area helps on ultrawide or tall windows.
        pygame.draw.rect(
            self.screen,
            (55, 45, 95),
            (self.viewport_x, self.viewport_y, self.viewport_w, self.viewport_h),
            max(1, int(2 * self.scale)),
        )
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    new_w = max(640, event.w)
                    new_h = max(360, event.h)
                    self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                    self.update_viewport()
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event)

            # Floating text and particles should continue a bit in non-playing overlays.
            if self.state in ("playing",):
                self.update(dt)
            else:
                self.update_particles_and_text(dt)
                self.shake = max(0, self.shake - dt)
                self.wrong_flash = max(0, self.wrong_flash - dt)

            self.draw()


if __name__ == "__main__":
    Game().run()
