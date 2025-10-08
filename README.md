# Pygame – Mini Space Invaders : Guide détaillé

> **Objectif** : comprendre *en profondeur* comment fonctionne Pygame (Surfaces, Rect, boucle de jeu, Sprites/Groupes, horloge, évènements), puis décortiquer pas à pas le code fourni, et savoir comment l’étendre proprement.

---

## 1) Rappels express sur Pygame

Pygame est un *wrapper* autour de **SDL** (Simple DirectMedia Layer). Il fournit :

* **Surfaces** : zones de pixels en mémoire (images, textures, écran). On *dessine* dessus et on les **blitte** (copie rapide de pixels) vers d’autres surfaces.
* **Rect** : rectangles utilitaires pour positionnement, tailles et **collisions**. Un `Rect` n’a pas de pixels ; c’est une boîte englobante attachée à une Surface via `surface.get_rect()`.
* **Événements** : clavier, souris, fermeture fenêtre, etc., mis en file par SDL et lus avec `pygame.event.get()`.
* **Boucle de jeu** : itération continue « *input → update → draw* » cadencée par `pygame.time.Clock()`.
* **Sprites / Groupes** : canevas OO pour gérer des objets de jeu (image + rect + `update()`). Les groupes savent `update()` et `draw()` *en lot*.

### Coordonnées & unités

* Origine **(0,0)** en **haut-gauche**. Axe **x** va à droite, **y** va vers le bas.
* Les positions et tailles sont en **pixels**.
* Le temps est géré en **ms** via l’horloge (`clock.tick(FPS)`, `get_time()`, `get_fps()`).

### Pipeline de rendu (simplifié)

1. **Effacer** l’écran (souvent `screen.fill(couleur)`).
2. **Dessiner** (blit) toutes les images sur `screen` dans le bon ordre.
3. **Présenter** à l’utilisateur : `pygame.display.flip()` (ou `update()`).

### Double buffering

* Pygame/SDL dessinent sur un **back buffer** puis l’échangent avec l’**écran**. D’où l’obligation d’effacer/redessiner **à chaque frame**.

---

## 2) Surfaces : ce que c’est *vraiment*

* Une **Surface** est un tableau de pixels + un *format* (profondeur couleur, canal alpha). Exemples : `pygame.Surface((w,h))`, `pygame.image.load(...)`.
* `convert()` / `convert_alpha()` :

  * `convert()` adapte le format de la surface au format d’affichage pour **accélérer** les blits (sans alpha).
  * `convert_alpha()` conserve l’**alpha** (transparence par pixel).
* **Alpha global** vs **alpha par pixel** :

  * Global : `surface.set_alpha(128)` → semi‑transparent partout.
  * Par pixel : image PNG avec canal alpha + `convert_alpha()`.

**Dans ton code** : le joueur est un cercle vert dessiné sur une Surface **avec alpha** (`pygame.SRCALPHA`).

---

## 3) Rect : boîte outil pour positions & collisions

* `Rect` stocke `(x, y, w, h)` et offre de **nombreux attributs** : `left/right/top/bottom/center`, etc., plus des méthodes (`move`, `inflate`, `colliderect`, `clamp_ip`, …).
* Un `Rect` **ne dessine rien**. Il sert à :

  * positionner la `Surface` associée (via `blit(image, rect)`) ;
  * tester des **collisions** (`rect.colliderect(autre_rect)`).

**Dans ton code** : `self.rect = self.image.get_rect(center=(x, y))`, puis on modifie `rect.x`, `rect.left/right` pour le mouvement et le *clamping*.

---

## 4) Événements, entrées et états de touches

Il existe deux façons complémentaires d’obtenir le clavier :

1. **Événements discrets** via la queue :

   ```python
   for event in pygame.event.get():
       if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
           tirer()
   ```

   Utile pour des actions **instantanées** (tir, pause, menu…).

2. **État continu** du clavier via `pygame.key.get_pressed()`: tableau booléen indexé par les **scancodes**.

   ```python
   keys = pygame.key.get_pressed()
   if keys[pygame.K_LEFT]: rect.x -= speed
   ```

   Parfait pour des **mouvements continus**.

**Dans ton code** : `handle_events()` lit les événements (fermeture). `update()` lit l’état du clavier pour déplacer le joueur.

---

## 5) Boucle de jeu & timing (fixe vs variable)

* `clock.tick(FPS)` limite la vitesse de la boucle et retourne le **delta temps** écoulé *depuis la frame précédente* (en ms via `clock.get_time()`).
* Deux approches :

  * **Timestep fixe** (comme ici) : on suppose ~`1/FPS` constant. Simple mais la vitesse dépend un peu de la machine. OK pour jeux simples.
  * **Timestep variable** : on multiplie tous les déplacements par `dt` (en secondes). Plus robuste : `position += vitesse * dt`.

**Conseil** : si tu rajoutes de la physique, utilise `dt = clock.get_time() / 1000.0` et rends tes vitesses en *pixels/seconde*.

---

## 6) Sprites & Groupes : architecture orientée objets

* **Sprite** = classe dérivante de `pygame.sprite.Sprite` avec typiquement `self.image` + `self.rect` + `update()`.
* **Group** = conteneur qui sait **mettre à jour** et **dessiner** tous ses sprites :

  ```python
  all_sprites = pygame.sprite.Group()
  all_sprites.add(player, enemy, bullet)
  all_sprites.update(args)
  all_sprites.draw(screen)
  ```
* **Collisions** :

  * `pygame.sprite.spritecollide(sprite, group, dokill=False, collided=None)`
  * `pygame.sprite.groupcollide(group1, group2, dokill1, dokill2, collided=None)`

**Dans ton code** : `Player` est un Sprite minimal ; `Game` crée `all_sprites` et appelle `update/draw` dessus.

---

## 7) Lecture pas à pas de ton code

### 7.1 Constantes et couleurs

* `WIDTH, HEIGHT = 800, 600`, `FPS = 60` : taille fenêtre, cadence visée.
* Couleurs RGB : `WHITE`, `BLACK`, `GREEN`.

### 7.2 `class Player(Sprite)`

* Crée une **Surface alpha** de diamètre `2*radius`.
* Dessine un **cercle** vert : `pygame.draw.circle(self.image, GREEN, (radius, radius), radius)`.
* Construit `self.rect` centré en `(x, y)` et stocke `speed`.
* `update(keys)` :

  * déplace `rect.x` selon `K_LEFT` / `K_RIGHT` ;
  * **clamp** dans l’écran via `rect.left/right`.

### 7.3 `class Game`

* `__init__` :

  * `pygame.init()` → initialise tous les sous‑modules ;
  * `set_mode((WIDTH, HEIGHT))` → crée la fenêtre ;
  * `Clock()` → horloge ;
  * `Group()` → `all_sprites` ;
  * crée le **joueur** et l’ajoute au groupe ;
  * `self.running = True` pour la boucle.
* `run()` (la boucle) :

  1. `clock.tick(FPS)`
  2. `handle_events()` → lit la queue (quitter)
  3. `update()` → lit l’état du clavier + `all_sprites.update(keys)`
  4. `draw()` → `fill(BLACK)` + `all_sprites.draw(screen)` + `display.flip()`
  5. **Sortie propre** : `pygame.quit()` puis `sys.exit()`

---


