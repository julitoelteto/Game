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
        surf = pygame.Surface((ancho, alto), pygame.SRCALPHA)
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
img_enemigo_aire = cargar_imagen("disparador_enemigo.png", 45, 45, (255, 50, 50))
img_alien = cargar_imagen("alien.png", 45, 50, (50, 255, 50)) # Alienígena caminante
BOSS_W, BOSS_H = 160, 200
img_boss = cargar_imagen("boss.png", BOSS_W, BOSS_H, (180, 0, 0))
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

# --- CARGA DE FONDOS PROGRESIVOS ---
fondos_niveles = []
for i in range(1, 4):
    imagen_fondo = cargar_imagen(f"fondo{i}.jpeg", ANCHO, ALTO, (30, 30, 50))
    fondos_niveles.append(imagen_fondo)

fondo_actual = fondos_niveles[0]

# --- GESTIÓN DE MÚSICA Y SONIDOS ---
sonido_disparo_jugador = cargar_sonido("sonidobalajugador.mp3", 0.7)
sonido_disparo_enemigo = cargar_sonido("sonidobalaenemigo.mp3", 0.4)
sonido_recarga = cargar_sonido("sonidorecarga.mp3", 0.8)
sonido_derrota = cargar_sonido("youloss.mp3", 0.9)
sonido_victoria = cargar_sonido("youwin.mp3", 0.9)

def reproducir_musica(nombre_archivo):
    try:
        mixer.music.load(nombre_archivo)
        mixer.music.set_volume(0.6)
        mixer.music.play(-1)
    except Exception as e:
        print(f"⚠️ AVISO: No se pudo reproducir la música '{nombre_archivo}': {e}")

# Fuentes
fuente_titulo = pygame.font.SysFont("Arial", 64, bold=True)
fuente_ui = pygame.font.SysFont("Arial", 22, bold=True)
fuente_pausa = pygame.font.SysFont("Arial", 48, bold=True)

# =====================================================================
#   ANIMACIÓN DEL JUGADOR
# =====================================================================
SPRITE_MIRA = 1
JUG_W, JUG_H = img_jugador.get_size()
CADERA_Y = int(JUG_H * 0.58)
HOMBRO_Y = 22
MARGEN_X, MARGEN_ARR, MARGEN_ABA = 10, 6, 4
N_FRAMES = 8

def rotar_pivote(surf, angulo, pivote, pos):
    rotada = pygame.transform.rotate(surf, angulo)
    offset = Vec(pivote) - Vec(surf.get_rect().center)
    offset_rot = offset.rotate(-angulo)
    centro = Vec(pos) - offset_rot
    return rotada, rotada.get_rect(center=(round(centro.x), round(centro.y)))

def generar_frame_jugador(ang_pierna, lift_izq, lift_der, bob, balanceo):
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
BASE_Y_LIENZO = JUG_H + MARGEN_ARR

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

color_brazo = color_promedio(img_jugador, pygame.Rect(8, max(0, CADERA_Y - 12), JUG_W - 16, 12))
color_piel = (235, 190, 150)

