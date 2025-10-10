# -----------------------------------------------------------------------------
# Introduction – Space Invaders (tir + ennemis + collisions) avec Pygame
#
# Objectif
# --------
# Étendre la base Pygame pour gérer :
# - un joueur mobile,
# - des projectiles (Bullets) avec cadence de tir (cooldown),
# - des ennemis simples,
# - la détection de collisions bullet/enemy et la suppression des sprites touchés.
#
# Rappels Pygame
# --------------
# - Sprite : objet de jeu standard (image + rect + update()).
# - Group : collection de sprites ; on peut faire group.update(args) et group.draw(screen).
# - Surface : zone graphique du sprite (dessin/couleur).
# - Rect : boîte (x, y, w, h) pour positionnement et collisions.
# - get_ticks() : horloge interne Pygame (en millisecondes) utile pour gérer les cooldowns.
#
# Architecture du code
# --------------------
# 1) Constantes : taille fenêtre (WIDTH, HEIGHT), FPS, couleurs.
# 2) Bullet(Sprite) :
#    - projectiles fins (4x12 px), blancs, partent vers le haut (speed négative),
#    - update() : translate verticalement ; auto-destruction quand hors-écran (kill()).
# 3) Enemy(Sprite) :
#    - petit rectangle rouge, positionné en grille simple (immobile ici, parfait pour tests).
# 4) Player(Sprite) :
#    - rectangle vert contrôlé gauche/droite, borné aux limites de l’écran,
#    - tir avec délai minimal entre deux tirs (shoot_cooldown en ms via get_ticks()),
#    - shoot() crée une Bullet et l’ajoute aux groupes bullets et all_sprites.
# 5) Game :
#    - init Pygame, fenêtre, horloge, et 3 groupes :
#        * all_sprites : tous les sprites à mettre à jour et dessiner,
#        * bullets     : uniquement les projectiles (facilite les collisions),
#        * enemies     : les ennemis.
#    - création du joueur + d’une rangée d’ennemis statiques pour tests.
#    - boucle principale :
#        a) handle_events() : fermeture fenêtre ; tir au SPACE -> player.shoot(...)
#        b) update() :
#           - all_sprites.update(keys) : player reçoit keys ; bullets/ennemies ignorent (signature compatible)
#           - collisions bullet/enemy via pygame.sprite.groupcollide(...)
#             * groupcollide(enemies, bullets, True, True) supprime un ennemi et la balle au contact,
#             * renvoie un dict des collisions ; ici on logge len(hits) pour visualiser.
#        c) draw() : fond noir + rendu des sprites + flip d’affichage.
#    - sortie propre : pygame.quit(); sys.exit()
#
# Boucle de jeu (rappel)
# ----------------------
# while running:
#     clock.tick(FPS)          # cadence fixe
#     handle_events()          # clavier/souris
#     update()                 # logique, tir, collisions
#     draw()                   # rendu et flip
#
# Points d’extension
# ------------------
# - Mouvements d’ennemis (patrouille, descente par paliers, zigzag).
# - Vagues / spawn dynamique d’ennemis, score et HUD (pygame.font).
# - Sons de tir/explosion (pygame.mixer).
# - Système de vies, fin de partie, redémarrage.
# - Optimisations : limiter les checks de collision avec des sous-groupes / spatial hashing.
#
# Exécution
# ---------
# - Installer : `pip install pygame`
# - Lancer    : `python ton_fichier.py`
#
# Notes pédagogiques
# ------------------
# - groupcollide(A, B, dokillA, dokillB) gère les collisions entre deux Group :
#   * True/True supprime l’ennemi ET la balle au contact (ici).
# - Le cooldown de tir empêche le spam : on compare l’horloge courante (ms) au dernier tir.
# -----------------------------------------------------------------------------
import pygame, sys                                   # Importe Pygame (moteur 2D) et sys (pour quitter proprement).
WIDTH, HEIGHT = 800, 600                             # Dimensions de la fenêtre de jeu : largeur 800 px, hauteur 600 px.
FPS = 60                                             # Fréquence d'affichage visée : 60 images par seconde.
WHITE=(255,255,255); BLACK=(0,0,0); GREEN=(80,220,100); RED=(220,80,80)  # Définition de quelques couleurs RGB.

