# Pygame – Mini Space Invaders

# 🎯 Modalités d’évaluation

- 🗓️ **Date limite de rendu** : **18/11/2025 à 00h00 (dernier délai)**  
- 📦 **Format attendu** : un **dossier compressé (.zip)** nommé **Prenom.Nom.zip**  
- 📧 **Envoi du projet** : le dossier `.zip` doit être envoyé **par mail** à l’adresse suivante :  
  👉 **louis.mougenot@edu.univ-fcomte.fr**
- 📁 **Contenu obligatoire du dossier** :
  1. Un **seul fichier Python** contenant le jeu complet et **commenté** de type prenomnom.py
  2. Un dossier **`assets/`** contenant **toutes les images** nécessaires au jeu
  3. Un **fichier de documentation** (format libre : `.md`, `.pdf` ou `.txt`) détaillant :
     - Le **prompt** utilisé pour demander de l’aide à l’IA  
     - Les **extraits de code** générés ou inspirés par l’IA  
     - Une **explication claire** de **comment** ces éléments ont été **intégrés et adaptés** dans le code final

> ⚠️ Le dossier doit être complet et exécutable tel quel.  
> L’absence d’un des éléments ou une structure différente entraînera une pénalité.

## 📂 Exemple de structure attendue

```bash
Prenom.Nom/
│
├── prenomnom.py                 # Fichier Python du jeu, complet et commenté
│
├── assets/                 # Dossier contenant toutes les images
│   ├── Fond.jpg
│   ├── PLayer.jpg
│   └── vaisseau.jpg
│
└── utilisation_IA.md       # Fichier expliquant l'usage de l'IA (prompt, code, intégration)
```

---

## 1) Rappels express sur Pygame

*Identique à ta version d’origine : Surfaces, Rect, Événements, Boucle de jeu, Sprites/Groupes, coordonnées, pipeline de rendu, double buffering, etc.*

---

## 2) Surfaces : ce que c’est *vraiment*

*Idem +* deux points pratiques utilisés dans le code **étendu** :

* `convert()` **sans** alpha pour accélérer les blits (adaptation au format d’affichage).
* `set_colorkey(WHITE)` pour rendre **transparent** un fond d’image uni (utile avec des JPEGs). Alternative : PNG + `convert_alpha()` pour une vraie transparence par pixel.

---

## 3) Rect : positions & collisions

*Idem*, avec rappel : on positionne via `image.get_rect(...)`, puis on modifie `rect.x/y` ou des alias (`left/right/top/bottom/center`). Les collisions AABB se font via les `Rect` **ou** via les helpers des **Groupes** (cf. §7.4).

---

## 4) Événements & entrées

Deux styles complémentaires :

1. **Événements discrets** (ex : appui ponctuel sur une touche pour *tirer*).
2. **État continu** (ex : flèches gauche/droite pour *déplacer* le joueur).

Dans le code étendu :

* Le tir est déclenché sur **KEYDOWN** de la touche **A** (`pygame.K_a`).
* Le déplacement latéral lit l’état du clavier dans `update(keys)` du joueur.

---

## 5) Boucle de jeu & timing

* `clock.tick(FPS)` pour limiter/mesurer la cadence.
* Si tu ajoutes de la physique/mouvements lissés : préfère un **timestep variable** `dt = clock.get_time()/1000.0` et exprime les vitesses en px/s.

---

## 6) Sprites & Groupes : architecture

Le code étendu introduit **trois types** de sprites :

* `Player` (le tireur)
* `Enemy` (les cibles)
* `Bullet` (les projectiles)

Et **trois groupes** dédiés :

* `all_sprites` : *tout ce qui s’affiche* (ordre de dessin géré par le groupe).
* `enemies` : pour tester les collisions avec les balles.
* `bullets` : pour mettre à jour/retirer les projectiles.

> Astuce perf : On **réutilise** la même `Surface` d’ennemi pour tous les `Enemy` (passée au constructeur). Si un ennemi doit être visuellement différent, fais un `.copy()` avant modification.