# --- ARMA EN LA MANO DEL JUGADOR ---
def crear_arma_procedural():
    s = pygame.Surface((34, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, (85, 85, 95), (24, 5, 10, 4))
    pygame.draw.rect(s, (45, 45, 52), (4, 3, 22, 8), border_radius=2)
    pygame.draw.line(s, (120, 120, 130), (6, 4), (24, 4), 1)
    pygame.draw.polygon(s, (95, 62, 40), [(5, 10), (12, 10), (10, 13), (4, 13)])
    pygame.draw.rect(s, (200, 200, 210), (31, 3, 2, 2))
    return s

try:
    img_arma = pygame.transform.smoothscale(pygame.image.load("arma_jugador.png").convert_alpha(), (36, 16))
except Exception:
    img_arma = crear_arma_procedural()

ARMA_W, ARMA_H = img_arma.get_size()
ARMA_PIVOTE = (8, ARMA_H // 2)
ARMA_LARGO = ARMA_W - ARMA_PIVOTE[0]
ARMA_DIST_MANO = 10

# --- ESTADOS DEL JUEGO ---
ESTADO_PORTADA = 0
ESTADO_JUGANDO = 1
ESTADO_BOSS = 2
ESTADO_VICTORIA = 3
ESTADO_DERROTA = 4
estado_actual = ESTADO_PORTADA

juego_pausado = False

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
escudo_jugador = 0
escudo_max = 100

tiene_arma = False
municion_balas = 0
VEL_BALA_JUGADOR = 12
CADENCIA_JUGADOR = 10
cooldown_disparo = 0

dir_mirada = 1
anim_fase = 0.0
moviendo = False
corriendo = False
bob_actual = 0
aplastar = 0
retroceso = 0.0
flash_timer = 0
flash_dano = 0
tiempo = 0
mensaje_texto = ""
mensaje_timer = 0

# Variables del Jefe Final
boss_x = 0
boss_y = SUELO_Y + 50 - BOSS_H
boss_vida = 200
boss_vida_max = 200
boss_cooldown = 0
jugador_derrotado = False
muerte_en_boss = False   # True si el jugador murió peleando contra el villano final
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

# --- BOTÓN DE PAUSA ---
rect_boton_pausa = pygame.Rect(ANCHO - 60, 15, 40, 40)

def alternar_pausa():
    global juego_pausado
    juego_pausado = not juego_pausado
    try:
        if juego_pausado:
            mixer.music.pause()
        else:
            mixer.music.unpause()
    except Exception:
        pass

def dibujar_boton_pausa():
    pos = pygame.mouse.get_pos()
    color_bg = (180, 50, 50) if rect_boton_pausa.collidepoint(pos) else (60, 60, 70)
    pygame.draw.rect(pantalla, color_bg, rect_boton_pausa, border_radius=8)
    pygame.draw.rect(pantalla, (255, 255, 255), rect_boton_pausa, 2, border_radius=8)
    pygame.draw.rect(pantalla, (255, 255, 255), (rect_boton_pausa.x + 12, rect_boton_pausa.y + 10, 5, 20))
    pygame.draw.rect(pantalla, (255, 255, 255), (rect_boton_pausa.x + 23, rect_boton_pausa.y + 10, 5, 20))

def dibujar_pantalla_pausa():
    overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    pantalla.blit(overlay, (0, 0))
    
    txt = fuente_pausa.render("JUEGO EN PAUSA", True, (255, 255, 255))
    pantalla.blit(txt, (ANCHO // 2 - txt.get_width() // 2, ALTO // 2 - 50))
    
    sub_txt = fuente_ui.render("Haz clic en el botón || o presiona P para reanudar", True, (200, 200, 200))
    pantalla.blit(sub_txt, (ANCHO // 2 - sub_txt.get_width() // 2, ALTO // 2 + 20))
    dibujar_boton_pausa()

# =====================================================================
#   UTILIDADES
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
    return pygame.transform.rotate(img, -math.degrees(math.atan2(vy, vx)))

def dibujar_bala(b, color_estela):
    x, y = b['x'] - camara_x, b['y']
    pygame.draw.line(pantalla, color_estela, (x - b['vx'] * 3, y - b['vy'] * 3), (x, y), 2)
    img = b['img']
    pantalla.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)))

def enemigo_centro(e):
    if e['tipo'] == 'caminante':
        return e['x'] + img_alien.get_width() / 2, e['y'] + img_alien.get_height() / 2
    else:
        flote = math.sin(tiempo * 0.05 + e['x'] * 0.01) * 4
        return e['x'] + img_enemigo_aire.get_width() / 2, e['y'] + img_enemigo_aire.get_height() / 2 + flote

def herir_jugador(dano):
    global vida_jugador, escudo_jugador, flash_dano
    flash_dano = 10
    
    if escudo_jugador > 0:
        if escudo_jugador >= dano:
            escudo_jugador -= dano
            crear_particulas(jugador_x + JUG_W / 2, jugador_y + JUG_H / 2, 8, (0, 180, 255), vel=3, vida=20)
        else:
            resto_dano = dano - escudo_jugador
            escudo_jugador = 0
            vida_jugador -= resto_dano
            crear_particulas(jugador_x + JUG_W / 2, jugador_y + JUG_H / 2, 8, (200, 30, 30), vel=3, vida=20)
    else:
        vida_jugador -= dano
        crear_particulas(jugador_x + JUG_W / 2, jugador_y + JUG_H / 2, 8, (200, 30, 30), vel=3, vida=20)

# =====================================================================
#   APUNTADO Y DISPARO CON EL MOUSE
# =====================================================================
def estado_apuntado():
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
    punta = hombro + direc * (ARMA_DIST_MANO + ARMA_LARGO)
    vx, vy = direc.x * VEL_BALA_JUGADOR, direc.y * VEL_BALA_JUGADOR
    balas_jugador.append({'x': punta.x + camara_x, 'y': punta.y, 'vx': vx, 'vy': vy,
                          'img': rotar_bala(img_bala_jugador, vx, vy)})
    municion_balas -= 1
    cooldown_disparo = CADENCIA_JUGADOR
    retroceso = 5.0
    flash_timer = 3
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
    return jugador_x - x_antes

def aplicar_fisica_salto():
    global jugador_y, jugador_vy, en_suelo, aplastar
    vy_previa = jugador_vy
    jugador_vy += gravedad
    jugador_y += jugador_vy
    if jugador_y >= SUELO_Y:
        if not en_suelo and vy_previa > 6:
            aplastar = 7
            for lado in (-1, 1):
                crear_particulas(jugador_x + JUG_W / 2 + lado * 10, SUELO_Y + JUG_H - 2, 3,
                                 (160, 150, 130), vel=1.5, vida=18, radio=3, grav=-0.02, arriba=True)
        jugador_y = SUELO_Y
        jugador_vy = 0
        en_suelo = True

def actualizar_animacion(dx, corre):
    global anim_fase, moviendo, corriendo, dir_mirada, bob_actual
    moviendo = dx != 0
    corriendo = corre and moviendo

    if tiene_arma:
        mx, _ = pygame.mouse.get_pos()
        centro = jugador_x - camara_x + JUG_W / 2
        if abs(mx - centro) > 3:
            dir_mirada = 1 if mx > centro else -1
    elif moviendo:
        dir_mirada = 1 if dx > 0 else -1

    if moviendo:
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
        bob_actual = round(math.sin(tiempo * 0.08))

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

    altura = max(0, SUELO_Y - jugador_y)
    w_sombra = max(14, int(36 - altura * 0.12))
    sombra = pygame.Surface((w_sombra, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 90), sombra.get_rect())
    pantalla.blit(sombra, (pies_x - w_sombra / 2, SUELO_Y + JUG_H - 6))

    if not en_suelo:
        frame = frame_salto
    elif moviendo:
        frame = (frames_correr if corriendo else frames_caminar)[int(anim_fase) % N_FRAMES]
    else:
        frame = frame_quieto

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
    hombro, direc, ang = estado_apuntado()
    mano = hombro + direc * (ARMA_DIST_MANO - retroceso)

    pygame.draw.line(pantalla, color_brazo, hombro, mano, 5)
    pygame.draw.circle(pantalla, color_brazo, (int(hombro.x), int(hombro.y)), 3)

    arma = img_arma
    if direc.x < 0:
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
#   NIVELES Y RECONFIGURACIÓN DE ENEMIGOS
# =====================================================================
# Variables para guardar el estado al iniciar el nivel (para poder repetir el mismo nivel al morir)
checkpoint_vida = 100
checkpoint_escudo = 0

def restaurar_salud_checkpoint():
    """Devuelve la vida y el escudo que tenías al ENTRAR al nivel (o a la pelea final) donde moriste."""
    global vida_jugador, escudo_jugador
    vida_jugador = checkpoint_vida
    escudo_jugador = checkpoint_escudo

def iniciar_nivel(nivel, conservar_salud=False):
    """Configura el mapa, dificultad y los enemigos según el nivel. 
       Si conservar_salud es True, mantiene la vida y escudo actuales."""
    global nivel_actual, longitud_mapa, refugio_x, fondo_actual, juego_pausado
    global checkpoint_vida, checkpoint_escudo
    global vida_jugador, escudo_jugador, municion_balas
    global jugador_x, jugador_y, jugador_vy, en_suelo, camara_x
    
    nivel_actual = nivel
    juego_pausado = False

    reproducir_musica("MusicaFondo.mp3")

    fondo_actual = fondos_niveles[nivel_actual - 1]
    longitud_mapa = 5500 + (nivel * 1500)
    refugio_x = longitud_mapa - 350

    if not conservar_salud:
        vida_jugador = 100
        escudo_jugador = 0

    # Guardamos el estado actual como checkpoint de este nivel
    checkpoint_vida = vida_jugador
    checkpoint_escudo = escudo_jugador

    jugador_x = 100
    camara_x = 0
    jugador_y = SUELO_Y
    jugador_vy = 0
    en_suelo = True
    municion_balas = 15 if tiene_arma else 0
    balas_enemigas.clear()
    balas_jugador.clear()
    particulas.clear()

    enemigos.clear()
    items_arma.clear()

    # --- CONFIGURACIÓN DE ENEMIGOS SEGÚN NIVEL ---
    if nivel == 1:
        cant_aliens = 20
        distribucion = (refugio_x - 500) / cant_aliens
        for i in range(cant_aliens):
            pos_x = int(500 + (i * distribucion) + random.randint(-30, 30))
            enemigos.append({
                'tipo': 'caminante',
                'x': pos_x,
                'y': SUELO_Y,
                'vx': -2.0,
                'cooldown': random.randint(0, 60)
            })

    elif nivel == 2:
        cant_aereos = 25
        distribucion = (refugio_x - 400) / cant_aereos
        for i in range(cant_aereos):
            pos_x = int(400 + (i * distribucion) + random.randint(-40, 40))
            enemigos.append({
                'tipo': 'aereo',
                'x': pos_x,
                'y': random.randint(30, 95),
                'cooldown': random.randint(0, 60)
            })

    elif nivel == 3:
        cant_aereos = 10
        distribucion_a = (refugio_x - 400) / cant_aereos
        for i in range(cant_aereos):
            pos_x = int(400 + (i * distribucion_a) + random.randint(-30, 30))
            enemigos.append({
                'tipo': 'aereo',
                'x': pos_x,
                'y': random.randint(30, 95),
                'cooldown': random.randint(0, 60)
            })

        cant_aliens = 12
        distribucion_c = (refugio_x - 500) / cant_aliens
        for i in range(cant_aliens):
            pos_x = int(500 + (i * distribucion_c) + random.randint(-30, 30))
            enemigos.append({
                'tipo': 'caminante',
                'x': pos_x,
                'y': SUELO_Y,
                'vx': -2.5,
                'cooldown': random.randint(0, 60)
            })

    if not tiene_arma:
        items_arma.append({'x': 330, 'y': SUELO_Y + 15, 'activo': True})

    for _ in range(6):
        items_arma.append({
            'x': random.randint(600, refugio_x - 400),
            'y': SUELO_Y + 15,
            'activo': True
        })

def iniciar_boss_final():
    global estado_actual, jugador_x, jugador_y, jugador_vy, en_suelo, camara_x, boss_x, boss_y, boss_vida
    global balas_enemigas, balas_jugador, municion_balas, tiene_arma, boss_cooldown, flash_dano, jugador_derrotado, juego_pausado
    global checkpoint_vida, checkpoint_escudo
    
    estado_actual = ESTADO_BOSS
    juego_pausado = False
    
    # Guardamos checkpoint al entrar al Boss (por si muere en la pelea y da clic en repetir)
    checkpoint_vida = vida_jugador
    checkpoint_escudo = escudo_jugador

    reproducir_musica("musicadeboss.mp3")

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
    municion_balas = 50
    balas_enemigas.clear()
    balas_jugador.clear()
    particulas.clear()

# --- UI Y PORTADA ---
def dibujar_portada():
    if fondo_portada:
        pantalla.blit(fondo_portada, (0, 0))
    else:
        pantalla.fill((15, 15, 30))

    rect_boton = pygame.Rect(ANCHO // 2 - 100, 420, 200, 60)
    pos_mouse = pygame.mouse.get_pos()
    color_boton = (0, 200, 100) if rect_boton.collidepoint(pos_mouse) else (0, 150, 70)
    pygame.draw.rect(pantalla, color_boton, rect_boton, border_radius=10)

    txt_empezar = fuente_ui.render("EMPEZAR", True, (255, 255, 255))
    pantalla.blit(txt_empezar, (rect_boton.x + (200 - txt_empezar.get_width()) // 2, rect_boton.y + 18))
    return rect_boton

def dibujar_hud():
    # Barra de vida del jugador (Roja)
    pygame.draw.rect(pantalla, (100, 0, 0), (20, 15, 180, 16))
    pygame.draw.rect(pantalla, (0, 255, 0), (20, 15, max(0, int(vida_jugador * 1.8)), 16))
    pygame.draw.rect(pantalla, (255, 255, 255), (20, 15, 180, 16), 2)
    txt_vida = fuente_ui.render(f"HP: {max(0, vida_jugador)}/100", True, (255, 255, 255))
    pantalla.blit(txt_vida, (210, 12))

    # Barra de Escudo del jugador (Azul)
    pygame.draw.rect(pantalla, (0, 50, 100), (20, 36, 180, 16))
    pygame.draw.rect(pantalla, (0, 180, 255), (20, 36, max(0, int(escudo_jugador * 1.8)), 16))
    pygame.draw.rect(pantalla, (255, 255, 255), (20, 36, 180, 16), 2)
    txt_escudo = fuente_ui.render(f"ESC: {escudo_jugador}/100", True, (0, 220, 255))
    pantalla.blit(txt_escudo, (210, 33))

    if estado_actual == ESTADO_JUGANDO:
        txt_lvl = fuente_ui.render(f"Nivel: {nivel_actual}/{max_niveles}", True, (255, 255, 0))
        pantalla.blit(txt_lvl, (ANCHO - 220, 18))

        porcentaje = int((jugador_x / refugio_x) * 100)
        txt_progreso = fuente_ui.render(f"Meta: {min(100, porcentaje)}%", True, (200, 255, 200))
        pantalla.blit(txt_progreso, (ANCHO - 220, 45))
    elif estado_actual == ESTADO_BOSS:
        txt_jefe = fuente_ui.render("¡BATALLA FINAL CONTRA EL VILLANO!", True, (255, 50, 50))
        pantalla.blit(txt_jefe, (ANCHO // 2 - txt_jefe.get_width() // 2, 108))

        pygame.draw.rect(pantalla, (80, 0, 0), (ANCHO // 2 - 150, 50, 300, 25))
        ancho_barra_boss = max(0, int((boss_vida / boss_vida_max) * 300))
        pygame.draw.rect(pantalla, (255, 0, 0), (ANCHO // 2 - 150, 50, ancho_barra_boss, 25))
        pygame.draw.rect(pantalla, (255, 255, 255), (ANCHO // 2 - 150, 50, 300, 25), 2)
        txt_vb = fuente_ui.render(f"Villano: {boss_vida}/{boss_vida_max}", True, (255, 255, 255))
        pantalla.blit(txt_vb, (ANCHO // 2 - txt_vb.get_width() // 2 - 3, 77))

    if tiene_arma:
        color_municion = (0, 255, 255) if municion_balas > 0 else (255, 80, 80)
        txt_arma = fuente_ui.render(f"Balas: {municion_balas}", True, color_municion)
    else:
        txt_arma = fuente_ui.render("Sin arma", True, (170, 170, 170))
    pantalla.blit(txt_arma, (20, 57))

    if mensaje_timer > 0:
        txt = fuente_ui.render(mensaje_texto, True, (255, 255, 255))
        txt.set_alpha(min(255, mensaje_timer * 10))
        pantalla.blit(txt, (ANCHO // 2 - txt.get_width() // 2, 110))

    dibujar_boton_pausa()

def botones_derrota():
    return (pygame.Rect(ANCHO // 2 - 130, 340, 260, 55),
            pygame.Rect(ANCHO // 2 - 130, 415, 260, 55))

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

def dibujar_victoria():
    if snapshot_derrota:
        pantalla.blit(snapshot_derrota, (0, 0))
    oscuro = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    oscuro.fill((0, 0, 0, 175))
    pantalla.blit(oscuro, (0, 0))

    txt = fuente_titulo.render("¡VICTORIA!", True, (255, 215, 0))
    pantalla.blit(txt, (ANCHO // 2 - txt.get_width() // 2, 180))

    txt_sub = fuente_ui.render("¡Has derrotado al villano final!", True, (200, 255, 200))
    pantalla.blit(txt_sub, (ANCHO // 2 - txt_sub.get_width() // 2, 260))

    pos = pygame.mouse.get_pos()
    menu_rect = pygame.Rect(ANCHO // 2 - 130, 360, 260, 55)
    color_btn = (0, 200, 100) if menu_rect.collidepoint(pos) else (0, 150, 70)
    pygame.draw.rect(pantalla, color_btn, menu_rect, border_radius=10)
    t = fuente_ui.render("MENÚ PRINCIPAL", True, (255, 255, 255))
    pantalla.blit(t, (menu_rect.centerx - t.get_width() // 2, menu_rect.centery - t.get_height() // 2))
    return menu_rect

def dibujar_efecto_dano():
    if flash_dano > 0:
        overlay_dano.set_alpha(flash_dano * 9)
        pantalla.blit(overlay_dano, (0, 0))

# --- BUCLE PRINCIPAL ---
ejecutando = True
while ejecutando:
    reloj.tick(60)

    if not juego_pausado:
        tiempo += 1

    pygame.mouse.set_visible(estado_actual not in (ESTADO_JUGANDO, ESTADO_BOSS) or juego_pausado)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

        if estado_actual == ESTADO_PORTADA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                rect_btn = pygame.Rect(ANCHO // 2 - 100, 420, 200, 60)
                if rect_btn.collidepoint(evento.pos):
                    tiene_arma = False
                    vida_jugador = 100
                    escudo_jugador = 0
                    iniciar_nivel(1, conservar_salud=False)
                    estado_actual = ESTADO_JUGANDO

        elif estado_actual in (ESTADO_JUGANDO, ESTADO_BOSS):
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if rect_boton_pausa.collidepoint(evento.pos):
                    alternar_pausa()

            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                    alternar_pausa()
                if evento.key == pygame.K_SPACE and en_suelo and not juego_pausado:
                    jugador_vy = fuerza_salto
                    en_suelo = False

        elif estado_actual == ESTADO_DERROTA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                rect_repetir, rect_menu = botones_derrota()
                if rect_repetir.collidepoint(evento.pos):
                    # Repite el nivel (o la pelea final) donde moriste, con la vida/escudo con que entraste
                    restaurar_salud_checkpoint()
                    if muerte_en_boss:
                        iniciar_boss_final()                         # Pone estado BOSS y su música
                    else:
                        iniciar_nivel(nivel_actual, conservar_salud=True)
                        estado_actual = ESTADO_JUGANDO
                elif rect_menu.collidepoint(evento.pos):
                    estado_actual = ESTADO_PORTADA
                    reproducir_musica("MusicaFondo.mp3")

        elif estado_actual == ESTADO_VICTORIA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                btn_menu = pygame.Rect(ANCHO // 2 - 130, 360, 260, 55)
                if btn_menu.collidepoint(evento.pos):
                    estado_actual = ESTADO_PORTADA
                    reproducir_musica("MusicaFondo.mp3")

    if estado_actual == ESTADO_PORTADA:
        dibujar_portada()

    elif estado_actual == ESTADO_JUGANDO:
        if not juego_pausado:
            teclas = pygame.key.get_pressed()
            corre = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
            velocidad = velocidad_run if corre else velocidad_base

            dx = mover_jugador(velocidad, 0, longitud_mapa - 40)
            aplicar_fisica_salto()

            camara_x = jugador_x - 250
            camara_x = max(0, min(camara_x, longitud_mapa - ANCHO))

            actualizar_animacion(dx, corre)

            if pygame.mouse.get_pressed()[0] and not rect_boton_pausa.collidepoint(pygame.mouse.get_pos()):
                disparar()
            actualizar_efectos()

            cadencia_enemigo = 60 if nivel_actual == 1 else (45 if nivel_actual == 2 else 20)
            vel_bala_enemiga = 5 if nivel_actual == 1 else (7 if nivel_actual == 2 else 9)

            for e in enemigos:
                if e['tipo'] == 'caminante':
                    e['x'] += e['vx']

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

            for b in balas_enemigas[:]:
                b['x'] += b['vx']
                b['y'] += b['vy']
                if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                    herir_jugador(10)
                    balas_enemigas.remove(b)
                    if vida_jugador <= 0:
                        muerte_en_boss = False
                        snapshot_derrota = pantalla.copy()
                        estado_actual = ESTADO_DERROTA
                        mixer.music.stop()
                        if sonido_derrota:
                            sonido_derrota.play()
                        break
                elif b['y'] > ALTO or b['y'] < 0 or b['x'] < camara_x - 100 or b['x'] > camara_x + ANCHO + 100:
                    balas_enemigas.remove(b)

            for bj in balas_jugador[:]:
                bj['x'] += bj['vx']
                bj['y'] += bj['vy']

                for e in enemigos[:]:
                    ex, ey = enemigo_centro(e)
                    if math.hypot(bj['x'] - ex, bj['y'] - ey) < 30:
                        enemigos.remove(e)
                        
                        # --- RECOMPENSA POR KILL (+10 Vida y +10 Escudo, máx 100) ---
                        vida_jugador = min(100, vida_jugador + 10)
                        escudo_jugador = min(escudo_max, escudo_jugador + 10)
                        crear_particulas(ex, ey, 10, (0, 255, 120), vel=3.0, vida=20, radio=3, grav=0)
                        
                        crear_particulas(ex, ey, 14, (255, 160, 40), vel=4, vida=28, radio=4)
                        crear_particulas(ex, ey, 6, (90, 90, 90), vel=2, vida=35, radio=5, grav=-0.03)
                        if bj in balas_jugador:
                            balas_jugador.remove(bj)
                        break
                if bj in balas_jugador and (bj['y'] < -50 or bj['y'] > ALTO + 50 or
                                            bj['x'] < camara_x - 50 or bj['x'] > camara_x + ANCHO + 50):
                    balas_jugador.remove(bj)

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
                            mostrar_mensaje("¡Arma equipada! +10 balas")
                        else:
                            municion_balas += 5
                            mostrar_mensaje("+5 balas", 60)

            if jugador_x >= refugio_x:
                if nivel_actual < max_niveles:
                    # Al pasar de nivel, conservamos la vida y escudo actuales
                    iniciar_nivel(nivel_actual + 1, conservar_salud=True)
                else:
                    iniciar_boss_final()

        # Renderizado Nivel
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
                if e['tipo'] == 'caminante':
                    pantalla.blit(img_alien, (ex - camara_x - img_alien.get_width() / 2,
                                              ey - img_alien.get_height() / 2))
                else:
                    pantalla.blit(img_enemigo_aire, (ex - camara_x - img_enemigo_aire.get_width() / 2,
                                                ey - img_enemigo_aire.get_height() / 2))

        dibujar_jugador()

        for b in balas_enemigas:
            dibujar_bala(b, (255, 120, 60))
        for bj in balas_jugador:
            dibujar_bala(bj, (255, 240, 150))

        dibujar_particulas()
        dibujar_efecto_dano()
        dibujar_hud()

        if juego_pausado:
            dibujar_pantalla_pausa()
        else:
            dibujar_mira()

    elif estado_actual == ESTADO_BOSS:
        if not juego_pausado:
            dx = mover_jugador(velocidad_base, 50, boss_x - BOSS_W // 2 - JUG_W)
            aplicar_fisica_salto()
            camara_x = 0
            actualizar_animacion(dx, False)

            if pygame.mouse.get_pressed()[0] and not rect_boton_pausa.collidepoint(pygame.mouse.get_pos()):
                disparar()
            actualizar_efectos()

            boss_cx, boss_cy = boss_x, boss_y + BOSS_H * 0.35
            hitbox_boss = pygame.Rect(int(boss_x - BOSS_W // 2 + 15), int(boss_y + 10), BOSS_W - 30, BOSS_H - 10)

            boss_cooldown += 1
            if boss_cooldown >= 30:
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

            for b in balas_enemigas[:]:
                b['x'] += b['vx']
                b['y'] += b['vy']
                if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                    herir_jugador(15)
                    balas_enemigas.remove(b)
                    if vida_jugador <= 0:
                        jugador_derrotado = True
                        balas_enemigas.clear()
                        break
                elif b['y'] > ALTO or b['y'] < 0 or b['x'] < 0 or b['x'] > ANCHO:
                    balas_enemigas.remove(b)

            for bj in balas_jugador[:]:
                bj['x'] += bj['vx']
                bj['y'] += bj['vy']

                if hitbox_boss.collidepoint(bj['x'], bj['y']):
                    boss_vida -= 10
                    # Recompensa por impacto al Boss (+10 Vida y +10 Escudo)
                    vida_jugador = min(100, vida_jugador + 10)
                    escudo_jugador = min(escudo_max, escudo_jugador + 10)
                    crear_particulas(bj['x'], bj['y'], 8, (255, 90, 60), vel=3.5, vida=20, radio=3)
                    if bj in balas_jugador:
                        balas_jugador.remove(bj)
                    if boss_vida <= 0:
                        snapshot_derrota = pantalla.copy()
                        estado_actual = ESTADO_VICTORIA
                        mixer.music.stop()
                        if sonido_victoria:
                            sonido_victoria.play()
                    break
                if bj['y'] < -50 or bj['y'] > ALTO + 50 or bj['x'] < -50 or bj['x'] > ANCHO + 50:
                    if bj in balas_jugador:
                        balas_jugador.remove(bj)

        # Renderizado Boss
        pantalla.blit(fondos_niveles[2], (0, 0))
        flote_boss = math.sin(tiempo * 0.05) * 4
        pantalla.blit(img_boss, (boss_x - BOSS_W // 2, boss_y + flote_boss))
        dibujar_jugador()

        for b in balas_enemigas:
            dibujar_bala(b, (255, 120, 60))
        for bj in balas_jugador:
            dibujar_bala(bj, (255, 240, 150))

        dibujar_particulas()
        dibujar_efecto_dano()
        dibujar_hud()

        if jugador_derrotado:
            muerte_en_boss = True
            snapshot_derrota = pantalla.copy()
            jugador_derrotado = False
            estado_actual = ESTADO_DERROTA
            mixer.music.stop()
            if sonido_derrota:
                sonido_derrota.play()

        if juego_pausado:
            dibujar_pantalla_pausa()
        elif estado_actual == ESTADO_BOSS and not jugador_derrotado:
            dibujar_mira()

    elif estado_actual == ESTADO_DERROTA:
        dibujar_derrota()

    elif estado_actual == ESTADO_VICTORIA:
        dibujar_victoria()

    pygame.display.update()

pygame.quit()