import math
import random
import sys
from dataclasses import dataclass

import pygame

# Wizard Typing Duel — Step 2 Gameplay Balance
# Controls:
# - Menu: 1 = Easy, 2 = Normal, 3 = Hard
# - Type the word on a flying spell to destroy it.
# - Backspace deletes input.
# - Enter clears input.
# - Esc quits.

WIDTH, HEIGHT = 960, 540
FPS = 60
PLAYER_X = 120
CENTER_Y = HEIGHT // 2

# -----------------------------
# BALANCE SETTINGS
# Меняй эти значения, если хочешь быстро подкрутить игру.
# -----------------------------
DIFFICULTIES = {
    "easy": {
        "label": "EASY",
        "health": 7,
        "base_spawn_delay": 1.85,
        "min_spawn_delay": 0.78,
        "speed_min": 62,
        "speed_max": 98,
        "speed_per_level": 6,
        "max_spells": 5,
        "level_every": 8,
        "boss_every": 12,
    },
    "normal": {
        "label": "NORMAL",
        "health": 5,
        "base_spawn_delay": 1.55,
        "min_spawn_delay": 0.62,
        "speed_min": 78,
        "speed_max": 122,
        "speed_per_level": 9,
        "max_spells": 6,
        "level_every": 7,
        "boss_every": 10,
    },
    "hard": {
        "label": "HARD",
        "health": 4,
        "base_spawn_delay": 1.22,
        "min_spawn_delay": 0.48,
        "speed_min": 100,
        "speed_max": 150,
        "speed_per_level": 12,
        "max_spells": 7,
        "level_every": 6,
        "boss_every": 8,
    },
}

SHORT_WORDS = [
    "mana", "fire", "bolt", "hex", "nova", "rune", "mist", "frost", "spark",
    "curse", "ward", "ember", "blink", "flare", "void", "orb", "moon", "star",
    "ash", "ice", "doom", "light", "chaos", "glyph", "magic", "soul",
]

MEDIUM_WORDS = [
    "shield", "arcane", "fireball", "moonlight", "starlance", "crystal",
    "phantom", "thunder", "nightfall", "sunburst", "wardstone", "soulbind",
    "spellbreak", "witchfire", "runeblade", "dreamdust", "bloodmoon",
]

HARD_WORDS = [
    "astral prison", "silver eclipse", "forbidden rune", "mirror curse",
    "celestial spear", "shadow covenant", "obsidian circle", "dragon sigil",
]

BOSS_PHRASES = [
    "ancient dragon flame",
    "the moon obeys me",
    "break the cursed sigil",
    "storm above the tower",
    "no magic without sacrifice",
    "stars fall when i speak",
]

LANES = [95, 145, 195, 245, 295, 345, 395]