class Bullet(pygame.sprite.Sprite):                  # Classe Projectile, héritée de Sprite pour profiter des Group/update/draw.
    def __init__(self, x, y, speed=-8):              # Constructeur : position initiale (x,y) et vitesse verticale (vers le haut si négative).
        super().__init__()                           # Initialise la partie Sprite (classe parente).
        self.image = pygame.Surface((4, 12))         # Crée l'image du projectile : un petit rectangle 4x12 px.
        self.image.fill(WHITE)                       # Remplit le rectangle en blanc.
        self.rect = self.image.get_rect(midbottom=(x, y))  # Crée le Rect associé et place son milieu-bas à (x,y).
        self.speed = speed                           # Stocke la vitesse verticale (négative => monte).

    def update(self, *_):                            # Mise à jour à chaque frame ; *_ accepte et ignore d'éventuels arguments (ex: keys).
        self.rect.y += self.speed                    # Déplace le projectile verticalement selon sa vitesse.
        if self.rect.bottom < 0:                     # Si le bas du projectile dépasse le haut de l'écran (hors champ)...
            self.kill()                              # ...on le supprime du jeu (retiré de tous les Group).

class Enemy(pygame.sprite.Sprite):                   # Classe Ennemi, simple Sprite statique pour tests.
    def __init__(self, x, y):                        # Constructeur : position de départ coin haut-gauche (x,y).
        super().__init__()                           # Initialise la classe parente Sprite.
        self.image = pygame.Surface((40, 25))        # Crée l'image de l'ennemi : rectangle 40x25 px.
        self.image.fill(RED)                         # Remplit en rouge.
        self.rect = self.image.get_rect(topleft=(x, y))  # Place le Rect en haut-gauche à (x,y).

class Player(pygame.sprite.Sprite):                  # Classe Joueur, contrôlé au clavier.
    def __init__(self, x, y, speed=5):               # Constructeur : position initiale et vitesse horizontale.
        super().__init__()                           # Initialise la classe parente Sprite.
        self.image = pygame.Surface((60, 20))        # Image du joueur : rectangle 60x20 px.
        self.image.fill(GREEN)                       # Remplit en vert.
        self.rect = self.image.get_rect(midbottom=(x, y))  # Place le Rect (milieu-bas) à (x,y).
        self.speed = speed                           # Vitesse de déplacement horizontale.
        self.shoot_cooldown = 250  # ms              # Délai minimal entre deux tirs (en millisecondes).
        self.last_shot = 0                           # Timestamp du dernier tir (ms), 0 au départ.

    def update(self, keys):                          # Mise à jour du joueur (réagit aux touches pressées).
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed   # Si flèche gauche pressée, déplace vers la gauche.
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed   # Si flèche droite pressée, déplace vers la droite.
        self.rect.left = max(self.rect.left, 0)      # Empêche de sortir par la gauche (x >= 0).
        self.rect.right = min(self.rect.right, WIDTH) # Empêche de sortir par la droite (x <= WIDTH).

    def can_shoot(self):                             # Indique si le cooldown est écoulé.
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown  # Compare le temps écoulé au délai.

    def shoot(self, bullets_group, all_sprites_group):  # Crée un projectile et l'ajoute aux groupes si cooldown OK.
        if self.can_shoot():                         # Vérifie qu'on peut tirer maintenant.
            bullet = Bullet(self.rect.centerx, self.rect.top)  # Crée une balle à la position centrale du haut du joueur.
            bullets_group.add(bullet)                # Ajoute la balle au groupe des projectiles (pour collisions/MAJ).
            all_sprites_group.add(bullet)            # Ajoute aussi à all_sprites (pour update/draw globaux).
            self.last_shot = pygame.time.get_ticks() # Met à jour l'heure du dernier tir.

