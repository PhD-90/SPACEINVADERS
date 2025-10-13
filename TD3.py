import pygame, sys                                   # Importe Pygame (moteur 2D) et sys (pour quitter proprement).
WIDTH, HEIGHT = 800, 600                             # Dimensions de la fenêtre de jeu (largeur x hauteur).
FPS = 60                                             # Fréquence d'affichage visée (images par seconde).
WHITE=(255,255,255);
BLACK=(0,0,0);
GREEN=(80,220,100);
RED=(220,80,80)  # Couleurs RGB utiles.

PLAYING, GAME_OVER = 0, 1                            # États du jeu : en cours (0) ou écran de fin (1).

class Bullet(pygame.sprite.Sprite):                  # Classe projectile (balle), héritant de Sprite.
    def __init__(self, x, y, speed=-8):              # Constructeur : position initiale et vitesse (négative => monte).
        super().__init__()                           # Initialise la classe parente Sprite.
        self.image = pygame.Surface((4, 12))         # Crée une Surface de 4x12 pixels pour représenter la balle.
        self.image.fill(WHITE)                       # Colore la balle en blanc.
        self.rect = self.image.get_rect(midbottom=(x, y))  # Rect centré en bas sur (x,y) (pointe de tir).
        self.speed = speed                           # Enregistre la vitesse verticale.

    def update(self, *_):                            # Mise à jour par frame (ignore les args éventuels).
        self.rect.y += self.speed                    # Déplace la balle verticalement selon sa vitesse.
        if self.rect.bottom < 0: self.kill()         # Si sortie de l'écran par le haut, on supprime la balle.

class Enemy(pygame.sprite.Sprite):                   # Classe Ennemi simple (rectangle rouge).
    def __init__(self, x, y):                        # Position initiale en haut-gauche (x,y).
        super().__init__()                           # Init Sprite parent.
        self.image = pygame.Surface((40, 25))        # Surface 40x25 px pour l'ennemi.
        self.image.fill(RED)                         # Couleur rouge.
        self.rect = self.image.get_rect(topleft=(x, y))  # Place le Rect à (x,y) (coin supérieur gauche).

class Player(pygame.sprite.Sprite):                  # Classe Joueur contrôlé au clavier.
    def __init__(self, x, y, speed=5):               # Position initiale et vitesse horizontale.
        super().__init__()                           # Init Sprite parent.
        self.image = pygame.Surface((60, 20))        # Surface 60x20 px pour le joueur.
        self.image.fill(GREEN)                       # Couleur verte.
        self.rect = self.image.get_rect(midbottom=(x, y))  # Place le Rect (milieu-bas) à (x,y).
        self.speed = speed                           # Vitesse de déplacement horizontal.
        self.shoot_cooldown = 250                    # Délai minimal entre tirs (ms).
        self.last_shot = 0                           # Horodatage du dernier tir (ms).
        self.lives = 3                               # Nombre de vies du joueur.

    def update(self, keys):                          # Mise à jour : gère le déplacement selon le clavier.
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed   # Flèche gauche : se déplacer à gauche.
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed   # Flèche droite : se déplacer à droite.
        self.rect.left = max(self.rect.left, 0)      # Empêche de sortir par la gauche (x >= 0).
        self.rect.right = min(self.rect.right, WIDTH) # Empêche de sortir par la droite (x <= WIDTH).

    def can_shoot(self):                             # Vérifie si le cooldown de tir est écoulé.
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown

    def shoot(self, bullets_group, all_sprites_group):   # Crée et enregistre une balle dans les groupes.
        if self.can_shoot():                         # Si tir autorisé...
            bullet = Bullet(self.rect.centerx, self.rect.top)  # Balle part du centre haut du joueur.
            bullets_group.add(bullet); all_sprites_group.add(bullet)  # Ajout aux groupes (gestion + rendu).
            self.last_shot = pygame.time.get_ticks() # Mémorise le moment du tir.

