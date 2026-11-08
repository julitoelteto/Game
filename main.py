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

# --- CARGA DE ASSETS (Imágenes y Respaldo) ---
def cargar_imagen(nombre_archivo, ancho, alto, color_fallback=(0, 255, 0)):
    try:
        img = pygame.image.load(nombre_archivo).convert_alpha()
        return pygame.transform.scale(img, (ancho, alto))
    except Exception as e:
        print(f"⚠️ AVISO: No se pudo cargar '{nombre_archivo}'. Usando respaldo. Detalle: {e}")
        surf = pygame.Surface((ancho, alto))
        surf.fill(color_fallback)
        return surf

def cargar_sonido(nombre_archivo, volumen=0.5):
    try:
        sonido = mixer.Sound(nombre_archivo)
        sonido.set_volume(volumen)
        return sonido
    except:
        return None

# Carga de Portada y Sprites principales
fondo_portada = cargar_imagen("FondoPortada.jpg", ANCHO, ALTO, (20, 20, 40))
img_jugador = cargar_imagen("jugador.png", 40, 50, (0, 200, 255))
img_enemigo = cargar_imagen("disparador_enemigo.png", 45, 45, (255, 50, 50))
img_boss = cargar_imagen("boss.png", 70, 90, (180, 0, 0)) # Villano final
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

sonido_disparo_jugador = cargar_sonido("disparo.mp3", 0.7)
sonido_disparo_enemigo = cargar_sonido("disparo_enemigo.mp3", 0.4)

# Fuentes
fuente_titulo = pygame.font.SysFont("Arial", 64, bold=True)
fuente_ui = pygame.font.SysFont("Arial", 24, bold=True)

# --- ESTADOS DEL JUEGO ---
ESTADO_PORTADA = 0
ESTADO_JUGANDO = 1
ESTADO_BOSS = 2
ESTADO_VICTORIA = 3
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

# Sistema de Munición
municion_balas = 10 # Empezamos con unas balas para defendernos

# Variables del Jefe Final
boss_x = 0
boss_y = SUELO_Y - 90
boss_vida = 200
boss_vida_max = 200
boss_cooldown = 0

# Listas del nivel
balas_jugador = [] 
enemigos = [] 
balas_enemigas = [] 
items_arma = []
longitud_mapa = 6000   
refugio_x = longitud_mapa - 350

def resetear_checkpoint():
    """Reaparece al jugador en el inicio del nivel actual con vida llena."""
    global jugador_x, jugador_y, jugador_vy, vida_jugador, municion_balas, balas_enemigas, camara_x, en_suelo
    jugador_x = 100
    camara_x = 0
    jugador_y = SUELO_Y
    jugador_vy = 0
    en_suelo = True
    vida_jugador = 100
    municion_balas = 15  
    balas_enemigas.clear()

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
        
    # Colocar armas en el camino
    for _ in range(6):
        items_arma.append({
            'x': random.randint(600, refugio_x - 400),
            'y': SUELO_Y + 15,
            'activo': True
        })