---

## 7) Lecture pas à pas du **code étendu**

### 7.1 Constantes & couleurs

```python
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (80, 220, 100)
RED   = (255, 0, 0)
```

* Ajout de **RED** au besoin (indicateurs, débogage, etc.).

### 7.2 `class Bullet(Sprite)` – projectiles ascendants

```python
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-8):
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed

    def update(self, *_):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()
```

* **Taille** simple (4×20), **couleur** blanche.
* **Vitesse négative** ⇒ la balle **monte** (coordonnée `y` diminue).
* Sortie du haut d’écran ⇒ `kill()` (retire du groupe → GC par Pygame).
* `update(self, *_)` accepte des args en plus (compat). Les groupes appellent `update(keys)` pour tous les sprites ; ceux qui n’utilisent pas `keys` peuvent l’ignorer.

### 7.3 `class Enemy(Sprite)` – cibles

```python
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface):
        super().__init__()
        self.image = image_surface  # réutilisée pour tous
        self.rect = self.image.get_rect(topleft=(x, y))
```

* Construction **rapide** à partir d’une `Surface` préparée.

### 7.4 `class Player(Sprite)` – tireur, déplacement & cooldown

```python
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=5):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed
        self.shoot_cooldown = 250  # ms
        self.last_shot = 0

    def update(self, keys):
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        # Clamping dans l’écran
        self.rect.left  = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown

    def shoot(self, bullets_group, all_sprites_group):
        if self.can_shoot():
            bullet = Bullet(self.rect.centerx, self.rect.top)
            bullets_group.add(bullet)
            all_sprites_group.add(bullet)
            self.last_shot = pygame.time.get_ticks()
```

* **Cooldown** (250 ms) géré via `pygame.time.get_ticks()` ⇒ empêche le *spam*.
* `shoot()` instancie une `Bullet`, l’ajoute aux groupes adéquats, et mémorise l’horodatage.

### 7.5 Chargement des **images** (fond, joueur, ennemi)

```python
# Fond
bg_raw = pygame.image.load("…/Fond.jpg").convert()   # pas d’alpha
background = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))

# Joueur (fond blanc rendu transparent)
player_raw = pygame.image.load("…/PLayer.jpg").convert()
player_raw.set_colorkey(WHITE)
player_img = pygame.transform.smoothscale(player_raw, (60, 60))

# Ennemi
enemy_raw = pygame.image.load("…/vaisseau.jpg").convert()
enemy_img = pygame.transform.smoothscale(enemy_raw, (40, 25))
```

* **`convert()`** : format d’affichage (perf), pas de canal alpha ⇒ parfait pour JPEG/fonds opaques.
* **Transparence** joueur : `set_colorkey(WHITE)` supprime le blanc *uniforme*. Pour un détourage plus propre, préfère un **PNG** + `convert_alpha()`.
* **Redimensionnement** avec `smoothscale` pour limiter l’aliasing.
* **Chemins** : privilégie des **chemins relatifs** + `os.path.join` pour la portabilité (Windows/macOS/Linux) et évite les chemins absolus spécifiques à une machine.

### 7.6 Initialisation des groupes & placement

```python
self.all_sprites = pygame.sprite.Group()
self.bullets    = pygame.sprite.Group()
self.enemies    = pygame.sprite.Group()

self.player = Player(WIDTH//2, HEIGHT-30, player_img)
self.all_sprites.add(self.player)

# Deux rangées d’ennemis, espacées régulièrement
for i in range(9):
    e = Enemy(60 + i*80, 80, enemy_img)
    h = Enemy(60 + i*80, 20, enemy_img)
    self.enemies.add(e, h)
    self.all_sprites.add(e, h)
```

* Simple **grille** d’ennemis (2 rangées × 9 colonnes).
* Tous les sprites sont **dessinés** par `all_sprites` (cf. §7.8).

### 7.7 Gestion des événements