class Game:                                          # Classe principale gérant le cycle de jeu.
    def __init__(self):                              # Constructeur du jeu.
        pygame.init()                                # Initialise les modules Pygame.
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Crée la fenêtre d'affichage.
        pygame.display.set_caption("Space Invaders - TD3")       # Définit le titre de la fenêtre.
        self.clock = pygame.time.Clock()             # Horloge pour contrôler le FPS.
        self.font = pygame.font.SysFont(None, 32)    # Police par défaut, taille 32, pour le HUD/texte.
        self.reset()                                 # Initialise/relance l'état du jeu (sprites, score, etc.).

    def reset(self):                                 # Réinitialise entièrement une partie.
        self.all_sprites = pygame.sprite.Group()     # Groupe de tous les sprites (update/draw global).
        self.bullets = pygame.sprite.Group()         # Groupe des projectiles (pour collisions et MAJ spécifiques).
        self.enemies = pygame.sprite.Group()         # Groupe des ennemis.

        self.player = Player(WIDTH//2, HEIGHT-30)    # Crée le joueur centré en bas (30 px du bord).
        self.all_sprites.add(self.player)            # Ajoute le joueur au groupe global.

        # grille ennemis
        for row in range(3):                         # 3 rangées...
            for col in range(10):                    # ...de 10 colonnes d'ennemis.
                e = Enemy(60 + col*70, 60 + row*40)  # Calcule la position de chaque ennemi (espacements réguliers).
                self.enemies.add(e); self.all_sprites.add(e)  # Ajoute l'ennemi aux groupes.

        self.fleet_dir = 1  # 1->droite, -1->gauche   # Direction horizontale de la flotte (droite au départ).
        self.fleet_speed = 1.0                        # Vitesse horizontale (pixels/frame) de la flotte.
        self.drop_amount = 15                         # Descente verticale (pixels) quand un bord est touché.

        self.state = PLAYING                          # État du jeu : on commence en mode "en cours".
        self.score = 0                                # Score initial.

    def run(self):                                    # Boucle principale (tourne indéfiniment).
        while True:                                   # Boucle sans fin ; sortie via événements.
            self.clock.tick(FPS)                      # Cadence la boucle à ~FPS itérations par seconde.
            self.handle_events()                      # Traite les entrées utilisateur/événements système.
            self.update()                             # Met à jour la logique du jeu (si PLAYING).
            self.draw()                               # Rendu graphique.

    def handle_events(self):                          # Gestion des événements (clavier, fermeture...).
        for event in pygame.event.get():              # Parcourt la file d'événements.
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()  # Fermeture fenêtre -> quitter proprement.
            if self.state == PLAYING and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.player.shoot(self.bullets, self.all_sprites)     # ESPACE pendant PLAYING : tirer.
            if self.state == GAME_OVER and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()                          # 'R' pendant GAME_OVER : relancer une partie.

    def update(self):                                 # Logique de mise à jour par frame.
        keys = pygame.key.get_pressed()               # État des touches (pressées / non pressées).
        if self.state != PLAYING:                     # Si pas en mode jeu (écran de fin)...
            return                                   # ...ne rien mettre à jour (stop logique).

        # MàJ sprites
        self.all_sprites.update(keys)                 # Appelle update(keys) de tous les sprites (Player utilise keys).

        # Mouvement de flotte (très simple)
        edge_hit = False                              # Indicateur : un ennemi touche un bord ?
        for e in self.enemies:                        # Pour chaque ennemi...
            e.rect.x += self.fleet_dir * self.fleet_speed  # Déplacement horizontal selon direction/vitesse.
            if e.rect.right >= WIDTH-5 or e.rect.left <= 5:  # Si proche d'un bord (marge 5 px)...
                edge_hit = True                       # ...marque qu'on a touché un bord.
        if edge_hit:                                  # Si au moins un ennemi touche un bord...
            self.fleet_dir *= -1                      # ...on inverse la direction de toute la flotte.
            for e in self.enemies:                    # ...et on fait descendre tous les ennemis...
                e.rect.y += self.drop_amount          # ...d'un cran vertical (drop_amount).

        # Collisions balle/ennemi
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)  # Supprime ennemi et balle au contact.
        self.score += len(hits) * 10                   # Ajoute 10 points par ennemi touché ce frame.

        # Défaite : un ennemi touche le bas ou collision avec le joueur
        for e in self.enemies:                         # Vérifie les conditions de fin défavorables.
            if e.rect.bottom >= HEIGHT-40:             # Ennemi trop bas sur l'écran -> game over.
                self.state = GAME_OVER
            if e.rect.colliderect(self.player.rect):   # Collision ennemi/joueur -> perdre une vie et game over.
                self.player.lives -= 1
                self.state = GAME_OVER

        # Victoire (simple) : plus d’ennemis
        if not self.enemies:                           # Si tous les ennemis ont été détruits...
            self.state = GAME_OVER                     # ...on passe aussi par l'écran de fin (replay avec 'R').

    def draw(self):                                    # Rendu graphique (dessin à l'écran).
        self.screen.fill(BLACK)                        # Efface l'écran avec un fond noir.
        self.all_sprites.draw(self.screen)             # Dessine tous les sprites.

        # HUD
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)  # Surface texte pour le score.
        lives_surf = self.font.render(f"Vies: {self.player.lives}", True, WHITE)  # Surface texte pour les vies.
        self.screen.blit(score_surf, (10, 10))         # Affiche le score en haut-gauche.
        self.screen.blit(lives_surf, (WIDTH-120, 10))  # Affiche les vies en haut-droit.

        if self.state == GAME_OVER:                    # Si on est en écran de fin...
            msg = self.font.render("FIN — Appuie sur R pour recommencer", True, WHITE)  # Message de fin.
            rect = msg.get_rect(center=(WIDTH//2, HEIGHT//2))  # Centre le texte au milieu de l'écran.
            self.screen.blit(msg, rect)                # Affiche le message.

        pygame.display.flip()                          # Met à jour l'affichage (double buffering).

if __name__ == "__main__":                             # Point d'entrée si le fichier est exécuté directement.
    Game().run()