def iniciar_boss_final():
    """Prepara el escenario de combate contra el villano final."""
    global estado_actual, jugador_x, camara_x, boss_x, boss_y, boss_vida, balas_enemigas, balas_jugador, municion_balas
    estado_actual = ESTADO_BOSS
    jugador_x = 200
    camara_x = 0
    boss_x = 600
    boss_y = SUELO_Y - 90
    boss_vida = 200
    municion_balas = 50 # Munición generosa para la pelea final
    balas_enemigas.clear()
    balas_jugador.clear()

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
    
    txt_vida = fuente_ui.render(f"Vida: {vida_jugador}/100", True, (255, 255, 255))
    pantalla.blit(txt_vida, (230, 18))
    
    if estado_actual == ESTADO_JUGANDO:
        txt_lvl = fuente_ui.render(f"Nivel: {nivel_actual}/{max_niveles}", True, (255, 255, 0))
        pantalla.blit(txt_lvl, (ANCHO - 150, 18))
        
        porcentaje = int((jugador_x / refugio_x) * 100)
        txt_progreso = fuente_ui.render(f"Meta: {min(100, porcentaje)}%", True, (200, 255, 200))
        pantalla.blit(txt_progreso, (ANCHO - 160, 45))
    elif estado_actual == ESTADO_BOSS:
        txt_jefe = fuente_ui.render("¡BATALLA FINAL CONTRA EL VILLANO!", True, (255, 50, 50))
        pantalla.blit(txt_jefe, (ANCHO // 2 - txt_jefe.get_width() // 2, 15))
        
        # Barra de vida del Jefe
        pygame.draw.rect(pantalla, (80, 0, 0), (ANCHO // 2 - 150, 50, 300, 25))
        ancho_barra_boss = max(0, int((boss_vida / boss_vida_max) * 300))
        pygame.draw.rect(pantalla, (255, 0, 0), (ANCHO // 2 - 150, 50, ancho_barra_boss, 25))
        pygame.draw.rect(pantalla, (255, 255, 255), (ANCHO // 2 - 150, 50, 300, 25), 2)
        txt_vb = fuente_ui.render(f"Villano: {boss_vida}/{boss_vida_max}", True, (255, 255, 255))
        pantalla.blit(txt_vb, (ANCHO // 2 - txt_vb.get_width() // 2 - 3, 77))

    # Indicador de Munición
    color_municion = (0, 255, 255) if municion_balas > 0 else (255, 80, 80)
    txt_arma = fuente_ui.render(f"Balas: {municion_balas}", True, color_municion)
    pantalla.blit(txt_arma, (20, 45))

# --- BUCLE PRINCIPAL ---
ejecutando = True
while ejecutando:
    reloj.tick(60) 
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
            
        if estado_actual == ESTADO_PORTADA:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                rect_btn = pygame.Rect(ANCHO // 2 - 100, 420, 200, 60)
                if rect_btn.collidepoint(evento.pos):
                    iniciar_nivel(1)
                    estado_actual = ESTADO_JUGANDO

        elif estado_actual in (ESTADO_JUGANDO, ESTADO_BOSS):
            if evento.type == pygame.KEYDOWN:
                # Saltar con ESPACIO
                if evento.key == pygame.K_SPACE and en_suelo:
                    jugador_vy = fuerza_salto
                    en_suelo = False

            # Disparar con CLICK IZQUIERDO hacia donde apunta el cursor del mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if municion_balas > 0:
                    mx, my = pygame.mouse.get_pos()
                    # Convertir coordenadas de pantalla a coordenadas del mundo (aplicando cámara)
                    world_mx = mx + camara_x if estado_actual == ESTADO_JUGANDO else mx
                    world_my = my
                    
                    p_x = jugador_x + 20
                    p_y = jugador_y + 25
                    
                    dx = world_mx - p_x
                    dy = world_my - p_y
                    dist = max(1, math.hypot(dx, dy))
                    
                    vel_bala_jugador = 12
                    vx = (dx / dist) * vel_bala_jugador
                    vy = (dy / dist) * vel_bala_jugador
                    
                    balas_jugador.append({'x': p_x, 'y': p_y, 'vx': vx, 'vy': vy})
                    municion_balas -= 1  
                    if sonido_disparo_jugador:
                        sonido_disparo_jugador.play()

    if estado_actual == ESTADO_PORTADA:
        dibujar_portada()

    elif estado_actual == ESTADO_JUGANDO:
        # --- MOVIMIENTO Y CÁMARA ---
        teclas = pygame.key.get_pressed()
        velocidad = velocidad_run if (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]) else velocidad_base
        
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            jugador_x -= velocidad
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            jugador_x += velocidad

        jugador_x = max(0, min(jugador_x, longitud_mapa - 40))

        # Físicas de salto
        jugador_vy += gravedad
        jugador_y += jugador_vy
        if jugador_y >= SUELO_Y:
            jugador_y = SUELO_Y
            jugador_vy = 0
            en_suelo = True

        camara_x = jugador_x - 250
        camara_x = max(0, min(camara_x, longitud_mapa - ANCHO))

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
                    dx = (jugador_x + 20) - e['x']
                    dy = jugador_y - e['y']
                    dist = max(1, math.hypot(dx, dy))
                    
                    balas_enemigas.append({
                        'x': e['x'],
                        'y': e['y'],
                        'vx': (dx / dist) * vel_bala_enemiga,
                        'vy': (dy / dist) * vel_bala_enemiga
                    })
                    if sonido_disparo_enemigo:
                        sonido_disparo_enemigo.play()

        # Colisiones balas enemigas
        for b in balas_enemigas[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                vida_jugador -= 10
                balas_enemigas.remove(b)
                if vida_jugador <= 0:
                    resetear_checkpoint() 
            elif b['y'] > ALTO or b['y'] < 0 or b['x'] < camara_x or b['x'] > camara_x + ANCHO:
                balas_enemigas.remove(b)

        # Balas del jugador
        for bj in balas_jugador[:]:
            bj['x'] += bj['vx']
            bj['y'] += bj['vy']
            
            for e in enemigos[:]:
                if math.hypot(bj['x'] - e['x'], bj['y'] - e['y']) < 30:
                    enemigos.remove(e)
                    if bj in balas_jugador:
                        balas_jugador.remove(bj)
                    break
            if bj in balas_jugador and (bj['y'] < 0 or bj['y'] > ALTO if 'ALTO' in globals() else bj['y'] > ALTO):
                balas_jugador.remove(bj)

        # Recoger armas (+5 balas)
        for item in items_arma:
            if item['activo']:
                if math.hypot((jugador_x + 20) - item['x'], jugador_y - item['y']) < 35:
                    municion_balas += 5  
                    item['activo'] = False

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
                pantalla.blit(img_item_arma, (item['x'] - camara_x, item['y']))

        for e in enemigos:
            pantalla.blit(img_enemigo, (e['x'] - camara_x, e['y']))

        pantalla.blit(img_jugador, (jugador_x - camara_x, jugador_y))

        for b in balas_enemigas:
            pantalla.blit(img_bala_enemiga, (int(b['x'] - camara_x), int(b['y'])))
        for bj in balas_jugador:
            pantalla.blit(img_bala_jugador, (int(bj['x'] - camara_x), int(bj['y'])))

        dibujar_hud()

    elif estado_actual == ESTADO_BOSS:
        # --- LÓGICA DE LA BATALLA FINAL CONTRA EL JEFE ---
        teclas = pygame.key.get_pressed()
        velocidad = velocidad_base
        
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            jugador_x -= velocidad
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            jugador_x += velocidad

        # Limitar movimiento dentro de la arena del jefe
        jugador_x = max(50, min(jugador_x, ANCHO - 100))

        # Físicas de salto
        jugador_vy += gravedad
        jugador_y += jugador_vy
        if jugador_y >= SUELO_Y:
            jugador_y = SUELO_Y
            jugador_vy = 0
            en_suelo = True

        # El jefe dispara ráfagas letales hacia el jugador
        boss_cooldown += 1
        if boss_cooldown >= 30: # Dispara rápido
            boss_cooldown = 0
            dx = (jugador_x + 20) - boss_x
            dy = jugador_y - boss_y
            dist = max(1, math.hypot(dx, dy))
            balas_enemigas.append({
                'x': boss_x,
                'y': boss_y,
                'vx': (dx / dist) * 7,
                'vy': (dy / dist) * 7
            })
            if sonido_disparo_enemigo:
                sonido_disparo_enemigo.play()

        # Colisiones balas enemigas en fase Boss
        for b in balas_enemigas[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            if math.hypot(b['x'] - (jugador_x + 20), b['y'] - (jugador_y + 25)) < 25:
                vida_jugador -= 15 # Daño fuerte del jefe
                balas_enemigas.remove(b)
                if vida_jugador <= 0:
                    # Reiniciar combate de jefe
                    vida_jugador = 100
                    boss_vida = 200
                    balas_enemigas.clear()
            elif b['y'] > ALTO or b['y'] < 0 or b['x'] < 0 or b['x'] > ANCHO:
                balas_enemigas.remove(b)

        # Colisiones balas del jugador contra el Jefe (200 HP)
        for bj in balas_jugador[:]:
            bj['x'] += bj['vx']
            bj['y'] += bj['vy']
            
            if math.hypot(bj['x'] - boss_x, bj['y'] - boss_y) < 45:
                boss_vida -= 10 # Cada impacto le resta 10 de vida
                if bj in balas_jugador:
                    balas_jugador.remove(bj)
                if boss_vida <= 0:
                    estado_actual = ESTADO_VICTORIA
                    mixer.music.stop()
                break
            if bj['y'] < 0 or bj['x'] < 0 or bj['x'] > ANCHO:
                if bj in balas_jugador:
                    balas_jugador.remove(bj)

        # --- RENDERIZADO BATALLA BOSS ---
        pantalla.blit(fondos_niveles[2], (0, 0)) # Fondo del nivel 3
        pantalla.blit(img_refugio, (ANCHO - 350, SUELO_Y - 130)) # Castillo de fondo
        pantalla.blit(img_boss, (boss_x - 35, boss_y)) # Villano final
        pantalla.blit(img_jugador, (jugador_x, jugador_y)) # Jugador

        for b in balas_enemigas:
            pantalla.blit(img_bala_enemiga, (int(b['x']), int(b['y'])))
        for bj in balas_jugador:
            pantalla.blit(img_bala_jugador, (int(bj['x']), int(bj['y'])))

        dibujar_hud()

    elif estado_actual == ESTADO_VICTORIA:
        pantalla.fill((10, 50, 10))
        txt_vic = fuente_titulo.render("¡VICTORIA! VILLANO DERROTADO", True, (255, 255, 255))
        pantalla.blit(txt_vic, (ANCHO // 2 - txt_vic.get_width() // 2, ALTO // 2 - 30))

    pygame.display.update()

pygame.quit()