```python
for event in pygame.event.get():
    if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
        self.player.shoot(self.bullets, self.all_sprites)
    if event.type == pygame.QUIT:
        self.running = False
```

* Le tir se fait sur **`K_a`**. Change facilement la touche (ex.: `K_SPACE`).
* `QUIT` met fin à la boucle proprement.

### 7.8 Update & **collisions** `Group` vs `Group`

```python
keys = pygame.key.get_pressed()
self.all_sprites.update(keys)

hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
if hits:
    print("touché :", len(hits))
```

* `update(keys)` est appelé **pour tous** les sprites ; seuls ceux qui utilisent `keys` s’en servent.
* `groupcollide(G1, G2, kill1, kill2)` supprime ici **l’ennemi** et la **balle** lors d’un impact (AABB par défaut).

  * Besoin d’une hitbox plus fine (cercle/masque) ? Regarde `collide_mask` avec des **mask** de pixels.

### 7.9 Dessin : **fond** puis sprites

```python
self.screen.blit(self.background, (0, 0))
self.all_sprites.draw(self.screen)
pygame.display.flip()
```

* Toujours dessiner le **fond en premier**, puis les **sprites** dans l’ordre du groupe.
* `flip()` présente la frame (double‑buffering SDL).

---


## 8) Check‑list débogage

* Fenêtre noire ? Vérifie l’ordre `blit(background)` **avant** `draw()` + `flip()`.
* Pas de transparence ? Confonds‑tu `convert()` (pas d’alpha) et `convert_alpha()` / `set_colorkey()` ?
* Balle immobile ? Signe de `speed` ou oubli de `add()` dans les groupes.
* Collisions muettes ? Vérifie que `enemies` et `bullets` contiennent bien des sprites actifs et que `groupcollide(..., True, True)` n’est pas inversé.

---

## 9) Code exécutable minimal (étendu)

> *Version compacte reprenant les points ci‑dessus, à adapter en chemins relatifs :*

```python
import pygame, sys
from pathlib import Path

WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (80,220,100)

ASSETS = Path(__file__).parent/"assets"

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-8):
        super().__init__()
        self.image = pygame.Surface((4,20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.speed = speed
    def update(self, *_):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(topleft=(x,y))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface, speed=5):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.speed = speed
        self.shoot_cooldown = 250
        self.last_shot = 0
    def update(self, keys):
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        self.rect.left  = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.shoot_cooldown
    def shoot(self, bullets_group, all_sprites_group):
        if self.can_shoot():
            b = Bullet(self.rect.centerx, self.rect.top)
            bullets_group.add(b); all_sprites_group.add(b)
            self.last_shot = pygame.time.get_ticks()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders (simple)")
        self.clock = pygame.time.Clock()

        self.all_sprites = pygame.sprite.Group()
        self.bullets    = pygame.sprite.Group()
        self.enemies    = pygame.sprite.Group()

        bg_raw = pygame.image.load(ASSETS/"Fond.jpg").convert()
        self.background = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))

        player_raw = pygame.image.load(ASSETS/"PLayer.jpg").convert()
        player_raw.set_colorkey(WHITE)
        self.player_img = pygame.transform.smoothscale(player_raw, (60,60))

        enemy_raw = pygame.image.load(ASSETS/"vaisseau.jpg").convert()
        self.enemy_img = pygame.transform.smoothscale(enemy_raw, (40,25))

        self.player = Player(WIDTH//2, HEIGHT-30, self.player_img)
        self.all_sprites.add(self.player)

        for i in range(9):
            e = Enemy(60+i*80, 80, self.enemy_img)
            h = Enemy(60+i*80, 20, self.enemy_img)
            self.enemies.add(e,h); self.all_sprites.add(e,h)

        self.running = True

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events(); self.update(); self.draw()
        pygame.quit(); sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                self.player.shoot(self.bullets, self.all_sprites)
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.all_sprites.update(keys)
        pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)

    def draw(self):
        self.screen.blit(self.background, (0,0))
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

if __name__ == "__main__":
    Game().run()
```

---
