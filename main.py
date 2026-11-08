import pygame # type: ignore
import random
import math
from pygame import mixer # type: ignore

# --- INICIALIZACIÓN ---
pygame.init()
pygame.font.init()
mixer.init()

ANCHO, ALTO = 800, 600
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Fast Run - El Refugio Final")
reloj = pygame.time.Clock()
Vec = pygame.math.Vector2

# --- CARGA DE ASSETS (Imágenes y Respaldo) ---
def cargar_imagen(nombre_archivo, ancho, alto, color_fallback=(0, 255, 0)):
    try:
        img = pygame.image.load(nombre_archivo).convert_alpha()
        return pygame.transform.scale(img, (ancho, alto))
    except Exception as e:
        print(f"⚠️ AVISO: No se pudo cargar '{nombre_archivo}'. Usando respaldo. Detalle: {e}")
        surf = pygame.Surface((ancho, alto), pygame.SRCALPHA)  # SRCALPHA para poder rotarla sin bordes negros
        surf.fill(color_fallback)
        return surf

def cargar_sonido(nombre_archivo, volumen=0.5):
    try:
        sonido = mixer.Sound(nombre_archivo)
        sonido.set_volume(volumen)
        return sonido
    except Exception as e:
        print(f"⚠️ AVISO: No se pudo cargar el sonido '{nombre_archivo}'. Detalle: {e}")
        return None

# Carga de Portada y Sprites principales
fondo_portada = cargar_imagen("FondoPortada.jpg", ANCHO, ALTO, (20, 20, 40))
img_jugador = cargar_imagen("jugador.png", 40, 50, (0, 200, 255))
img_enemigo = cargar_imagen("disparador_enemigo.png", 45, 45, (255, 50, 50))
BOSS_W, BOSS_H = 160, 200   # Tamaño del villano final (antes 70 x 90)
img_boss = cargar_imagen("boss.png", BOSS_W, BOSS_H, (180, 0, 0)) # Villano final
img_bala_enemiga = cargar_imagen("bala_enemigo.png", 10, 10, (255, 255, 0))
img_item_arma = cargar_imagen("arma_pickup.png", 30, 30, (0, 255, 100))
img_bala_jugador = cargar_imagen("bala_jugador.png", 12, 12, (0, 255, 255))

# --- CARGA DEL CASTILLO / REFUGIO CON TRANSPARENCIA AUTOMÁTICA ---
try:
    img_refugio = pygame.image.load("refugio.png").convert_alpha()
    img_refugio = pygame.transform.scale(img_refugio, (280, 180))
    for x in range(img_refugio.get_width()):
        for y in range(img_refugio.get_height()):
            c = img_refugio.get_at((x, y))
            if abs(c.r - c.g) < 10 and abs(c.g - c.b) < 10 and c.r > 110:
                img_refugio.set_at((x, y), (0, 0, 0, 0))
except:
    img_refugio = pygame.Surface((280, 180))
    img_refugio.fill((0, 255, 150))

# --- CARGA DE FONDOS PROGRESIVOS (Usando .jpeg) ---
fondos_niveles = []
for i in range(1, 4):
    imagen_fondo = cargar_imagen(f"fondo{i}.jpeg", ANCHO, ALTO, (30, 30, 50))
    fondos_niveles.append(imagen_fondo)

fondo_actual = fondos_niveles[0]

# --- GESTIÓN DE MÚSICA Y SONIDOS ---
try:
    mixer.music.load("MusicaFondo.mp3")
    mixer.music.set_volume(0.6)
    mixer.music.play(-1)
except:
    pass

sonido_disparo_jugador = cargar_sonido("sonidobalajugador.mp3", 0.7)
sonido_disparo_enemigo = cargar_sonido("sonidobalaenemigo.mp3", 0.4)
sonido_recarga = cargar_sonido("sonidorecarga.mp3", 0.8)
sonido_derrota = cargar_sonido("youloss.mp3", 0.9)
sonido_victoria = cargar_sonido("youwin.mp3", 0.9)

def iniciar_musica():
    try:
        mixer.music.play(-1)
    except Exception:
        pass

# Fuentes
fuente_titulo = pygame.font.SysFont("Arial", 64, bold=True)
fuente_ui = pygame.font.SysFont("Arial", 24, bold=True)

# =====================================================================
#   ANIMACIÓN DEL JUGADOR (se genera automáticamente desde jugador.png)
# =====================================================================
# Si tu sprite mira hacia la IZQUIERDA en el PNG, cambia esto a -1
SPRITE_MIRA = 1

JUG_W, JUG_H = img_jugador.get_size()   # 40 x 50
CADERA_Y = int(JUG_H * 0.58)            # Altura donde se "parte" el sprite: arriba torso, abajo piernas
HOMBRO_Y = 22                           # Altura del hombro (de donde sale el brazo con el arma)
MARGEN_X, MARGEN_ARR, MARGEN_ABA = 10, 6, 4
N_FRAMES = 8

def rotar_pivote(surf, angulo, pivote, pos):
    """Rota 'surf' alrededor de 'pivote' (coords locales) y deja ese pivote en 'pos'."""
    rotada = pygame.transform.rotate(surf, angulo)
    offset = Vec(pivote) - Vec(surf.get_rect().center)
    offset_rot = offset.rotate(-angulo)
    centro = Vec(pos) - offset_rot
    return rotada, rotada.get_rect(center=(round(centro.x), round(centro.y)))