@dataclass
class Spell:
    word: str
    x: float
    y: float
    speed: float
    radius: int
    wobble: float
    spell_type: str = "normal"  # normal / hard / boss

    def update(self, dt: float):
        self.x -= self.speed * dt
        self.y += math.sin(pygame.time.get_ticks() * 0.004 + self.wobble) * 0.25

    def draw(self, screen, font, small_font, typed):
        is_targeted = bool(typed) and self.word.startswith(typed)
        is_boss = self.spell_type == "boss"
        is_hard = self.spell_type == "hard"

        if is_boss:
            aura_color = (190, 55, 135)
            core_color = (255, 100, 185)
            border_color = (255, 190, 230)
        elif is_hard:
            aura_color = (70, 135, 190)
            core_color = (90, 195, 255)
            border_color = (210, 245, 255)
        else:
            aura_color = (90, 70, 180)
            core_color = (185, 140, 255)
            border_color = (245, 235, 255)

        pulse = 2 + math.sin(pygame.time.get_ticks() * 0.012 + self.wobble) * 2
        pygame.draw.circle(screen, aura_color, (int(self.x), int(self.y)), self.radius + int(pulse), 2)
        pygame.draw.circle(screen, core_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, border_color, (int(self.x - 4), int(self.y - 5)), max(3, self.radius // 4))

        if is_targeted:
            pygame.draw.circle(screen, (255, 245, 170), (int(self.x), int(self.y)), self.radius + 8, 3)

        label_font = small_font if len(self.word) > 12 else font
        text_color = (255, 245, 210)
        text = label_font.render(self.word, True, text_color)
        rect = text.get_rect(center=(int(self.x), int(self.y - self.radius - 18)))
        pad = 6
        bg = rect.inflate(pad * 2, pad)
        bg_color = (25, 18, 45) if not is_targeted else (60, 48, 25)
        border = (100, 85, 190) if not is_targeted else (255, 220, 120)
        pygame.draw.rect(screen, bg_color, bg, border_radius=8)
        pygame.draw.rect(screen, border, bg, 1, border_radius=8)
        screen.blit(text, rect)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wizard Typing Duel")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("consolas", 42, bold=True)
        self.font = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_tiny = pygame.font.SysFont("consolas", 15, bold=True)
        self.selected_difficulty = "normal"
        self.reset(keep_menu=True)

    def reset(self, keep_menu=False):
        self.settings = DIFFICULTIES[self.selected_difficulty]
        self.spells = []
        self.particles = []
        self.typed = ""
        self.score = 0
        self.health = self.settings["health"]
        self.level = 1
        self.destroyed = 0
        self.combo = 0
        self.best_combo = 0
        self.spawn_timer = 0
        self.spawn_delay = self.settings["base_spawn_delay"]
        self.shake = 0
        self.wrong_flash = 0
        self.next_boss_at = self.settings["boss_every"]
        self.state = "menu" if keep_menu else "playing"

    def choose_word(self):
        # С ростом уровня появляются более длинные и опасные слова.
        if self.destroyed >= self.next_boss_at:
            self.next_boss_at += self.settings["boss_every"]
            return random.choice(BOSS_PHRASES), "boss"

        roll = random.random()
        if self.level <= 2:
            return random.choice(SHORT_WORDS), "normal"
        if self.level <= 4:
            if roll < 0.72:
                return random.choice(SHORT_WORDS), "normal"
            return random.choice(MEDIUM_WORDS), "normal"
        if self.level <= 6:
            if roll < 0.45:
                return random.choice(SHORT_WORDS), "normal"
            if roll < 0.88:
                return random.choice(MEDIUM_WORDS), "normal"
            return random.choice(HARD_WORDS), "hard"

        if roll < 0.30:
            return random.choice(SHORT_WORDS), "normal"
        if roll < 0.75:
            return random.choice(MEDIUM_WORDS), "normal"
        return random.choice(HARD_WORDS), "hard"

    def get_spawn_y(self):
        # Выбираем линию, где меньше всего пересечений, чтобы слова не налезали друг на друга.
        random.shuffle(LANES)
        for lane in LANES:
            too_close = any(abs(spell.y - lane) < 38 and spell.x > WIDTH - 260 for spell in self.spells)
            if not too_close:
                return lane
        return random.choice(LANES)

    def spawn_spell(self):
        if len(self.spells) >= self.settings["max_spells"]:
            return

        word, spell_type = self.choose_word()
        if spell_type == "boss":
            radius = 28
            speed = self.settings["speed_min"] * 0.72 + self.level * 5
        elif spell_type == "hard":
            radius = 22
            speed = random.randint(self.settings["speed_min"], self.settings["speed_max"]) * 0.86 + self.level * self.settings["speed_per_level"]
        else:
            radius = 18
            speed = random.randint(self.settings["speed_min"], self.settings["speed_max"]) + self.level * self.settings["speed_per_level"]

        self.spells.append(
            Spell(
                word=word,
                x=WIDTH + random.randint(40, 160),
                y=self.get_spawn_y(),
                speed=speed,
                radius=radius,
                wobble=random.random() * 10,
                spell_type=spell_type,
            )
        )

    def explode(self, x, y, amount=18):
        for _ in range(amount):
            angle = random.random() * math.tau
            speed = random.uniform(70, 220)
            self.particles.append([
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.25, 0.65), random.randint(2, 5)
            ])

    def handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        if self.state == "menu":
            if event.key == pygame.K_1:
                self.selected_difficulty = "easy"
            elif event.key == pygame.K_2:
                self.selected_difficulty = "normal"
            elif event.key == pygame.K_3:
                self.selected_difficulty = "hard"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset(keep_menu=False)
            return

        if self.state == "gameover":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset(keep_menu=False)
            elif event.key == pygame.K_m:
                self.reset(keep_menu=True)
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
        self.level = 1 + self.destroyed // self.settings["level_every"]
        base = self.settings["base_spawn_delay"]
        minimum = self.settings["min_spawn_delay"]
        self.spawn_delay = max(minimum, base - self.level * 0.105)

    def check_typing(self):
        matching_prefix = False

        # Сначала бьем ближайшее к игроку заклинание, если есть несколько одинаковых слов.
        for spell in sorted(self.spells, key=lambda s: s.x):
            if spell.word.startswith(self.typed):
                matching_prefix = True
            if self.typed == spell.word:
                self.explode(spell.x, spell.y, 34 if spell.spell_type == "boss" else 20)

                base_points = 100 + len(spell.word) * 12
                if spell.spell_type == "hard":
                    base_points += 90
                if spell.spell_type == "boss":
                    base_points += 320
                combo_bonus = min(250, self.combo * 12)

                self.score += base_points + combo_bonus
                self.destroyed += 1
                self.combo += 1
                self.best_combo = max(self.best_combo, self.combo)
                self.update_balance_after_kill()

                self.spells.remove(spell)
                self.typed = ""
                return

        if self.typed and not matching_prefix:
            self.wrong_flash = 0.18
            self.combo = 0

    def update(self, dt):
        if self.state != "playing":
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.spawn_spell()

        for spell in self.spells[:]:
            spell.update(dt)
            if spell.x < PLAYER_X + 20:
                self.spells.remove(spell)
                damage = 2 if spell.spell_type == "boss" else 1
                self.health -= damage
                self.combo = 0
                self.shake = 0.22
                self.typed = ""
                self.explode(PLAYER_X, spell.y, 14 if spell.spell_type == "boss" else 9)
                if self.health <= 0:
                    self.state = "gameover"

        for p in self.particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            if p[4] <= 0:
                self.particles.remove(p)

        self.shake = max(0, self.shake - dt)
        self.wrong_flash = max(0, self.wrong_flash - dt)

    def draw_background(self, surf):
        surf.fill((12, 10, 28))
        ticks = pygame.time.get_ticks() * 0.001
        for i in range(80):
            x = (i * 137) % WIDTH
            y = (i * 83) % HEIGHT
            twinkle = 80 + int(60 * math.sin(ticks * 2 + i))
            surf.set_at((x, y), (twinkle, twinkle, min(255, twinkle + 50)))
        pygame.draw.line(surf, (55, 45, 95), (0, HEIGHT - 70), (WIDTH, HEIGHT - 70), 2)

    def draw_wizard(self, surf):
        x, y = PLAYER_X, CENTER_Y + 50
        pygame.draw.polygon(surf, (80, 60, 160), [(x - 35, y + 70), (x, y - 55), (x + 38, y + 70)])
        pygame.draw.circle(surf, (240, 220, 190), (x, y - 70), 22)
        pygame.draw.polygon(surf, (50, 40, 120), [(x - 32, y - 82), (x + 5, y - 130), (x + 34, y - 82)])
        pygame.draw.line(surf, (180, 140, 80), (x + 32, y - 15), (x + 76, y - 82), 5)
        pygame.draw.circle(surf, (210, 180, 255), (x + 78, y - 86), 8)

    def draw_hud(self, surf):
        hearts = "♥" * max(0, self.health)
        hp = self.font.render("HP: " + hearts, True, (255, 120, 150))
        score = self.font.render(f"SCORE: {self.score}", True, (255, 235, 180))
        level = self.font.render(f"LVL: {self.level}", True, (180, 220, 255))
        diff = self.font_small.render(self.settings["label"], True, (180, 230, 255))
        combo = self.font_small.render(f"COMBO: {self.combo}", True, (255, 220, 120))

        surf.blit(hp, (24, 18))
        surf.blit(score, (24, 52))
        surf.blit(combo, (24, 84))
        surf.blit(level, (WIDTH - 130, 18))
        surf.blit(diff, (WIDTH - 130, 50))

        color = (255, 90, 90) if self.wrong_flash > 0 else (230, 230, 255)
        prompt = self.font.render("> " + self.typed, True, color)
        pygame.draw.rect(surf, (20, 16, 42), (22, HEIGHT - 55, WIDTH - 44, 36), border_radius=8)
        pygame.draw.rect(surf, (95, 80, 170), (22, HEIGHT - 55, WIDTH - 44, 36), 1, border_radius=8)
        surf.blit(prompt, (34, HEIGHT - 50))

        # Маленькая полоска до следующего босса.
        kills_to_boss = max(0, self.next_boss_at - self.destroyed)
        boss_hint = self.font_tiny.render(f"Boss in: {kills_to_boss} spells", True, (170, 145, 210))
        surf.blit(boss_hint, (WIDTH - 210, HEIGHT - 50))

    def draw_menu(self, surf):
        title = self.font_big.render("WIZARD TYPING DUEL", True, (245, 230, 170))
        subtitle = self.font.render("Type spell words before they hit you", True, (210, 210, 245))
        diff = self.font.render(f"Difficulty: {self.settings['label']}  [1 Easy | 2 Normal | 3 Hard]", True, (180, 230, 255))
        start = self.font.render("Press SPACE or ENTER to start", True, (255, 220, 120))
        tip = self.font_small.render("Backspace = delete | Enter = clear | Esc = quit", True, (150, 145, 190))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 145)))
        surf.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 205)))
        surf.blit(diff, diff.get_rect(center=(WIDTH // 2, 270)))
        surf.blit(start, start.get_rect(center=(WIDTH // 2, 330)))
        surf.blit(tip, tip.get_rect(center=(WIDTH // 2, 380)))

    def draw_gameover(self, surf):
        title = self.font_big.render("GAME OVER", True, (255, 120, 150))
        score = self.font.render(f"Final score: {self.score}", True, (245, 230, 170))
        combo = self.font.render(f"Best combo: {self.best_combo}", True, (255, 220, 120))
        restart = self.font.render("SPACE/ENTER = restart | M = menu", True, (180, 230, 255))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 165)))
        surf.blit(score, score.get_rect(center=(WIDTH // 2, 230)))
        surf.blit(combo, combo.get_rect(center=(WIDTH // 2, 270)))
        surf.blit(restart, restart.get_rect(center=(WIDTH // 2, 335)))

    def draw(self):
        offset_x = random.randint(-5, 5) if self.shake > 0 else 0
        offset_y = random.randint(-4, 4) if self.shake > 0 else 0

        world = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(world)
        self.draw_wizard(world)

        for spell in self.spells:
            spell.draw(world, self.font_small, self.font_small, self.typed)

        for x, y, vx, vy, life, size in self.particles:
            alpha = max(0, min(255, int(life * 420)))
            pygame.draw.circle(world, (alpha, alpha, 255), (int(x), int(y)), size)

        if self.state == "playing":
            self.draw_hud(world)
        elif self.state == "menu":
            self.draw_menu(world)
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
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
