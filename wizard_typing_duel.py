import math
import random
import sys
from dataclasses import dataclass

import pygame

# Wizard Typing Duel — tiny pygame MVP
# Controls:
# - Type the word on a flying spell to destroy it.
# - Backspace deletes input.
# - Enter clears input.
# - Esc quits.

WIDTH, HEIGHT = 960, 540
FPS = 60
PLAYER_X = 120
CENTER_Y = HEIGHT // 2

EASY_WORDS = [
    "mana", "fire", "bolt", "hex", "nova", "rune", "mist", "frost", "spark",
    "curse", "shield", "arcane", "ember", "blink", "flare", "void", "orb",
]
MEDIUM_WORDS = [
    "fireball", "moonlight", "starlance", "spellbreak", "crystal", "phantom",
    "thunder", "nightfall", "sunburst", "wardstone", "soulbind",
]
BOSS_PHRASES = [
    "ancient dragon flame", "the moon obeys me", "break the cursed sigil",
    "storm above the tower", "no magic without sacrifice",
]


@dataclass
class Spell:
    word: str
    x: float
    y: float
    speed: float
    radius: int
    wobble: float
    is_boss: bool = False

    def update(self, dt: float):
        self.x -= self.speed * dt
        self.y += math.sin(pygame.time.get_ticks() * 0.004 + self.wobble) * 0.25

    def draw(self, screen, font, small_font):
        # Outer aura
        pulse = 2 + math.sin(pygame.time.get_ticks() * 0.012 + self.wobble) * 2
        pygame.draw.circle(screen, (90, 70, 180), (int(self.x), int(self.y)), self.radius + int(pulse), 2)
        pygame.draw.circle(screen, (185, 140, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (245, 235, 255), (int(self.x - 4), int(self.y - 5)), max(3, self.radius // 4))

        label_font = small_font if len(self.word) > 12 else font
        text = label_font.render(self.word, True, (255, 245, 210))
        rect = text.get_rect(center=(int(self.x), int(self.y - self.radius - 18)))
        pad = 6
        bg = rect.inflate(pad * 2, pad)
        pygame.draw.rect(screen, (25, 18, 45), bg, border_radius=8)
        pygame.draw.rect(screen, (100, 85, 190), bg, 1, border_radius=8)
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
        self.reset()

    def reset(self):
        self.spells = []
        self.particles = []
        self.typed = ""
        self.score = 0
        self.health = 5
        self.level = 1
        self.destroyed = 0
        self.spawn_timer = 0
        self.spawn_delay = 1.75
        self.shake = 0
        self.wrong_flash = 0
        self.state = "menu"

    def spawn_spell(self):
        boss = self.destroyed > 0 and self.destroyed % 10 == 0 and not any(s.is_boss for s in self.spells)
        if boss:
            word = random.choice(BOSS_PHRASES)
            radius = 26
            speed = 58 + self.level * 4
        else:
            pool = EASY_WORDS if self.level < 4 else EASY_WORDS + MEDIUM_WORDS
            word = random.choice(pool)
            radius = 18
            speed = random.randint(75, 115) + self.level * 9

        y = random.randint(90, HEIGHT - 140)
        self.spells.append(Spell(word=word, x=WIDTH + 80, y=y, speed=speed, radius=radius, wobble=random.random() * 10, is_boss=boss))

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

        if self.state in ("menu", "gameover"):
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.reset()
                self.state = "playing"
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

    def check_typing(self):
        # Exact match destroys a spell. Prefix mismatch gives feedback but does not instantly punish too hard.
        matching_prefix = False
        for spell in self.spells:
            if spell.word.startswith(self.typed):
                matching_prefix = True
            if self.typed == spell.word:
                self.explode(spell.x, spell.y, 28 if spell.is_boss else 16)
                self.score += 100 + len(spell.word) * 10 + (250 if spell.is_boss else 0)
                self.destroyed += 1
                self.level = 1 + self.destroyed // 7
                self.spawn_delay = max(0.62, 1.75 - self.level * 0.12)
                self.spells.remove(spell)
                self.typed = ""
                return
        if self.typed and not matching_prefix:
            self.wrong_flash = 0.18

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
                self.health -= 1
                self.shake = 0.22
                self.typed = ""
                self.explode(PLAYER_X, spell.y, 10)
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
        # Stars
        ticks = pygame.time.get_ticks() * 0.001
        for i in range(80):
            x = (i * 137) % WIDTH
            y = (i * 83) % HEIGHT
            twinkle = 80 + int(60 * math.sin(ticks * 2 + i))
            surf.set_at((x, y), (twinkle, twinkle, min(255, twinkle + 50)))
        # Floor line
        pygame.draw.line(surf, (55, 45, 95), (0, HEIGHT - 70), (WIDTH, HEIGHT - 70), 2)

    def draw_wizard(self, surf):
        # Very simple mage silhouette
        x, y = PLAYER_X, CENTER_Y + 50
        pygame.draw.polygon(surf, (80, 60, 160), [(x - 35, y + 70), (x, y - 55), (x + 38, y + 70)])
        pygame.draw.circle(surf, (240, 220, 190), (x, y - 70), 22)
        pygame.draw.polygon(surf, (50, 40, 120), [(x - 32, y - 82), (x + 5, y - 130), (x + 34, y - 82)])
        pygame.draw.line(surf, (180, 140, 80), (x + 32, y - 15), (x + 76, y - 82), 5)
        pygame.draw.circle(surf, (210, 180, 255), (x + 78, y - 86), 8)

    def draw_hud(self, surf):
        hp = self.font.render("HP: " + "♥" * self.health, True, (255, 120, 150))
        score = self.font.render(f"SCORE: {self.score}", True, (255, 235, 180))
        level = self.font.render(f"LVL: {self.level}", True, (180, 220, 255))
        surf.blit(hp, (24, 18))
        surf.blit(score, (24, 52))
        surf.blit(level, (WIDTH - 130, 18))

        color = (255, 90, 90) if self.wrong_flash > 0 else (230, 230, 255)
        prompt = self.font.render("> " + self.typed, True, color)
        pygame.draw.rect(surf, (20, 16, 42), (22, HEIGHT - 55, WIDTH - 44, 36), border_radius=8)
        pygame.draw.rect(surf, (95, 80, 170), (22, HEIGHT - 55, WIDTH - 44, 36), 1, border_radius=8)
        surf.blit(prompt, (34, HEIGHT - 50))

    def draw_menu(self, surf):
        title = self.font_big.render("WIZARD TYPING DUEL", True, (245, 230, 170))
        subtitle = self.font.render("Type spell words before they hit you", True, (210, 210, 245))
        start = self.font.render("Press SPACE or ENTER to start", True, (180, 230, 255))
        tip = self.font_small.render("Backspace = delete | Enter = clear | Esc = quit", True, (150, 145, 190))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 165)))
        surf.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 225)))
        surf.blit(start, start.get_rect(center=(WIDTH // 2, 295)))
        surf.blit(tip, tip.get_rect(center=(WIDTH // 2, 345)))

    def draw_gameover(self, surf):
        title = self.font_big.render("GAME OVER", True, (255, 120, 150))
        score = self.font.render(f"Final score: {self.score}", True, (245, 230, 170))
        restart = self.font.render("Press SPACE or ENTER to restart", True, (180, 230, 255))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 185)))
        surf.blit(score, score.get_rect(center=(WIDTH // 2, 250)))
        surf.blit(restart, restart.get_rect(center=(WIDTH // 2, 315)))

    def draw(self):
        offset_x = random.randint(-5, 5) if self.shake > 0 else 0
        offset_y = random.randint(-4, 4) if self.shake > 0 else 0

        world = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(world)
        self.draw_wizard(world)

        for spell in self.spells:
            spell.draw(world, self.font_small, self.font_small)

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
