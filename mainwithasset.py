# --- Importation des modules nécessaires ---
import random            # pour générer des événements aléatoires (ex. tirs ennemis)
import pygame            # la bibliothèque principale pour le jeu 2D
import sys               # pour quitter proprement le programme
import math              # pour calculer les trajectoires sinusoïdales
from pathlib import Path # pour gérer les chemins de fichiers (assets) de façon portable

# --- Constantes globales du jeu ---
WIDTH, HEIGHT = 800, 600   # dimensions de la fenêtre du jeu (pixels)
FPS = 60                   # nombre d’images par seconde (fréquence d’actualisation)
WHITE = (255, 255, 255)    # couleur blanche (utilisée pour les textes, transparences)
BLACK = (0, 0, 0)          # couleur noire
GREEN = (80, 220, 100)     # couleur verte (utilisable pour débogage)
RED = (255, 0, 0)          # couleur rouge (utilisable pour erreur ou tir)
PLAYING = 0                # état du jeu : en cours
GAME_OVER = 1              # état du jeu : perdu ou terminé

# --- Répertoire des assets ---
# Cette ligne définit le dossier dans lequel se trouvent toutes les images du jeu.
# On part du dossier où se trouve ce fichier Python (__file__), puis on ajoute "assets".
ASSETS = Path(__file__).parent / "assets"


# ---------------------------------------------------------------
# Classe représentant la balle du joueur
# ---------------------------------------------------------------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=-8):
        """Crée une balle tirée par le joueur (qui monte vers le haut)."""
        super().__init__()                            # initialise la classe Sprite
        self.image = image_surface                    # image affichée pour la balle
        self.rect = self.image.get_rect(midbottom=(x, y))  # position initiale
        self.speed = speed                            # vitesse verticale (négative = monte)

    def update(self, *_):
        """Met à jour la position de la balle à chaque frame."""
        self.rect.y += self.speed                     # déplace la balle verticalement
        if self.rect.bottom < 0:                      # si elle sort de l’écran par le haut
            self.kill()                               # on la supprime (pour libérer mémoire)


# ---------------------------------------------------------------
# Classe représentant un ennemi
# ---------------------------------------------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface):
        super().__init__()
        self.image = image_surface                    # image de l’ennemi
        self.rect = self.image.get_rect(topleft=(x, y))  # position initiale


# ---------------------------------------------------------------
# Classe représentant une balle ennemie avec un mouvement sinusoïdal
# ---------------------------------------------------------------
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=4, amp=60, freq=1.2, phase=0.0, drift=0.0):
        """
        speed : vitesse verticale (px/frame)
        amp   : amplitude horizontale du mouvement sinusoïdal
        freq  : fréquence des oscillations (nombre par seconde)
        phase : décalage initial de la sinusoïde
        drift : dérive horizontale constante
        """
        super().__init__()
        # Crée une simple forme rouge pour la balle ennemie
        self.image = pygame.Surface((4, 12), pygame.SRCALPHA)
        self.image.fill((220, 80, 80))
        self.rect = self.image.get_rect(midtop=(x, y))

        # Paramètres de mouvement
        self.speed = speed
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.drift = drift

        # Variables continues (pour éviter les erreurs d'arrondi)
        self.spawn_x = float(x)
        self.pos_y = float(y)
        self.t = 0.0                                 # temps écoulé
        self.omega = 2.0 * math.pi * self.freq       # pulsation angulaire (2πf)

    def update(self, *_):
        """Mise à jour du mouvement de la balle ennemie."""
        self.t += 1.0 / FPS                          # incrémente le temps simulé
        self.pos_y += self.speed                     # avance verticalement (descend)
        # Mouvement sinusoïdal sur X + dérive
        x = self.spawn_x + self.amp * math.sin(self.phase + self.omega * self.t) + self.drift * (self.t * FPS)
        # Mise à jour de la position réelle sur l’écran
        self.rect.y = int(self.pos_y)
        self.rect.centerx = int(x)
        # Si la balle sort de l’écran → suppression
        if self.rect.top > HEIGHT or self.rect.right < -40 or self.rect.left > WIDTH + 40:
            self.kill()


# ---------------------------------------------------------------
# Classe représentant le joueur
# ---------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=5):
        super().__init__()
        self.image = image_surface                    # image du joueur (vaisseau)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed                            # vitesse horizontale
        self.shoot_cooldown = 250                     # temps minimal entre deux tirs (en ms)
        self.last_shot = 0                            # dernier tir enregistré
        self.lives = 3                                # nombre de vies restantes

    def update(self, keys):
        """Gère le déplacement du joueur à chaque frame."""
        if keys[pygame.K_LEFT]:                       # touche flèche gauche
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:                      # touche flèche droite
            self.rect.x += self.speed
        # Empêche le joueur de sortir de l’écran
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)

    def can_shoot(self):
        """Vérifie si le joueur peut tirer (cooldown écoulé)."""
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown

    def shoot(self, bullets_group, all_sprites_group, bullet_image):
        """Crée une balle si le cooldown le permet."""
        if self.can_shoot():
            bullet = Bullet(self.rect.centerx, self.rect.top, bullet_image)
            bullets_group.add(bullet)
            all_sprites_group.add(bullet)
            self.last_shot = pygame.time.get_ticks()


