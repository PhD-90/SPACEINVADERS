import random

import pygame
import sys
import math
# --- Constantes globales ---
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (80, 220, 100)
RED = (255, 0, 0)
PLAYING = 0
GAME_OVER = 1

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=-8):  # balle du joueur (monte)
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed

    def update(self, *_):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(topleft=(x, y))

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=4, amp=60, freq=1.2, phase=0.0, drift=0.0):
        """
        speed : vitesse verticale (px/frame)
        amp   : amplitude horizontale (px)
        freq  : fréquence en Hz (oscillations par seconde, approx si FPS constant)
        phase : phase initiale (radians)
        drift : dérive horizontale constante (px/frame), 0 = aucune
        """
        super().__init__()
        # sprite simple (remplace par ton image si tu veux)
        self.image = pygame.Surface((4, 12), pygame.SRCALPHA)
        self.image.fill((220, 80, 80))
        self.rect = self.image.get_rect(midtop=(x, y))

        # paramètres de mouvement
        self.speed = speed
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.drift = drift

        # états continus (pour éviter les erreurs d'arrondi)
        self.spawn_x = float(x)
        self.pos_y = float(y)
        self.t = 0.0  # temps "simulé" en secondes approx
        self.omega = 2.0 * math.pi * self.freq

    def update(self, *_):
        # incrémente le temps (approx si tu tournes à FPS constant)
        self.t += 1.0 / FPS

        # avance verticalement
        self.pos_y += self.speed

        # oscillation horizontale + dérive éventuelle
        x = self.spawn_x + self.amp * math.sin(self.phase + self.omega * self.t) + self.drift * (self.t * FPS)

        # applique la position
        self.rect.y = int(self.pos_y)
        self.rect.centerx = int(x)

        # hors écran -> suppression
        if self.rect.top > HEIGHT or self.rect.right < -40 or self.rect.left > WIDTH + 40:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=5):
        super().__init__()
        # Image du joueur (déjà redimensionnée en amont)
        self.image = image_surface
        # placé comme avant : milieu-bas au point (x,y)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed
        self.shoot_cooldown = 250  # ms
        self.last_shot = 0
        self.lives = 3

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown

    def shoot(self, bullets_group, all_sprites_group, bullet_image):
        if self.can_shoot():
            bullet = Bullet(self.rect.centerx, self.rect.top, bullet_image)  # ← passe l'image
            bullets_group.add(bullet)
            all_sprites_group.add(bullet)
            self.last_shot = pygame.time.get_ticks()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders (simple)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("comicsans", 30)
        self.reset()


    def reset(self):
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()  #
        # --- FOND ---
        # Chemin fourni (image 1) : /mnt/data/Fond.jpg
        bg_raw = pygame.image.load(r"C:\Users\LouisMougenot\OneDrive - NEEXT Engineering\SPARTA\MODELE\PYTHON\Cours\JEUX\Fond.jpg").convert()    # pas d'alpha → convert()
        self.background = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))

        # --- IMAGE JOUEUR ---
        # Chemin fourni (image 2) : /mnt/data/PLayer.jpg
        player_raw = pygame.image.load(r"C:\Users\LouisMougenot\OneDrive - NEEXT Engineering\SPARTA\MODELE\PYTHON\Cours\JEUX\PLayer.jpg").convert()
        # rendre le blanc transparent (utile pour un JPEG silhouette sur fond blanc)
        player_raw.set_colorkey(WHITE)
        # redimensionner le tireur (ajuste si tu veux)
        self.player_img = pygame.transform.smoothscale(player_raw, (60, 60))

        # --- IMAGE ENNEMI (ton JPEG local existant) ---
        img_path_enemy = r"C:\Users\LouisMougenot\OneDrive - NEEXT Engineering\SPARTA\MODELE\PYTHON\Cours\JEUX\vaisseau.jpg"
        enemy_raw = pygame.image.load(img_path_enemy).convert()
        self.enemy_img = pygame.transform.smoothscale(enemy_raw, (40, 25))

        # PNG conseillés avec transparence
        player_bullet_raw = pygame.image.load(
            r"C:\Users\LouisMougenot\OneDrive - NEEXT Engineering\SPARTA\MODELE\PYTHON\Cours\JEUX\red.jpg"
        ).convert()
        # Redimension (ajuste selon ton sprite source)
        self.player_bullet_img = pygame.transform.smoothscale(player_bullet_raw, (8, 24))
        # Joueur (utilise l'image)
        self.player = Player(WIDTH // 2, HEIGHT - 30, self.player_img)
        self.all_sprites.add(self.player)

        # deux rangées d'ennemis
        for i in range(9):
            e = Enemy(60 + i * 80, 80, self.enemy_img)

            self.enemies.add(e)
            self.all_sprites.add(e)

            # deux rangées d'ennemis
        for i in range(7):
                h = Enemy(140 + i * 80, 120, self.enemy_img)
                self.enemies.add( h)
                self.all_sprites.add( h)

        for i in range(5):
            h = Enemy(220 + i * 80, 160, self.enemy_img)
            self.enemies.add(h)
            self.all_sprites.add(h)

        self.fleet_dir = 1 # 1 droite ; 0 gauche
        self.fleet_speed = 1
        self.drop_amount = 15
        self.state = PLAYING
        self.score = 0


    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == PLAYING and event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                self.player.shoot(self.bullets, self.all_sprites, self.player_bullet_img)

            if self.state == GAME_OVER and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def update(self):
        keys = pygame.key.get_pressed()
        if self.state != PLAYING:
            return

        self.all_sprites.update(keys)

        edge_hit = False
        for e in self.enemies:
            e.rect.x += self.fleet_dir * self.fleet_speed
            if e.rect.right >= WIDTH-5 or e.rect.left <= 5:
                edge_hit = True
        if edge_hit:
            self.fleet_dir *= -1
            for e in self.enemies:
                e.rect.y += self.drop_amount

        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        self.score += len(hits)*10

        for e in self.enemies:
            if e.rect.bottom >= HEIGHT-40:
                self.state = GAME_OVER
            if e.rect.colliderect(self.player.rect):
                self.player.lives -= 1
                self.state = GAME_OVER

        if not self.enemies:
            self.state = GAME_OVER

        self.enemy_bullet = getattr(self, "ennemy_bullets", pygame.sprite.Group())
        if self.enemies:
            n = len(self.enemies)
            p = max(0.002, 0.05 * n / 30.0)
            if random.random() < p:  # <- utilise random.random()
                shooter = random.choice(self.enemies.sprites())  # <- choix dans le module random
                b = EnemyBullet(shooter.rect.centerx, shooter.rect.bottom)
                self.enemy_bullets.add(b)  # <- dans le bon groupe
                self.all_sprites.add(b)

        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.state = GAME_OVER

    def draw(self):
        # dessiner le fond d'abord
        self.screen.blit(self.background, (0, 0))
        # puis les sprites par-dessus
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

        #HUD
        score_surf = self.font.render("Score: %d" % self.score, True, WHITE)
        lives_surf = self.font.render("Lives: %d" % self.player.lives, True, WHITE)
        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(lives_surf, (WIDTH-120, 10))

        if self.state == GAME_OVER:
            msg = self.font.render("FIN : Appuie sur R pour recommencer", True, WHITE)
            rect = msg.get_rect(centerx=WIDTH//2, centery=HEIGHT//2)
            self.screen.blit(msg, rect)

        pygame.display.flip()


if __name__ == "__main__":
    Game().run()