class Game:                                          # Classe qui gère l'initialisation et la boucle de jeu.
    def __init__(self):                              # Constructeur du jeu.
        pygame.init()                                # Initialise tous les modules Pygame.
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Crée la fenêtre d'affichage.
        pygame.display.set_caption("Space Invaders - TD2")       # Titre de la fenêtre.
        self.clock = pygame.time.Clock()             # Horloge pour contrôler le FPS.

        self.all_sprites = pygame.sprite.Group()     # Groupe contenant tous les sprites à mettre à jour/afficher.
        self.bullets = pygame.sprite.Group()         # Groupe dédié aux projectiles (facilite la gestion/collisions).
        self.enemies = pygame.sprite.Group()         # Groupe des ennemis.

        self.player = Player(WIDTH//2, HEIGHT-30)    # Crée le joueur centré en bas (à 30 px du bas de l'écran).
        self.all_sprites.add(self.player)            # Ajoute le joueur au groupe global.

        # quelques ennemis immobiles pour test
        for i in range(8):                           # Boucle pour créer une rangée de 8 ennemis espacés.
            e = Enemy(60 + i*80, 80)                 # Positionne chaque ennemi en x = 60 + 80*i, y = 80.
            self.enemies.add(e)                      # Ajoute l'ennemi au groupe des ennemis.
            self.all_sprites.add(e)                  # Ajoute aussi à all_sprites pour être dessiné/mis à jour.

        self.running = True                          # Drapeau de la boucle principale (True => continuer à jouer).

    def run(self):                                   # Lance la boucle de jeu principale.
        while self.running:                          # Tant que le jeu tourne...
            self.clock.tick(FPS)                     # Cadence la boucle pour viser 60 FPS.
            self.handle_events()                     # Traite les événements (clavier, fermeture, etc.).
            self.update()                            # Met à jour la logique (déplacements, collisions...).
            self.draw()                              # Dessine la frame actuelle à l'écran.
        pygame.quit(); sys.exit()                    # Quitte proprement Pygame puis termine le programme.

    def handle_events(self):                         # Gestion des événements Pygame.
        for event in pygame.event.get():             # Parcourt tous les événements en file.
            if event.type == pygame.QUIT: self.running = False  # Si clic sur croix, on arrête le jeu.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:  # Si une touche vient d'être pressée et que c'est ESPACE...
                self.player.shoot(self.bullets, self.all_sprites)  # ...on déclenche un tir (si cooldown OK).

    def update(self):                                # Mise à jour de l'état de tous les objets du jeu.
        keys = pygame.key.get_pressed()              # Récupère l'état (pressée ou non) de toutes les touches.
        self.all_sprites.update(keys)                # Appelle update(keys) sur chaque sprite du groupe (Player l'utilise, Bullet/Enemy ignorent).
        # collisions bullet/enemy
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)  # Détecte collisions entre ennemis et balles ; supprime les deux en cas de contact.
        # (pour TD : afficher len(hits) dans la console)
        if hits:                                     # Si au moins une collision a eu lieu...
            print("touché :", len(hits))            # ...affiche le nombre d'ennemis touchés sur cette frame.

    def draw(self):                                  # Rendu graphique de la scène.
        self.screen.fill(BLACK)                      # Efface l'écran en le remplissant de noir.
        self.all_sprites.draw(self.screen)           # Dessine tous les sprites du groupe all_sprites.
        pygame.display.flip()                        # Bascule le buffer pour afficher l'image dessinée (double buffering).

if __name__ == "__main__":                           # Point d'entrée : n'exécuter que si le fichier est lancé directement.
    Game().run()                                     # Instancie le jeu et démarre la boucle principale.