# ---------------------------------------------------------------
# Classe principale du jeu
# ---------------------------------------------------------------
class Game:
    def __init__(self):
        """Initialisation de la fenêtre, police, et lancement."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))  # création de la fenêtre
        pygame.display.set_caption("Mini Space Invaders")        # titre de la fenêtre
        self.clock = pygame.time.Clock()                         # horloge interne pour FPS
        self.font = pygame.font.SysFont("comicsans", 30)         # police pour le texte
        self.reset()                                             # initialisation du contenu du jeu

    # --- Fonction utilitaire ---
    def load_image(self, filename, size=None, colorkey=None):
        """Charge une image depuis le dossier assets, gère erreurs et redimensionnement."""
        path = ASSETS / filename
        if not path.exists():                                    # si le fichier n’existe pas
            print(f"[⚠] Fichier introuvable : {path}")
            surf = pygame.Surface(size or (50, 50))              # carré rouge par défaut
            surf.fill(RED)
            return surf
        img = pygame.image.load(path).convert()                  # charge l’image
        if colorkey is not None:
            img.set_colorkey(colorkey)                           # rend une couleur transparente
        if size:
            img = pygame.transform.smoothscale(img, size)        # redimensionne si demandé
        return img

    def reset(self):
        """Réinitialise le jeu (nouvelle partie)."""
        # Groupes de sprites (gestion automatique)
        self.all_sprites = pygame.sprite.Group()                 # tous les éléments à dessiner
        self.bullets = pygame.sprite.Group()                     # balles du joueur
        self.enemies = pygame.sprite.Group()                     # ennemis
        self.enemy_bullets = pygame.sprite.Group()               # balles ennemies

        # --- Chargement des images depuis /assets ---
        self.background = self.load_image("Fond.jpg", (WIDTH, HEIGHT))
        self.player_img = self.load_image("PLayer.jpg", (60, 60), WHITE)
        self.enemy_img = self.load_image("vaisseau.jpg", (40, 25))
        self.player_bullet_img = self.load_image("red.jpg", (8, 24))

        # --- Création du joueur ---
        self.player = Player(WIDTH // 2, HEIGHT - 30, self.player_img)
        self.all_sprites.add(self.player)

        # --- Génération de trois rangées d’ennemis ---
        for i in range(9):
            e = Enemy(60 + i * 80, 80, self.enemy_img)
            self.enemies.add(e)
            self.all_sprites.add(e)
        for i in range(7):
            h = Enemy(140 + i * 80, 120, self.enemy_img)
            self.enemies.add(h)
            self.all_sprites.add(h)
        for i in range(5):
            h = Enemy(220 + i * 80, 160, self.enemy_img)
            self.enemies.add(h)
            self.all_sprites.add(h)

        # --- Variables de contrôle de flotte ---
        self.fleet_dir = 1       # direction (1 = droite, -1 = gauche)
        self.fleet_speed = 1     # vitesse horizontale
        self.drop_amount = 15    # descente après rebond sur un bord
        self.state = PLAYING     # état du jeu
        self.score = 0           # score du joueur

    def run(self):
        """Boucle principale du jeu : tourne à l’infini jusqu’à fermeture."""
        while True:
            self.clock.tick(FPS)      # limite à FPS images/seconde
            self.handle_events()      # gestion des touches et événements
            self.update()             # mise à jour des positions et collisions
            self.draw()               # affichage à l’écran

    def handle_events(self):
        """Gère les entrées clavier et la fermeture."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:               # clic sur la croix rouge
                pygame.quit()
                sys.exit()

            # Tir du joueur
            if self.state == PLAYING and event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                self.player.shoot(self.bullets, self.all_sprites, self.player_bullet_img)

            # Rejouer en cas de Game Over
            if self.state == GAME_OVER and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def update(self):
        """Met à jour les objets du jeu (positions, collisions, logique)."""
        keys = pygame.key.get_pressed()                 # récupère l’état du clavier
        if self.state != PLAYING:                      # si pas en jeu, ne rien faire
            return

        self.all_sprites.update(keys)                  # met à jour tous les sprites

        # Déplacement horizontal de la flotte ennemie
        edge_hit = False
        for e in self.enemies:
            e.rect.x += self.fleet_dir * self.fleet_speed
            if e.rect.right >= WIDTH - 5 or e.rect.left <= 5:
                edge_hit = True                        # bord atteint
        if edge_hit:
            self.fleet_dir *= -1                       # inverse la direction
            for e in self.enemies:
                e.rect.y += self.drop_amount           # descend les ennemis d’un cran

        # Gestion des collisions balles ↔ ennemis
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        self.score += len(hits) * 10                   # +10 points par ennemi touché

        # Si un ennemi atteint le bas → fin de partie
        for e in self.enemies:
            if e.rect.bottom >= HEIGHT - 40 or e.rect.colliderect(self.player.rect):
                self.state = GAME_OVER

        # Si plus d’ennemis → victoire
        if not self.enemies:
            self.state = GAME_OVER

        # Tir aléatoire d’un ennemi
        if self.enemies and random.random() < max(0.002, 0.05 * len(self.enemies) / 30.0):
            shooter = random.choice(self.enemies.sprites())
            b = EnemyBullet(shooter.rect.centerx, shooter.rect.bottom)
            self.enemy_bullets.add(b)
            self.all_sprites.add(b)

        # Collision balle ennemie ↔ joueur
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.state = GAME_OVER

    def draw(self):
        """Affiche tous les éléments à l’écran."""
        self.screen.blit(self.background, (0, 0))       # affiche le fond
        self.all_sprites.draw(self.screen)              # affiche les sprites

        # --- HUD (interface) ---
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_surf = self.font.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(lives_surf, (WIDTH - 120, 10))

        # Message de fin de partie
        if self.state == GAME_OVER:
            msg = self.font.render("FIN : Appuie sur R pour recommencer", True, WHITE)
            rect = msg.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2)
            self.screen.blit(msg, rect)

        pygame.display.flip()                           # met à jour l’écran


# ---------------------------------------------------------------
# Lancement du jeu
# ---------------------------------------------------------------
if __name__ == "__main__":
    Game().run()
