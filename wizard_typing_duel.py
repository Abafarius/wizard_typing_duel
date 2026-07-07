import json
import math
import os
import random
import sys
from dataclasses import dataclass

import pygame

# Wizard Typing Duel — v0.3.0 Core Fun Update
# Controls:
# - Menu: 1 = Easy, 2 = Normal, 3 = Hard
# - Type spell words before they hit the wizard.
# - Playing: 1 = Barrier, 2 = Slow Time, 3 = Arcane Blast
# - Upgrade screen: A / S / D = choose upgrade
# - Backspace = delete input, Enter = clear input, P = pause, Esc = quit

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

LANES = [95, 145, 195, 245, 295, 345, 395]

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
        pygame.display.set_caption("Wizard Typing Duel v0.3.0")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("consolas", 42, bold=True)
        self.font = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_tiny = pygame.font.SysFont("consolas", 15, bold=True)
        self.selected_difficulty = "normal"
        self.best_score = self.load_best_score()
        self.reset(keep_menu=True)

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

    def handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

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
            if event.key == pygame.K_p:
                self.state = "playing"
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

        if event.key == pygame.K_p:
            self.state = "paused"
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
        surf.fill((12, 10, 28))
        ticks = pygame.time.get_ticks() * 0.001
        for i in range(90):
            x = (i * 137) % WIDTH
            y = (i * 83) % HEIGHT
            twinkle = 80 + int(60 * math.sin(ticks * 2 + i))
            surf.set_at((x, y), (twinkle, twinkle, min(255, twinkle + 50)))
        pygame.draw.line(surf, (55, 45, 95), (0, HEIGHT - 70), (WIDTH, HEIGHT - 70), 2)
        # Enemy caster silhouette.
        ex, ey = WIDTH - 110, CENTER_Y + 70
        pygame.draw.polygon(surf, (65, 30, 80), [(ex - 38, ey + 60), (ex, ey - 70), (ex + 42, ey + 60)])
        pygame.draw.circle(surf, (120, 70, 135), (ex, ey - 82), 21)
        pygame.draw.circle(surf, (255, 80, 160), (ex - 7, ey - 84), 3)
        pygame.draw.circle(surf, (255, 80, 160), (ex + 7, ey - 84), 3)

    def draw_wizard(self, surf):
        x, y = PLAYER_X, CENTER_Y + 50
        pygame.draw.polygon(surf, (80, 60, 160), [(x - 35, y + 70), (x, y - 55), (x + 38, y + 70)])
        pygame.draw.circle(surf, (240, 220, 190), (x, y - 70), 22)
        pygame.draw.polygon(surf, (50, 40, 120), [(x - 32, y - 82), (x + 5, y - 130), (x + 34, y - 82)])
        pygame.draw.line(surf, (180, 140, 80), (x + 32, y - 15), (x + 76, y - 82), 5)
        pygame.draw.circle(surf, (210, 180, 255), (x + 78, y - 86), 8)

        if self.shield_timer > 0:
            shield_alpha = 100 + int(60 * math.sin(pygame.time.get_ticks() * 0.015))
            pygame.draw.circle(surf, (120, 190, 255), (x + 10, y - 25), 85, 3)
            pygame.draw.circle(surf, (shield_alpha, shield_alpha, 255), (x + 10, y - 25), 72, 1)

    def draw_bar(self, surf, x, y, w, h, value, max_value, fill_color, label):
        value = max(0, min(max_value, value))
        ratio = value / max_value if max_value else 0
        pygame.draw.rect(surf, (25, 18, 45), (x, y, w, h), border_radius=6)
        pygame.draw.rect(surf, fill_color, (x, y, int(w * ratio), h), border_radius=6)
        pygame.draw.rect(surf, (100, 85, 170), (x, y, w, h), 1, border_radius=6)
        txt = self.font_tiny.render(f"{label}: {int(value)}/{int(max_value)}", True, (235, 235, 255))
        surf.blit(txt, (x + 8, y + 2))

    def draw_hud(self, surf):
        hearts = "♥" * max(0, self.health)
        hp = self.font.render("HP: " + hearts, True, (255, 120, 150))
        score = self.font.render(f"SCORE: {self.score}", True, (255, 235, 180))
        level = self.font.render(f"LVL: {self.level}", True, (180, 220, 255))
        diff = self.font_small.render(self.settings["label"], True, (180, 230, 255))
        combo = self.font_small.render(f"COMBO: {self.combo}   BEST: {self.best_combo}", True, (255, 220, 120))
        best = self.font_tiny.render(f"High score: {self.best_score}", True, (160, 155, 205))

        surf.blit(hp, (24, 14))
        surf.blit(score, (24, 47))
        surf.blit(combo, (24, 79))
        surf.blit(best, (24, 105))
        surf.blit(level, (WIDTH - 130, 18))
        surf.blit(diff, (WIDTH - 130, 50))

        self.draw_bar(surf, 24, 128, 225, 20, self.mana, self.mana_cap, (85, 135, 255), "MANA")

        shield_cost = self.ability_cost(35)
        slow_cost = self.ability_cost(45)
        blast_cost = self.ability_cost(70)
        ability_text = self.font_tiny.render(
            f"1 Barrier({shield_cost})  2 Slow({slow_cost})  3 Blast({blast_cost})",
            True,
            (185, 215, 255),
        )
        surf.blit(ability_text, (24, 154))

        timer_parts = []
        if self.shield_timer > 0:
            timer_parts.append(f"Barrier {self.shield_timer:.1f}s")
        if self.slow_timer > 0:
            timer_parts.append(f"Slow {self.slow_timer:.1f}s")
        if timer_parts:
            timers = self.font_tiny.render(" | ".join(timer_parts), True, (255, 235, 160))
            surf.blit(timers, (24, 174))

        color = (255, 90, 90) if self.wrong_flash > 0 else (230, 230, 255)
        prompt = self.font.render("> " + self.typed, True, color)
        pygame.draw.rect(surf, (20, 16, 42), (22, HEIGHT - 55, WIDTH - 44, 36), border_radius=8)
        pygame.draw.rect(surf, (95, 80, 170), (22, HEIGHT - 55, WIDTH - 44, 36), 1, border_radius=8)
        surf.blit(prompt, (34, HEIGHT - 50))

        kills_to_boss = max(0, self.next_boss_at - self.destroyed)
        boss_hint = self.font_tiny.render(f"Boss in: {kills_to_boss} spells", True, (170, 145, 210))
        surf.blit(boss_hint, (WIDTH - 210, HEIGHT - 50))

    def draw_menu(self, surf):
        title = self.font_big.render("WIZARD TYPING DUEL", True, (245, 230, 170))
        version = self.font_small.render("v0.3.0 Core Fun Update", True, (180, 230, 255))
        subtitle = self.font.render("Type spell words. Spend mana. Survive the duel.", True, (210, 210, 245))
        diff = self.font.render(f"Difficulty: {self.settings['label']}  [1 Easy | 2 Normal | 3 Hard]", True, (180, 230, 255))
        start = self.font.render("Press SPACE or ENTER to start", True, (255, 220, 120))
        tip = self.font_small.render("Playing: 1 Barrier | 2 Slow Time | 3 Arcane Blast | P Pause", True, (150, 145, 190))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 120)))
        surf.blit(version, version.get_rect(center=(WIDTH // 2, 165)))
        surf.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 215)))
        surf.blit(diff, diff.get_rect(center=(WIDTH // 2, 280)))
        surf.blit(start, start.get_rect(center=(WIDTH // 2, 340)))
        surf.blit(tip, tip.get_rect(center=(WIDTH // 2, 390)))

    def draw_upgrade(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 210))
        surf.blit(overlay, (0, 0))
        title = self.font_big.render("LEVEL UP — CHOOSE A RUNE", True, (255, 230, 160))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 105)))

        keys = ["A", "S", "D"]
        card_w, card_h = 260, 160
        start_x = WIDTH // 2 - card_w - 18 - card_w // 2
        y = 210
        for i, upgrade in enumerate(self.upgrade_choices):
            x = start_x + i * (card_w + 36)
            rect = pygame.Rect(x, y, card_w, card_h)
            pygame.draw.rect(surf, (24, 18, 48), rect, border_radius=14)
            pygame.draw.rect(surf, (145, 120, 220), rect, 2, border_radius=14)
            key_surf = self.font.render(keys[i], True, (255, 230, 160))
            title_surf = self.font_small.render(upgrade["title"], True, (230, 225, 255))
            desc_surf = self.font_tiny.render(upgrade["desc"], True, (185, 190, 225))
            surf.blit(key_surf, key_surf.get_rect(center=(x + card_w // 2, y + 38)))
            surf.blit(title_surf, title_surf.get_rect(center=(x + card_w // 2, y + 82)))
            surf.blit(desc_surf, desc_surf.get_rect(center=(x + card_w // 2, y + 120)))

        hint = self.font_small.render("The duel is paused. Pick one upgrade.", True, (175, 180, 220))
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, 430)))

    def draw_gameover(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 190))
        surf.blit(overlay, (0, 0))
        title = self.font_big.render("GAME OVER", True, (255, 120, 150))
        score = self.font.render(f"Final score: {self.score}", True, (245, 230, 170))
        best = self.font.render(f"High score: {self.best_score}", True, (180, 230, 255))
        combo = self.font.render(f"Best combo: {self.best_combo}", True, (255, 220, 120))
        restart = self.font.render("SPACE/ENTER = restart | M = menu", True, (180, 230, 255))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
        surf.blit(score, score.get_rect(center=(WIDTH // 2, 220)))
        surf.blit(best, best.get_rect(center=(WIDTH // 2, 260)))
        surf.blit(combo, combo.get_rect(center=(WIDTH // 2, 300)))
        surf.blit(restart, restart.get_rect(center=(WIDTH // 2, 365)))

    def draw_pause(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 4, 15, 180))
        surf.blit(overlay, (0, 0))
        title = self.font_big.render("PAUSED", True, (245, 230, 170))
        hint = self.font.render("Press P to continue", True, (180, 230, 255))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 230)))
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, 295)))

    def draw_float_texts(self, surf):
        for text, x, y, life, color in self.float_texts:
            alpha_color = color
            s = self.font_small.render(text, True, alpha_color)
            surf.blit(s, s.get_rect(center=(int(x), int(y))))

    def draw(self):
        offset_x = random.randint(-5, 5) if self.shake > 0 else 0
        offset_y = random.randint(-4, 4) if self.shake > 0 else 0

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

        self.screen.blit(world, (offset_x, offset_y))
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event)

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