def generar_frame_jugador(ang_pierna, lift_izq, lift_der, bob, balanceo):
    """Crea un cuadro de animación: torso con leve balanceo + dos piernas que giran desde la cadera."""
    lienzo = pygame.Surface((JUG_W + 2 * MARGEN_X, JUG_H + MARGEN_ARR + MARGEN_ABA), pygame.SRCALPHA)
    bob = round(bob)
    cadera_y = MARGEN_ARR + CADERA_Y + bob
    mitad = JUG_W // 2
    alto_pierna = JUG_H - CADERA_Y

    pierna_izq = img_jugador.subsurface((0, CADERA_Y, mitad, alto_pierna)).copy()
    pierna_der = img_jugador.subsurface((mitad, CADERA_Y, JUG_W - mitad, alto_pierna)).copy()

    for pierna, ang, lift, cx in ((pierna_izq, ang_pierna, lift_izq, MARGEN_X + mitad // 2),
                                  (pierna_der, -ang_pierna, lift_der, MARGEN_X + mitad + (JUG_W - mitad) // 2)):
        rot, rect = rotar_pivote(pierna, ang, (pierna.get_width() / 2, 0), (cx, cadera_y - lift))
        lienzo.blit(rot, rect)

    torso = img_jugador.subsurface((0, 0, JUG_W, CADERA_Y)).copy()
    rot, rect = rotar_pivote(torso, balanceo, (JUG_W / 2, CADERA_Y), (MARGEN_X + JUG_W / 2, cadera_y))
    lienzo.blit(rot, rect)
    return lienzo

def crear_ciclo(amplitud, lift, rebote):
    frames = []
    for i in range(N_FRAMES):
        fi = 2 * math.pi * i / N_FRAMES
        s = math.sin(fi)
        frames.append(generar_frame_jugador(
            ang_pierna=amplitud * s,
            lift_izq=lift * max(0, math.cos(fi)),
            lift_der=lift * max(0, -math.cos(fi)),
            bob=-(1 - abs(s)) * rebote,
            balanceo=2.5 * s))
    return frames

def rebote_frame(i, rebote):
    return round(-(1 - abs(math.sin(2 * math.pi * i / N_FRAMES))) * rebote)

REBOTE_CAMINAR, REBOTE_CORRER = 2, 3
frames_caminar = crear_ciclo(24, 3, REBOTE_CAMINAR)
frames_correr = crear_ciclo(36, 5, REBOTE_CORRER)
frame_quieto = generar_frame_jugador(0, 0, 0, 0, 0)
frame_salto = generar_frame_jugador(20, 4, 4, 0, 0)
BASE_Y_LIENZO = JUG_H + MARGEN_ARR   # Donde están los pies dentro del lienzo

def color_promedio(img, rect, defecto=(60, 60, 70)):
    r = g = b = n = 0
    for px in range(rect.left, rect.right):
        for py in range(rect.top, rect.bottom):
            c = img.get_at((px, py))
            if c.a > 128:
                r += c.r; g += c.g; b += c.b; n += 1
    if n == 0:
        return defecto
    return (int(r / n * 0.85), int(g / n * 0.85), int(b / n * 0.85))

# El brazo toma el color de la ropa del propio sprite, así combina con tu personaje
color_brazo = color_promedio(img_jugador, pygame.Rect(8, max(0, CADERA_Y - 12), JUG_W - 16, 12))
color_piel = (235, 190, 150)

# --- ARMA EN LA MANO DEL JUGADOR ---
def crear_arma_procedural():
    """Pistola dibujada por código (se usa si no existe 'arma_jugador.png')."""
    s = pygame.Surface((34, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, (85, 85, 95), (24, 5, 10, 4))               # cañón
    pygame.draw.rect(s, (45, 45, 52), (4, 3, 22, 8), border_radius=2)  # cuerpo
    pygame.draw.line(s, (120, 120, 130), (6, 4), (24, 4), 1)        # brillo
    pygame.draw.polygon(s, (95, 62, 40), [(5, 10), (12, 10), (10, 13), (4, 13)])  # empuñadura
    pygame.draw.rect(s, (200, 200, 210), (31, 3, 2, 2))             # mira
    return s

try:
    # Opcional: pon un "arma_jugador.png" apuntando hacia la DERECHA; el agarre debe quedar cerca del lado izquierdo
    img_arma = pygame.transform.smoothscale(pygame.image.load("arma_jugador.png").convert_alpha(), (36, 16))
except Exception:
    img_arma = crear_arma_procedural()

ARMA_W, ARMA_H = img_arma.get_size()
ARMA_PIVOTE = (8, ARMA_H // 2)             # Punto de la mano sobre el arma
ARMA_LARGO = ARMA_W - ARMA_PIVOTE[0]       # Distancia de la mano a la boca del cañón
ARMA_DIST_MANO = 10                        # Distancia del hombro a la mano

# --- ESTADOS DEL JUEGO ---
ESTADO_PORTADA = 0
ESTADO_JUGANDO = 1
ESTADO_BOSS = 2
ESTADO_VICTORIA = 3
ESTADO_DERROTA = 4
estado_actual = ESTADO_PORTADA

# --- VARIABLES DEL JUEGO ---
nivel_actual = 1
max_niveles = 3

SUELO_Y = 500
jugador_x = 100
jugador_y = SUELO_Y
jugador_vy = 0
gravedad = 0.8
fuerza_salto = -14
en_suelo = True

camara_x = 0
velocidad_base = 4
velocidad_run = 7.5
vida_jugador = 100

# Sistema de Munición y Arma
tiene_arma = False          # El jugador empieza sin arma; la consigue al recoger el primer pickup
municion_balas = 0
VEL_BALA_JUGADOR = 12
CADENCIA_JUGADOR = 10       # Frames entre disparos al mantener el click (60 fps -> 6 disparos/seg)
cooldown_disparo = 0

# Estado de animación del jugador
dir_mirada = 1              # 1 = derecha, -1 = izquierda
anim_fase = 0.0
moviendo = False
corriendo = False
bob_actual = 0              # Rebote vertical del cuerpo (lo usa el arma para seguir al hombro)
aplastar = 0                # Frames de "squash" al aterrizar
retroceso = 0.0             # Retroceso del arma al disparar
flash_timer = 0             # Destello del cañón
flash_dano = 0              # Pantalla roja al recibir daño
tiempo = 0                  # Contador global de frames
mensaje_texto = ""
mensaje_timer = 0

# Variables del Jefe Final
boss_x = 0
boss_y = SUELO_Y + 50 - BOSS_H   # Los pies del jefe quedan a la altura de los pies del jugador
boss_vida = 200
boss_vida_max = 200
boss_cooldown = 0
jugador_derrotado = False
snapshot_derrota = None

# Listas del nivel
balas_jugador = []
enemigos = []
balas_enemigas = []
items_arma = []
particulas = []
longitud_mapa = 6000
refugio_x = longitud_mapa - 350

overlay_dano = pygame.Surface((ANCHO, ALTO))
overlay_dano.fill((255, 0, 0))

# =====================================================================
#   UTILIDADES: partículas, mensajes, balas
# =====================================================================
def crear_particulas(x, y, n, color, vel=3.0, vida=25, radio=3, grav=0.15, arriba=False):
    for _ in range(n):
        ang = random.uniform(0, 2 * math.pi)
        v = random.uniform(0.3, 1.0) * vel
        vy = math.sin(ang) * v
        if arriba:
            vy = -abs(vy)
        particulas.append({'x': x, 'y': y, 'vx': math.cos(ang) * v, 'vy': vy,
                           'vida': random.randint(max(1, vida // 2), vida), 'max': vida,
                           'color': color, 'r': radio, 'g': grav})

def actualizar_particulas():
    for p in particulas[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += p['g']
        p['vida'] -= 1
        if p['vida'] <= 0:
            particulas.remove(p)

def dibujar_particulas():
    for p in particulas:
        r = max(1, int(p['r'] * p['vida'] / p['max']))
        pygame.draw.circle(pantalla, p['color'], (int(p['x'] - camara_x), int(p['y'])), r)

def mostrar_mensaje(texto, frames=150):
    global mensaje_texto, mensaje_timer
    mensaje_texto = texto
    mensaje_timer = frames

def rotar_bala(img, vx, vy):
    """Gira la imagen de la bala para que apunte hacia donde viaja (asume que mira a la derecha)."""
    return pygame.transform.rotate(img, -math.degrees(math.atan2(vy, vx)))

def dibujar_bala(b, color_estela):
    x, y = b['x'] - camara_x, b['y']
    pygame.draw.line(pantalla, color_estela, (x - b['vx'] * 3, y - b['vy'] * 3), (x, y), 2)
    img = b['img']
    pantalla.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)))

def enemigo_centro(e):
    """Centro real del enemigo (incluye su flotación), usado para dibujar y para colisiones."""
    flote = math.sin(tiempo * 0.05 + e['x'] * 0.01) * 4
    return e['x'] + img_enemigo.get_width() / 2, e['y'] + img_enemigo.get_height() / 2 + flote

def herir_jugador(dano):
    global vida_jugador, flash_dano
    vida_jugador -= dano
    flash_dano = 10
    crear_particulas(jugador_x + JUG_W / 2, jugador_y + JUG_H / 2, 8, (200, 30, 30), vel=3, vida=20)

# =====================================================================
#   APUNTADO Y DISPARO CON EL MOUSE
# =====================================================================
def estado_apuntado():
    """Devuelve (hombro en pantalla, dirección normalizada hacia el mouse, ángulo en grados para rotar)."""
    hombro = Vec(jugador_x - camara_x + JUG_W / 2, jugador_y + HOMBRO_Y + bob_actual)
    mx, my = pygame.mouse.get_pos()
    d = Vec(mx, my) - hombro
    if d.length() < 1:
        d = Vec(dir_mirada, 0)
    direc = d.normalize()
    return hombro, direc, -math.degrees(math.atan2(d.y, d.x))

def disparar():
    global municion_balas, cooldown_disparo, retroceso, flash_timer
    if not tiene_arma or municion_balas <= 0 or cooldown_disparo > 0:
        return
    hombro, direc, _ = estado_apuntado()
    punta = hombro + direc * (ARMA_DIST_MANO + ARMA_LARGO)   # La bala sale de la boca del cañón
    vx, vy = direc.x * VEL_BALA_JUGADOR, direc.y * VEL_BALA_JUGADOR
    balas_jugador.append({'x': punta.x + camara_x, 'y': punta.y, 'vx': vx, 'vy': vy,
                          'img': rotar_bala(img_bala_jugador, vx, vy)})
    municion_balas -= 1
    cooldown_disparo = CADENCIA_JUGADOR
    retroceso = 5.0
    flash_timer = 3
    # Chispas y casquillo expulsado
    crear_particulas(punta.x + camara_x, punta.y, 4, (255, 220, 100), vel=3, vida=10, radio=2, grav=0)
    particulas.append({'x': hombro.x + camara_x, 'y': hombro.y, 'vx': -direc.x * 1.5 + random.uniform(-0.5, 0.5),
                       'vy': -2.5, 'vida': 35, 'max': 35, 'color': (220, 180, 60), 'r': 2, 'g': 0.3})
    if sonido_disparo_jugador:
        sonido_disparo_jugador.play()

# =====================================================================
#   MOVIMIENTO, FÍSICA Y ANIMACIÓN
# =====================================================================
def mover_jugador(velocidad, x_min, x_max):
    global jugador_x
    teclas = pygame.key.get_pressed()
    dx = 0
    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
        dx -= velocidad
    if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
        dx += velocidad
    x_antes = jugador_x
    jugador_x = max(x_min, min(jugador_x + dx, x_max))
    return jugador_x - x_antes   # Movimiento real (0 si choca con el borde)

def aplicar_fisica_salto():
    global jugador_y, jugador_vy, en_suelo, aplastar
    vy_previa = jugador_vy
    jugador_vy += gravedad
    jugador_y += jugador_vy
    if jugador_y >= SUELO_Y:
        if not en_suelo and vy_previa > 6:       # Aterrizaje con impacto
            aplastar = 7
            for lado in (-1, 1):
                crear_particulas(jugador_x + JUG_W / 2 + lado * 10, SUELO_Y + JUG_H - 2, 3,
                                 (160, 150, 130), vel=1.5, vida=18, radio=3, grav=-0.02, arriba=True)
        jugador_y = SUELO_Y
        jugador_vy = 0
        en_suelo = True

def actualizar_animacion(dx, corre):
    """Avanza el ciclo de caminata y decide hacia dónde mira el jugador."""
    global anim_fase, moviendo, corriendo, dir_mirada, bob_actual
    moviendo = dx != 0
    corriendo = corre and moviendo

    # Con arma, el cuerpo mira hacia donde apunta el mouse; sin arma, hacia donde camina
    if tiene_arma:
        mx, _ = pygame.mouse.get_pos()
        centro = jugador_x - camara_x + JUG_W / 2
        if abs(mx - centro) > 3:
            dir_mirada = 1 if mx > centro else -1
    elif moviendo:
        dir_mirada = 1 if dx > 0 else -1

    if moviendo:
        # Si camina hacia atrás (apuntando al lado contrario) la animación se reproduce al revés
        sentido = 1 if dx * dir_mirada > 0 else -1
        anim_fase = (anim_fase + sentido * (0.32 if corriendo else 0.2)) % N_FRAMES
        if en_suelo and tiempo % (6 if corriendo else 14) == 0:
            crear_particulas(jugador_x + JUG_W / 2 - dir_mirada * 8, SUELO_Y + JUG_H - 2, 1,
                             (160, 150, 130), vel=1.0, vida=16, radio=3, grav=-0.02, arriba=True)

    if not en_suelo:
        bob_actual = 0
    elif moviendo:
        bob_actual = rebote_frame(int(anim_fase) % N_FRAMES, REBOTE_CORRER if corriendo else REBOTE_CAMINAR)
    else:
        bob_actual = round(math.sin(tiempo * 0.08))   # Respiración

def actualizar_efectos():
    global cooldown_disparo, retroceso, flash_timer, aplastar, flash_dano, mensaje_timer
    cooldown_disparo = max(0, cooldown_disparo - 1)
    retroceso = max(0.0, retroceso - 0.7)
    flash_timer = max(0, flash_timer - 1)
    aplastar = max(0, aplastar - 1)
    flash_dano = max(0, flash_dano - 1)
    mensaje_timer = max(0, mensaje_timer - 1)
    actualizar_particulas()

def dibujar_jugador():
    sx = jugador_x - camara_x
    pies_x = sx + JUG_W / 2
    pies_y = jugador_y + JUG_H

    # Sombra en el suelo (se hace más pequeña al saltar)
    altura = max(0, SUELO_Y - jugador_y)
    w_sombra = max(14, int(36 - altura * 0.12))
    sombra = pygame.Surface((w_sombra, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 90), sombra.get_rect())
    pantalla.blit(sombra, (pies_x - w_sombra / 2, SUELO_Y + JUG_H - 6))

    # Cuadro de animación según lo que esté haciendo
    if not en_suelo:
        frame = frame_salto
    elif moviendo:
        frame = (frames_correr if corriendo else frames_caminar)[int(anim_fase) % N_FRAMES]
    else:
        frame = frame_quieto

    # Squash & stretch: se estira al subir/caer y se aplasta al aterrizar
    fx, fy = 1.0, 1.0
    if aplastar > 0:
        fx, fy = 1.0 + 0.02 * aplastar, 1.0 - 0.02 * aplastar
    elif not en_suelo:
        if jugador_vy < -3:
            fx, fy = 0.94, 1.08
        elif jugador_vy > 4:
            fx, fy = 0.96, 1.05

    if dir_mirada != SPRITE_MIRA:
        frame = pygame.transform.flip(frame, True, False)
    if fx != 1.0 or fy != 1.0:
        frame = pygame.transform.scale(frame, (int(frame.get_width() * fx), int(frame.get_height() * fy)))
    base = BASE_Y_LIENZO * fy
    pantalla.blit(frame, (pies_x - frame.get_width() / 2, pies_y - base))

    if tiene_arma:
        dibujar_arma()

def dibujar_arma():
    """Dibuja brazo + arma rotando hacia el mouse, con retroceso y destello al disparar."""
    hombro, direc, ang = estado_apuntado()
    mano = hombro + direc * (ARMA_DIST_MANO - retroceso)

    pygame.draw.line(pantalla, color_brazo, hombro, mano, 5)
    pygame.draw.circle(pantalla, color_brazo, (int(hombro.x), int(hombro.y)), 3)

    arma = img_arma
    if direc.x < 0:   # Al apuntar a la izquierda se voltea para que no quede "de cabeza"
        arma = pygame.transform.flip(img_arma, False, True)
    rotada, rect = rotar_pivote(arma, ang, ARMA_PIVOTE, mano)
    pantalla.blit(rotada, rect)
    pygame.draw.circle(pantalla, color_piel, (int(mano.x), int(mano.y)), 3)

    if flash_timer > 0:
        punta = mano + direc * ARMA_LARGO
        perp = Vec(-direc.y, direc.x)
        largo = random.uniform(12, 20)
        pygame.draw.polygon(pantalla, (255, 210, 80), [punta + perp * 5, punta + direc * largo, punta - perp * 5])
        pygame.draw.polygon(pantalla, (255, 255, 230), [punta + perp * 2.5, punta + direc * (largo * 0.6), punta - perp * 2.5])

def dibujar_mira():
    """Mira personalizada que sigue al mouse (se abre un poco al disparar)."""
    mx, my = pygame.mouse.get_pos()
    if tiene_arma:
        color = (255, 255, 255) if municion_balas > 0 else (255, 90, 90)
    else:
        color = (150, 150, 150)
    gap = 6 + int(retroceso * 2)
    pygame.draw.circle(pantalla, color, (mx, my), gap + 4, 1)
    for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(pantalla, color, (mx + ux * gap, my + uy * gap), (mx + ux * (gap + 7), my + uy * (gap + 7)), 2)
    pygame.draw.circle(pantalla, color, (mx, my), 1)

# =====================================================================
#   NIVELES
# =====================================================================
def resetear_checkpoint():
    """Reaparece al jugador en el inicio del nivel actual con vida llena."""
    global jugador_x, jugador_y, jugador_vy, vida_jugador, municion_balas, balas_enemigas, camara_x, en_suelo
    jugador_x = 100
    camara_x = 0
    jugador_y = SUELO_Y
    jugador_vy = 0
    en_suelo = True
    vida_jugador = 100
    municion_balas = 15 if tiene_arma else 0
    balas_enemigas.clear()
    balas_jugador.clear()
    particulas.clear()

def iniciar_nivel(nivel):
    """Configura el mapa y la dificultad extrema según el nivel."""
    global nivel_actual, longitud_mapa, refugio_x, enemigos, items_arma, fondo_actual
    nivel_actual = nivel

    fondo_actual = fondos_niveles[nivel_actual - 1]
    longitud_mapa = 5500 + (nivel * 1500)
    refugio_x = longitud_mapa - 350

    resetear_checkpoint()
    enemigos.clear()
    items_arma.clear()

    # Cantidad de enemigos según el nivel
    cant_enemigos = 15 + (nivel * 8)
    distribucion = (refugio_x - 400) / cant_enemigos

    for i in range(cant_enemigos):
        pos_x = int(400 + (i * distribucion) + random.randint(-40, 40))
        enemigos.append({
            'x': pos_x,
            'y': random.randint(30, 95),
            'cooldown': random.randint(0, 60)
        })

    # El primer arma queda cerca del inicio para que el jugador la encuentre enseguida
    if not tiene_arma:
        items_arma.append({'x': 330, 'y': SUELO_Y + 15, 'activo': True})

    # Colocar armas/munición en el camino
    for _ in range(6):
        items_arma.append({
            'x': random.randint(600, refugio_x - 400),
            'y': SUELO_Y + 15,
            'activo': True
        })

def iniciar_boss_final():
    """Prepara el escenario de combate contra el villano final."""
    global estado_actual, jugador_x, jugador_y, jugador_vy, en_suelo, camara_x, boss_x, boss_y, boss_vida
    global balas_enemigas, balas_jugador, municion_balas, tiene_arma, boss_cooldown, flash_dano, jugador_derrotado
    estado_actual = ESTADO_BOSS
    tiene_arma = True
    jugador_x = 200
    jugador_y = SUELO_Y
    jugador_vy = 0
    en_suelo = True
    camara_x = 0
    boss_x = 640
    boss_y = SUELO_Y + 50 - BOSS_H
    boss_cooldown = 0
    flash_dano = 0
    jugador_derrotado = False
    boss_vida = 200
    municion_balas = 50 # Munición generosa para la pelea final
    balas_enemigas.clear()
    balas_jugador.clear()
    particulas.clear()

# --- UI Y PORTADA ---
def dibujar_portada():
    if fondo_portada:
        pantalla.blit(fondo_portada, (0, 0))
    else:
        pantalla.fill((15, 15, 30))

    txt_titulo = fuente_titulo.render("FAST RUN", True, (255, 215, 0))
    pantalla.blit(txt_titulo, (ANCHO // 2 - txt_titulo.get_width() // 2, 80))

    rect_boton = pygame.Rect(ANCHO // 2 - 100, 420, 200, 60)
    pos_mouse = pygame.mouse.get_pos()
    color_boton = (0, 200, 100) if rect_boton.collidepoint(pos_mouse) else (0, 150, 70)
    pygame.draw.rect(pantalla, color_boton, rect_boton, border_radius=10)

    txt_empezar = fuente_ui.render("EMPEZAR", True, (255, 255, 255))
    pantalla.blit(txt_empezar, (rect_boton.x + (200 - txt_empezar.get_width()) // 2, rect_boton.y + 18))
    return rect_boton

def dibujar_hud():
    # Barra de vida del jugador
    pygame.draw.rect(pantalla, (100, 0, 0), (20, 20, 200, 20))
    pygame.draw.rect(pantalla, (0, 255, 0), (20, 20, max(0, vida_jugador * 2), 20))
    pygame.draw.rect(pantalla, (255, 255, 255), (20, 20, 200, 20), 2)

    txt_vida = fuente_ui.render(f"Vida: {max(0, vida_jugador)}/100", True, (255, 255, 255))
    pantalla.blit(txt_vida, (230, 18))

    if estado_actual == ESTADO_JUGANDO:
        txt_lvl = fuente_ui.render(f"Nivel: {nivel_actual}/{max_niveles}", True, (255, 255, 0))
        pantalla.blit(txt_lvl, (ANCHO - 150, 18))

        porcentaje = int((jugador_x / refugio_x) * 100)
        txt_progreso = fuente_ui.render(f"Meta: {min(100, porcentaje)}%", True, (200, 255, 200))
        pantalla.blit(txt_progreso, (ANCHO - 160, 45))
    elif estado_actual == ESTADO_BOSS:
        txt_jefe = fuente_ui.render("¡BATALLA FINAL CONTRA EL VILLANO!", True, (255, 50, 50))
        pantalla.blit(txt_jefe, (ANCHO // 2 - txt_jefe.get_width() // 2, 108))

        # Barra de vida del Jefe
        pygame.draw.rect(pantalla, (80, 0, 0), (ANCHO // 2 - 150, 50, 300, 25))
        ancho_barra_boss = max(0, int((boss_vida / boss_vida_max) * 300))
        pygame.draw.rect(pantalla, (255, 0, 0), (ANCHO // 2 - 150, 50, ancho_barra_boss, 25))
        pygame.draw.rect(pantalla, (255, 255, 255), (ANCHO // 2 - 150, 50, 300, 25), 2)
        txt_vb = fuente_ui.render(f"Villano: {boss_vida}/{boss_vida_max}", True, (255, 255, 255))
        pantalla.blit(txt_vb, (ANCHO // 2 - txt_vb.get_width() // 2 - 3, 77))

    # Indicador de Munición
    if tiene_arma:
        color_municion = (0, 255, 255) if municion_balas > 0 else (255, 80, 80)
        txt_arma = fuente_ui.render(f"Balas: {municion_balas}", True, color_municion)
    else:
        txt_arma = fuente_ui.render("Sin arma", True, (170, 170, 170))
    pantalla.blit(txt_arma, (20, 45))

    # Mensajes temporales (arma recogida, etc.)
    if mensaje_timer > 0:
        txt = fuente_ui.render(mensaje_texto, True, (255, 255, 255))
        txt.set_alpha(min(255, mensaje_timer * 10))
        pantalla.blit(txt, (ANCHO // 2 - txt.get_width() // 2, 110))

def botones_derrota():
    return (pygame.Rect(ANCHO // 2 - 130, 340, 260, 55),   # Repetir
            pygame.Rect(ANCHO // 2 - 130, 415, 260, 55))   # Menú principal

def dibujar_derrota():
    if snapshot_derrota:
        pantalla.blit(snapshot_derrota, (0, 0))
    oscuro = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    oscuro.fill((0, 0, 0, 175))
    pantalla.blit(oscuro, (0, 0))

    txt = fuente_titulo.render("¡HAS PERDIDO!", True, (255, 70, 70))
    pantalla.blit(txt, (ANCHO // 2 - txt.get_width() // 2, 200))

    pos = pygame.mouse.get_pos()
    rep_rect, menu_rect = botones_derrota()
    for rect, texto, normal, resaltado in ((rep_rect, "REPETIR", (0, 150, 70), (0, 200, 100)),
                                           (menu_rect, "MENÚ PRINCIPAL", (150, 60, 40), (200, 80, 55))):
        pygame.draw.rect(pantalla, resaltado if rect.collidepoint(pos) else normal, rect, border_radius=10)
        t = fuente_ui.render(texto, True, (255, 255, 255))
        pantalla.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

def dibujar_efecto_dano():
    if flash_dano > 0:
        overlay_dano.set_alpha(flash_dano * 9)
        pantalla.blit(overlay_dano, (0, 0))

# --- BUCLE PRINCIPAL ---
ejecutando = True
while ejecutando:
    reloj.tick(60)
    tiempo += 1

    # El cursor del sistema se oculta durante el juego (se usa la mira personalizada)
    pygame.mouse.set_visible(estado_actual not in (ESTADO_JUGANDO, ESTADO_BOSS))

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

        if estado_actual == ESTADO_PORTADA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                rect_btn = pygame.Rect(ANCHO // 2 - 100, 420, 200, 60)
                if rect_btn.collidepoint(evento.pos):
                    tiene_arma = False
                    iniciar_nivel(1)
                    estado_actual = ESTADO_JUGANDO

        elif estado_actual in (ESTADO_JUGANDO, ESTADO_BOSS):
            if evento.type == pygame.KEYDOWN:
                # Saltar con ESPACIO
                if evento.key == pygame.K_SPACE and en_suelo:
                    jugador_vy = fuerza_salto
                    en_suelo = False

        elif estado_actual == ESTADO_DERROTA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                rect_repetir, rect_menu = botones_derrota()
                if rect_repetir.collidepoint(evento.pos):
                    vida_jugador = 100
                    iniciar_boss_final()      # Vuelve a empezar la pelea contra el jefe
                    iniciar_musica()
                elif rect_menu.collidepoint(evento.pos):
                    estado_actual = ESTADO_PORTADA
                    iniciar_musica()

    if estado_actual == ESTADO_PORTADA:
        dibujar_portada()

    elif estado_actual == ESTADO_JUGANDO:
        # --- MOVIMIENTO Y CÁMARA ---
        teclas = pygame.key.get_pressed()
        corre = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
        velocidad = velocidad_run if corre else velocidad_base

        dx = mover_jugador(velocidad, 0, longitud_mapa - 40)
        aplicar_fisica_salto()

        camara_x = jugador_x - 250
        camara_x = max(0, min(camara_x, longitud_mapa - ANCHO))

        actualizar_animacion(dx, corre)

        # Disparar hacia el mouse (click izquierdo, se puede mantener presionado)
        if pygame.mouse.get_pressed()[0]:
            disparar()
        actualizar_efectos()

        # --- DIFICULTAD PROGRESIVA DE ENEMIGOS ---
        if nivel_actual == 1:
            cadencia_enemigo = 90
            vel_bala_enemiga = 3
        elif nivel_actual == 2:
            cadencia_enemigo = 45
            vel_bala_enemiga = 6
        else: # Nivel 3: ¡Casi imposible!
            cadencia_enemigo = 15
            vel_bala_enemiga = 10

        for e in enemigos:
            if abs(e['x'] - jugador_x) < 550:
                e['cooldown'] += 1
                if e['cooldown'] >= cadencia_enemigo:
                    e['cooldown'] = 0
                    ex, ey = enemigo_centro(e)
                    dx_e = (jugador_x + 20) - ex
                    dy_e = jugador_y - ey
                    dist = max(1, math.hypot(dx_e, dy_e))
                    vx_e = (dx_e / dist) * vel_bala_enemiga
                    vy_e = (dy_e / dist) * vel_bala_enemiga

                    balas_enemigas.append({
                        'x': ex, 'y': ey, 'vx': vx_e, 'vy': vy_e,
                        'img': rotar_bala(img_bala_enemiga, vx_e, vy_e)
                    })
                    if sonido_disparo_enemigo:
                        sonido_disparo_enemigo.play()

        # Colisiones balas enemigas
        for b in balas_enemigas[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                herir_jugador(10)
                balas_enemigas.remove(b)
                if vida_jugador <= 0:
                    if sonido_derrota:
                        sonido_derrota.play()
                    resetear_checkpoint()
            elif b['y'] > ALTO or b['y'] < 0 or b['x'] < camara_x or b['x'] > camara_x + ANCHO:
                balas_enemigas.remove(b)

        # Balas del jugador
        for bj in balas_jugador[:]:
            bj['x'] += bj['vx']
            bj['y'] += bj['vy']

            for e in enemigos[:]:
                ex, ey = enemigo_centro(e)
                if math.hypot(bj['x'] - ex, bj['y'] - ey) < 28:
                    enemigos.remove(e)
                    crear_particulas(ex, ey, 14, (255, 160, 40), vel=4, vida=28, radio=4)
                    crear_particulas(ex, ey, 6, (90, 90, 90), vel=2, vida=35, radio=5, grav=-0.03)
                    if bj in balas_jugador:
                        balas_jugador.remove(bj)
                    break
            if bj in balas_jugador and (bj['y'] < -50 or bj['y'] > ALTO + 50 or
                                        bj['x'] < camara_x - 50 or bj['x'] > camara_x + ANCHO + 50):
                balas_jugador.remove(bj)

        # Recoger armas / munición
        for item in items_arma:
            if item['activo']:
                if math.hypot((jugador_x + 20) - (item['x'] + 15), (jugador_y + 25) - (item['y'] + 15)) < 40:
                    item['activo'] = False
                    if sonido_recarga:
                        sonido_recarga.play()
                    crear_particulas(item['x'] + 15, item['y'] + 15, 16, (0, 255, 120), vel=3.5, vida=25, radio=3, grav=0)
                    if not tiene_arma:
                        tiene_arma = True
                        municion_balas += 10
                        mostrar_mensaje("¡Arma equipada! +10 balas  |  Apunta con el mouse y dispara con click")
                    else:
                        municion_balas += 5
                        mostrar_mensaje("+5 balas", 60)

        # Llegar al castillo / Refugio final
        if jugador_x >= refugio_x:
            if nivel_actual < max_niveles:
                iniciar_nivel(nivel_actual + 1)
            else:
                # Entramos a la pelea contra el villano final en el nivel 3
                iniciar_boss_final()

        # --- RENDERIZADO NIVEL ---
        pantalla.blit(fondo_actual, (0, 0))
        pantalla.blit(img_refugio, (refugio_x - camara_x, SUELO_Y - 130))

        for item in items_arma:
            if item['activo']:
                flote = math.sin(tiempo * 0.08 + item['x'] * 0.01) * 3
                cx = item['x'] - camara_x + 15
                cy = item['y'] + 15 + flote
                if -40 < cx < ANCHO + 40:
                    radio = int(22 + math.sin(tiempo * 0.1) * 3)
                    halo = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(halo, (0, 255, 120, 55), (30, 30), radio)
                    pantalla.blit(halo, (cx - 30, cy - 30))
                    pantalla.blit(img_item_arma, (cx - 15, cy - 15))

        for e in enemigos:
            ex, ey = enemigo_centro(e)
            if -60 < ex - camara_x < ANCHO + 60:
                pantalla.blit(img_enemigo, (ex - camara_x - img_enemigo.get_width() / 2,
                                            ey - img_enemigo.get_height() / 2))

        dibujar_jugador()

        for b in balas_enemigas:
            dibujar_bala(b, (255, 120, 60))
        for bj in balas_jugador:
            dibujar_bala(bj, (255, 240, 150))

        dibujar_particulas()
        dibujar_efecto_dano()
        dibujar_hud()
        dibujar_mira()

    elif estado_actual == ESTADO_BOSS:
        # --- LÓGICA DE LA BATALLA FINAL CONTRA EL JEFE ---
        dx = mover_jugador(velocidad_base, 50, boss_x - BOSS_W // 2 - JUG_W)
        aplicar_fisica_salto()
        camara_x = 0
        actualizar_animacion(dx, False)

        if pygame.mouse.get_pressed()[0]:
            disparar()
        actualizar_efectos()

        boss_cx, boss_cy = boss_x, boss_y + BOSS_H * 0.35   # Pecho del jefe: de aquí salen sus balas
        hitbox_boss = pygame.Rect(int(boss_x - BOSS_W // 2 + 15), int(boss_y + 10), BOSS_W - 30, BOSS_H - 10)

        # El jefe dispara ráfagas letales hacia el jugador
        boss_cooldown += 1
        if boss_cooldown >= 30: # Dispara rápido
            boss_cooldown = 0
            dx_b = (jugador_x + 20) - boss_cx
            dy_b = jugador_y - boss_cy
            dist = max(1, math.hypot(dx_b, dy_b))
            vx_b, vy_b = (dx_b / dist) * 7, (dy_b / dist) * 7
            balas_enemigas.append({
                'x': boss_cx, 'y': boss_cy, 'vx': vx_b, 'vy': vy_b,
                'img': rotar_bala(img_bala_enemiga, vx_b, vy_b)
            })
            if sonido_disparo_enemigo:
                sonido_disparo_enemigo.play()

        # Colisiones balas enemigas en fase Boss
        for b in balas_enemigas[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                herir_jugador(15) # Daño fuerte del jefe
                balas_enemigas.remove(b)
                if vida_jugador <= 0:
                    jugador_derrotado = True   # Se muestra el menú Repetir / Menú principal
                    balas_enemigas.clear()
                    break
            elif b['y'] > ALTO or b['y'] < 0 or b['x'] < 0 or b['x'] > ANCHO:
                balas_enemigas.remove(b)

        # Colisiones balas del jugador contra el Jefe (200 HP)
        for bj in balas_jugador[:]:
            bj['x'] += bj['vx']
            bj['y'] += bj['vy']

            if hitbox_boss.collidepoint(bj['x'], bj['y']):
                boss_vida -= 10 # Cada impacto le resta 10 de vida
                crear_particulas(bj['x'], bj['y'], 8, (255, 90, 60), vel=3.5, vida=20, radio=3)
                if bj in balas_jugador:
                    balas_jugador.remove(bj)
                if boss_vida <= 0:
                    estado_actual = ESTADO_VICTORIA
                    mixer.music.stop()
                    if sonido_victoria:
                        sonido_victoria.play()
                break
            if bj['y'] < -50 or bj['y'] > ALTO + 50 or bj['x'] < -50 or bj['x'] > ANCHO + 50:
                if bj in balas_jugador:
                    balas_jugador.remove(bj)

        # --- RENDERIZADO BATALLA BOSS ---
        pantalla.blit(fondos_niveles[2], (0, 0)) # Fondo del nivel 3
        flote_boss = math.sin(tiempo * 0.05) * 4
        pantalla.blit(img_boss, (boss_x - BOSS_W // 2, boss_y + flote_boss)) # Villano final (sin refugio)
        dibujar_jugador()

        for b in balas_enemigas:
            dibujar_bala(b, (255, 120, 60))
        for bj in balas_jugador:
            dibujar_bala(bj, (255, 240, 150))

        dibujar_particulas()
        dibujar_efecto_dano()
        dibujar_hud()

        if jugador_derrotado:
            snapshot_derrota = pantalla.copy()
            jugador_derrotado = False
            estado_actual = ESTADO_DERROTA
            mixer.music.stop()
            if sonido_derrota:
                sonido_derrota.play()
        else:
            dibujar_mira()

    elif estado_actual == ESTADO_DERROTA:
        dibujar_derrota()

    elif estado_actual == ESTADO_VICTORIA:
        pantalla.fill((10, 50, 10))
        txt_vic = fuente_titulo.render("¡VICTORIA! VILLANO DERROTADO", True, (255, 255, 255))
        pantalla.blit(txt_vic, (ANCHO // 2 - txt_vic.get_width() // 2, ALTO // 2 - 30))

    pygame.display.update()

pygame.quit()