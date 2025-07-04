import pygame
import random
import os
import json
from datetime import datetime

# Inicializa pygame e sistema de áudio
pygame.init()
pygame.mixer.init()

# Define dimensões da tela do jogo
largura, altura = 1000, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("GameKombi")

# Definições de cores (RGB)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AMARELO = (255, 255, 0)
CINZA = (100, 100, 100)
VERDE = (0, 255, 0)
VERMELHO = (255, 0, 0)
OURO = (255, 215, 0)
PRATA = (192, 192, 192)
BRONZE = (205, 127, 50)

# Configuração de fontes, FPS e clock
clock = pygame.time.Clock()
fps = 60
fonte = pygame.font.SysFont('Arial', 24)
fonte_grande = pygame.font.SysFont('Arial', 60, bold=True)
fonte_media = pygame.font.SysFont('Arial', 40)

# Diretórios de recursos e constantes de jogo
SPRITES_DIR = "sprites"
AUDIO_DIR = "audio"
PISTA_X_MIN = 200
PISTA_X_MAX = 800
RANKING_FILE = "ranking.json"

# --- Carregamento dos sons ---
try:
    som_coleta_moeda = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "moeda.wav"))
    som_colisao = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "colisao.wav"))
    som_pickup_turbo = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "turbo_pickup.wav"))
    som_uso_turbo = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "turbo_ativado.wav"))
    som_game_over = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "game_over.wav"))
    som_combustivel = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "som_combustivel.wav"))
    musica_fundo = os.path.join(AUDIO_DIR, "musica_fundo.mp3")
except pygame.error as e:
    print(f"Erro ao carregar som/música: {e}.")
    som_coleta_moeda = som_colisao = som_pickup_turbo = som_uso_turbo = som_game_over = som_combustivel = None
    musica_fundo = None

# Função para carregar sprites redimensionando se necessário
def carregar_sprite_redimensionado(nome, largura=None, altura=None):
    caminho = os.path.join(SPRITES_DIR, nome)
    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        if largura and altura:
            return pygame.transform.scale(imagem, (largura, altura))
        return imagem
    except pygame.error as e:
        print(f"Erro ao carregar sprite '{nome}': {e}.")
        return pygame.Surface((largura or 50, altura or 50), pygame.SRCALPHA)

# Função para desenhar um botão e detectar clique
def desenhar_botao(texto, fonte, cor_texto, cor_fundo, x, y, largura, altura, borda=0):
    mouse = pygame.mouse.get_pos()
    botao_rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, cor_fundo, botao_rect, border_radius=borda)
    if borda > 0:
        pygame.draw.rect(tela, BRANCO, botao_rect, 2, border_radius=borda)
    texto_render = fonte.render(texto, True, cor_texto)
    texto_rect = texto_render.get_rect(center=(x + largura // 2, y + altura // 2))
    tela.blit(texto_render, texto_rect)
    return botao_rect.collidepoint(mouse)

# Ranking: carregar, salvar e adicionar pontuação
def carregar_ranking():
    try:
        with open(RANKING_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_ranking(ranking):
    with open(RANKING_FILE, 'w') as f:
        json.dump(ranking, f)

def adicionar_ao_ranking(nome, pontos):
    ranking = carregar_ranking()
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    ranking.append({"nome": nome, "pontos": pontos, "data": data})
    ranking.sort(key=lambda x: x["pontos"], reverse=True)
    salvar_ranking(ranking[:10])  # Mantém só top 10

# Função utilitária para evitar sobreposição de pickups/obstáculos/moedas
def colisao_com_lista(rect, lista, margem=0):
    for item in lista:
        if isinstance(item, tuple):
            _, outro_rect = item
        else:
            outro_rect = item
        if rect.inflate(margem, margem).colliderect(outro_rect):
            return True
    return False

# Tela do menu principal (input nome, start, ranking, sair)
def menu_principal():
    fundo = carregar_sprite_redimensionado("fundo_pista.png", largura, altura)
    fundo_y = 0
    nome_jogador = "Player 1"  # Valor padrão
    ativo_input = False
    while True:
        # Fundo animado descendo
        fundo_y += 2
        if fundo_y >= altura:
            fundo_y = 0
        tela.blit(fundo, (0, fundo_y - altura))
        tela.blit(fundo, (0, fundo_y))
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        # Título e input de nome
        titulo = fonte_grande.render("KOMBI RACER", True, AMARELO)
        sombra = fonte_grande.render("KOMBI RACER", True, PRETO)
        tela.blit(sombra, (largura // 2 - titulo.get_width() // 2 + 3, 103))
        tela.blit(titulo, (largura // 2 - titulo.get_width() // 2, 100))
        label_nome = fonte.render("Digite seu nome:", True, BRANCO)
        tela.blit(label_nome, (largura // 2 - 150, 200))
        input_rect = pygame.Rect(largura // 2 - 150, 230, 300, 40)
        pygame.draw.rect(tela, CINZA, input_rect, border_radius=5)
        pygame.draw.rect(tela, AMARELO if ativo_input else BRANCO, input_rect, 2, border_radius=5)
        nome_render = fonte.render(nome_jogador, True, BRANCO)
        tela.blit(nome_render, (input_rect.x + 10, input_rect.y + 10))

        mouse_clicou = False
        # Eventos do pygame (teclado/mouse)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicou = True
                if input_rect.collidepoint(evento.pos):
                    ativo_input = True
                    if nome_jogador == "Player 1":
                        nome_jogador = ""
                else:
                    ativo_input = False
            elif evento.type == pygame.KEYDOWN and ativo_input:
                if evento.key == pygame.K_RETURN:
                    ativo_input = False
                elif evento.key == pygame.K_BACKSPACE:
                    nome_jogador = nome_jogador[:-1]
                else:
                    if len(nome_jogador) < 12:
                        nome_jogador += evento.unicode

        # Botão Start
        mouse = pygame.mouse.get_pos()
        start_rect = pygame.Rect(largura // 2 - 100, 300, 200, 50)
        pygame.draw.rect(tela, AMARELO, start_rect, border_radius=25)
        pygame.draw.rect(tela, BRANCO, start_rect, 2, border_radius=25)
        start_text = fonte_media.render("START", True, PRETO)
        tela.blit(start_text, (start_rect.centerx - start_text.get_width() // 2,
                              start_rect.centery - start_text.get_height() // 2))
        if start_rect.collidepoint(mouse) and mouse_clicou and nome_jogador.strip():
            if musica_fundo and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            return nome_jogador if nome_jogador.strip() else "Player 1"

        # Botão Ranking
        ranking_rect = pygame.Rect(largura // 2 - 100, 370, 200, 50)
        pygame.draw.rect(tela, CINZA, ranking_rect, border_radius=25)
        pygame.draw.rect(tela, BRANCO, ranking_rect, 2, border_radius=25)
        ranking_text = fonte_media.render("RANKING", True, BRANCO)
        tela.blit(ranking_text, (ranking_rect.centerx - ranking_text.get_width() // 2,
                                ranking_rect.centery - ranking_text.get_height() // 2))
        if ranking_rect.collidepoint(mouse) and mouse_clicou:
            mostrar_ranking()

        # Botão Sair
        sair_rect = pygame.Rect(largura // 2 - 100, 440, 200, 50)
        pygame.draw.rect(tela, CINZA, sair_rect, border_radius=25)
        pygame.draw.rect(tela, BRANCO, sair_rect, 2, border_radius=25)
        sair_text = fonte_media.render("SAIR", True, BRANCO)
        tela.blit(sair_text, (sair_rect.centerx - sair_text.get_width() // 2,
                             sair_rect.centery - sair_text.get_height() // 2))
        if sair_rect.collidepoint(mouse) and mouse_clicou:
            pygame.quit()
            exit()

        pygame.display.flip()
        clock.tick(fps)

def mostrar_ranking():
    # Carrega fundo animado e ranking
    fundo = carregar_sprite_redimensionado("fundo_pista.png", largura, altura)
    fundo_y = 0
    ranking = carregar_ranking()
    scroll_idx = 0

    # Configuração visual do pódio estilo Kahoot
    podio_width = 420
    podio_height = 210
    base_x = largura // 2 - podio_width // 2
    base_y = 190
    col_width = podio_width // 3
    col_heights = [110, 180, 90]
    cores_kahoot = [(108, 183, 237), (255, 202, 40), (253, 114, 114)]

    # Área visível da lista após o pódio
    lista_y_ini = base_y + podio_height + 30
    lista_y_fim = 550 - 50  # Reserva espaço para botão voltar
    lista_espaco_disp = lista_y_fim - lista_y_ini
    linhas_visiveis = lista_espaco_disp // 34

    while True:
        # Fundo animado
        fundo_y += 2
        if fundo_y >= altura:
            fundo_y = 0
        tela.blit(fundo, (0, fundo_y - altura))
        tela.blit(fundo, (0, fundo_y))

        # Sobreposição preta translúcida
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        tela.blit(overlay, (0, 0))

        # Título
        titulo = fonte_grande.render("TOP JOGADORES", True, AMARELO)
        tela.blit(titulo, (largura // 2 - titulo.get_width() // 2, 50))

        if not ranking:
            texto_vazio = fonte.render("Nenhum recorde ainda!", True, BRANCO)
            tela.blit(texto_vazio, (largura // 2 - texto_vazio.get_width() // 2, 200))
        else:
            # --- Desenha pódio estilizado ---
            for idx in range(3):
                px = base_x + idx * col_width
                ph = col_heights[idx]
                py = base_y + (podio_height - ph)
                pygame.draw.rect(tela, cores_kahoot[idx], (px+15, py, col_width-30, ph), border_radius=14)
                pygame.draw.rect(tela, PRETO, (px+15, py, col_width-30, ph), 3, border_radius=14)
                if idx < len(ranking):
                    pos_index = [1, 0, 2][idx] if len(ranking) > 2 else idx
                    item = ranking[pos_index]
                    # Medalha e número
                    medal_y = py - 38
                    medal_x = px + col_width // 2
                    cor_medalha = [PRATA, OURO, BRONZE][idx]
                    pygame.draw.circle(tela, cor_medalha, (medal_x, medal_y), 24)
                    pygame.draw.circle(tela, PRETO, (medal_x, medal_y), 24, 3)
                    pos_num = [2, 1, 3][idx]
                    num = fonte_grande.render(str(pos_num), True, PRETO)
                    tela.blit(num, (medal_x - num.get_width() // 2, medal_y - num.get_height() // 2))
                    # Nome centralizado e ajustado
                    nome_font_size = 26
                    nome_fonte = pygame.font.SysFont('Arial', nome_font_size, bold=True)
                    nome = item['nome']
                    nome_render = nome_fonte.render(nome, True, BRANCO)
                    while nome_render.get_width() > col_width-34 and nome_font_size > 16:
                        nome_font_size -= 2
                        nome_fonte = pygame.font.SysFont('Arial', nome_font_size, bold=True)
                        nome_render = nome_fonte.render(nome, True, BRANCO)
                    nome_y = py + 15 + (ph // 2 - nome_render.get_height()) // 2
                    tela.blit(nome_render, (medal_x - nome_render.get_width() // 2, nome_y))
                    pts = fonte.render(f"{item['pontos']} pts", True, BRANCO)
                    pts_y = nome_y + nome_render.get_height() + 5
                    tela.blit(pts, (medal_x - pts.get_width() // 2, pts_y))

            # --- Lista com rolagem dinâmica ---
            total = max(0, len(ranking) - 3)
            max_scroll = max(0, total - linhas_visiveis)
            scroll_idx = max(0, min(scroll_idx, max_scroll))

            lista_y = lista_y_ini
            if total > 0:
                # Exibe apenas as linhas visíveis (rolando se necessário)
                for i, item in enumerate(ranking[3+scroll_idx:3+scroll_idx+linhas_visiveis], start=4+scroll_idx):
                    texto = fonte.render(f"{i}º {item['nome']} - {item['pontos']} pts", True, BRANCO)
                    tela.blit(texto, (largura // 2 - texto.get_width() // 2, lista_y))
                    lista_y += 34

            # --- Barra de rolagem se necessário ---
            if total > linhas_visiveis:
                barra_x = largura - 55
                barra_y = lista_y_ini
                barra_alt = linhas_visiveis * 34 - 8
                pygame.draw.rect(tela, (100,100,100), (barra_x, barra_y, 12, barra_alt), border_radius=8)
                if max_scroll > 0:
                    pos_barra = int((scroll_idx / max_scroll) * (barra_alt - 32))
                else:
                    pos_barra = 0
                pygame.draw.rect(tela, AMARELO, (barra_x, barra_y + pos_barra, 12, 32), border_radius=8)

        # Eventos (fecha tela, rola ranking com setas ou scroll, volta ao menu)
        mouse_clicou = False
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicou = True
                if evento.button == 4:   # scroll up
                    scroll_idx = max(0, scroll_idx - 1)
                elif evento.button == 5: # scroll down
                    scroll_idx = min(max_scroll, scroll_idx + 1)
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    scroll_idx = max(0, scroll_idx - 1)
                elif evento.key == pygame.K_DOWN:
                    scroll_idx = min(max_scroll, scroll_idx + 1)

        # Botão Voltar
        voltar_rect = pygame.Rect(largura // 2 - 100, 550, 200, 40)
        pygame.draw.rect(tela, AMARELO, voltar_rect, border_radius=20)
        pygame.draw.rect(tela, BRANCO, voltar_rect, 2, border_radius=20)
        voltar_text = fonte.render("VOLTAR", True, PRETO)
        tela.blit(voltar_text, (voltar_rect.centerx - voltar_text.get_width() // 2,
                               voltar_rect.centery - voltar_text.get_height() // 2))
        if voltar_rect.collidepoint(pygame.mouse.get_pos()) and mouse_clicou:
            return
        pygame.display.flip()
        clock.tick(fps)

def jogo(nome_jogador):
    # Inicialização do cenário, sprites e variáveis principais do jogo
    fundo = carregar_sprite_redimensionado("fundo_pista.png", largura, altura)
    fundo_y = 0
    kombi_img = carregar_sprite_redimensionado("kombi.png", 100, 110)
    moeda_ouro = carregar_sprite_redimensionado("mouro.png", 40, 40)
    moeda_prata = carregar_sprite_redimensionado("mprata.png", 40, 40)
    moeda_bronze = carregar_sprite_redimensionado("mbronze.png", 40, 40)
    heart_img = carregar_sprite_redimensionado("heart.png", 30, 30)
    turbo_img = carregar_sprite_redimensionado("turbo.png", 40, 40)
    combustivel_display_img = carregar_sprite_redimensionado("fuel.png", 30, 30)
    combustivel_pickup_img = carregar_sprite_redimensionado("fuel.png", 40, 40)
    tempo_img = carregar_sprite_redimensionado("clock.png", 30, 30)
    obstaculo_imgs = [
        carregar_sprite_redimensionado("carro1.png", 100, 110),
        carregar_sprite_redimensionado("carro2.png", 100, 110)
    ]
    # Variáveis do player e do jogo
    carro_x = largura // 2 - kombi_img.get_width() // 2
    carro_y = altura - 120
    vel_carro = 7
    vidas = 3
    vel_base = 5
    vel_estrada = vel_base
    combustivel = 100
    pontos = 0
    turbo = 0
    tempo_inicio = pygame.time.get_ticks()
    nivel_dificuldade = 1
    obstaculos, moedas, pickups = [], [], []

    # Controle do turbo
    turbo_ativo = False
    tempo_turbo_ativo = 0
    duracao_turbo = som_uso_turbo.get_length() if som_uso_turbo else 1.0  # Segundos

    # Marcas de pneu para frenagem
    marcas_pneu = []

    # Funções internas para gerar obstáculos, moedas e pickups sem sobreposição
    def criar_obstaculo():
        sprite = random.choice(obstaculo_imgs)
        max_tentativas = 10
        for _ in range(max_tentativas):
            x = random.randint(PISTA_X_MIN, PISTA_X_MAX - sprite.get_width())
            rect = sprite.get_rect(topleft=(x, -100))
            if not colisao_com_lista(rect, obstaculos + moedas + pickups, margem=15):
                obstaculos.append((sprite, rect))
                return

    def criar_moeda():
        tipo = random.choice(["bronze", "prata", "ouro"])
        max_tentativas = 10
        for _ in range(max_tentativas):
            x = random.randint(PISTA_X_MIN, PISTA_X_MAX - 40)
            rect = pygame.Rect(x, -60, 40, 40)
            if not colisao_com_lista(rect, obstaculos + moedas + pickups, margem=15):
                moedas.append((tipo, rect))
                return

    def criar_pickup(tipo):
        max_tentativas = 10
        for _ in range(max_tentativas):
            x = random.randint(PISTA_X_MIN, PISTA_X_MAX - 40)
            rect = pygame.Rect(x, -60, 40, 40)
            if not colisao_com_lista(rect, obstaculos + moedas + pickups, margem=15):
                pickups.append((tipo, rect))
                return

    # Timers de criação de itens
    tempo_obst = tempo_moeda = tempo_pickup_turbo = tempo_pickup_combustivel = 0
    rodando = True
    if musica_fundo:
        pygame.mixer.music.load(musica_fundo)
        pygame.mixer.music.play(-1)
    while rodando:
        # Dificuldade dinâmica por pontos
        novo_nivel = pontos // 200 + 1
        if novo_nivel > nivel_dificuldade:
            nivel_dificuldade = novo_nivel
            vel_base = 5 + (nivel_dificuldade - 1) * 0.5
            if not turbo_ativo:
                vel_estrada = vel_base
        tempo_atual_segundos = (pygame.time.get_ticks() - tempo_inicio) // 1000
        minutos = tempo_atual_segundos // 60
        segundos = tempo_atual_segundos % 60
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
        teclas = pygame.key.get_pressed()
        # Movimentação lateral
        if teclas[pygame.K_LEFT] and carro_x > PISTA_X_MIN:
            carro_x -= vel_carro
        if teclas[pygame.K_RIGHT] and carro_x < PISTA_X_MAX - kombi_img.get_width():
            carro_x += vel_carro

        # Ativa turbo
        if teclas[pygame.K_SPACE] and turbo > 0 and not turbo_ativo:
            turbo_ativo = True
            tempo_turbo_ativo = pygame.time.get_ticks()
            turbo -= 1
            vel_estrada = vel_base + 5
            if som_uso_turbo:
                som_uso_turbo.play()
        if turbo_ativo:
            if (pygame.time.get_ticks() - tempo_turbo_ativo) / 1000 >= duracao_turbo:
                turbo_ativo = False
                vel_estrada = vel_base

        # Frenagem com marcas de pneu
        freando = False
        if teclas[pygame.K_DOWN]:
            vel_estrada = max(vel_base - 2, 1)
            freando = True
            largura_pneu = 7
            altura_pneu = 25
            x1 = carro_x + kombi_img.get_width() // 4 - largura_pneu // 2
            x2 = carro_x + 3 * kombi_img.get_width() // 4 - largura_pneu // 2
            y_pneu = carro_y + kombi_img.get_height() - altura_pneu
            marcas_pneu.append(((x1, y_pneu), (largura_pneu, altura_pneu)))
            marcas_pneu.append(((x2, y_pneu), (largura_pneu, altura_pneu)))
            if len(marcas_pneu) > 40:
                marcas_pneu = marcas_pneu[-40:]
        elif not turbo_ativo:
            vel_estrada = vel_base

        # Consumo de combustível e checagem de game over
        combustivel -= 0.03
        if combustivel <= 0 or vidas <= 0:
            rodando = False

        # Move fundo animado
        fundo_y += vel_estrada
        if fundo_y >= altura:
            fundo_y = 0

        # Criação de obstáculos, moedas e pickups com timers
        tempo_obst += 1
        tempo_moeda += 1
        tempo_pickup_turbo += 1
        tempo_pickup_combustivel += 1
        if tempo_obst > 50 - (nivel_dificuldade * 5):
            criar_obstaculo()
            tempo_obst = 0
        if tempo_moeda > 80:
            criar_moeda()
            tempo_moeda = 0
        if tempo_pickup_turbo > 300:
            criar_pickup("turbo")
            tempo_pickup_turbo = 0
        if combustivel < 30 and tempo_pickup_combustivel > 100:
            if random.random() < 0.2:
                criar_pickup("combustivel")
                tempo_pickup_combustivel = 0
        elif combustivel < 60 and tempo_pickup_combustivel > 200:
            if random.random() < 0.1:
                criar_pickup("combustivel")
                tempo_pickup_combustivel = 0

        # Move e limpa elementos fora da tela
        obstaculos = [(img, rect.move(0, vel_estrada)) for img, rect in obstaculos if rect.y < altura]
        moedas = [(tipo, rect.move(0, vel_estrada)) for tipo, rect in moedas if rect.y < altura]
        pickups = [(tipo, rect.move(0, vel_estrada)) for tipo, rect in pickups if rect.y < altura]
        # Marcas de pneu descem junto com a pista
        marcas_pneu = [((x, y + vel_estrada), tam) for (x, y), tam in marcas_pneu if y + vel_estrada < altura]

        # Retângulo de colisão do carro
        carro_rect = pygame.Rect(
            carro_x + kombi_img.get_width() * 0.2,
            carro_y + kombi_img.get_height() * 0.15,
            kombi_img.get_width() * 0.6,
            kombi_img.get_height() * 0.7
        )
        # Colisões com obstáculos
        for img, rect in obstaculos[:]:
            obst_rect = pygame.Rect(
                rect.x + rect.width * 0.2,
                rect.y + rect.height * 0.15,
                rect.width * 0.6,
                rect.height * 0.7
            )
            if carro_rect.colliderect(obst_rect):
                obstaculos.remove((img, rect))
                vidas -= 1
                if som_colisao:
                    som_colisao.play()
        # Colisões com moedas
        for tipo, m in moedas[:]:
            moeda_rect = pygame.Rect(
                m.x + m.width * 0.25,
                m.y + m.height * 0.25,
                m.width * 0.5,
                m.height * 0.5
            )
            if carro_rect.colliderect(moeda_rect):
                if tipo == "bronze":
                    pontos += 10
                elif tipo == "prata":
                    pontos += 20
                else:
                    pontos += 30
                moedas.remove((tipo, m))
                if som_coleta_moeda:
                    som_coleta_moeda.play()
        # Colisões com pickups (turbo/combustível)
        for tipo, p in pickups[:]:
            pickup_rect = pygame.Rect(
                p.x + p.width * 0.25,
                p.y + p.height * 0.25,
                p.width * 0.5,
                p.height * 0.5
            )
            if carro_rect.colliderect(pickup_rect):
                if tipo == "turbo":
                    turbo = min(5, turbo + 1)
                    if som_pickup_turbo:
                        som_pickup_turbo.play()
                elif tipo == "combustivel":
                    combustivel = min(100, combustivel + 25)
                    if som_combustivel:
                        som_combustivel.play()
                pickups.remove((tipo, p))

        # --- DESENHO NA TELA ---
        tela.blit(fundo, (0, fundo_y - altura))
        tela.blit(fundo, (0, fundo_y))
        # Desenha marcas de pneu no chão
        for (x, y), (w, h) in marcas_pneu:
            pygame.draw.rect(tela, (40, 40, 40), (x, y, w, h), border_radius=3)
        # Carro principal
        tela.blit(kombi_img, (carro_x, carro_y))
        # Obstáculos
        for img, rect in obstaculos:
            tela.blit(img, rect)
        # Moedas
        for tipo, m in moedas:
            img = moeda_bronze if tipo == "bronze" else moeda_prata if tipo == "prata" else moeda_ouro
            tela.blit(img, m)
        # Pickups
        for tipo, p in pickups:
            if tipo == "turbo":
                tela.blit(turbo_img, p)
            elif tipo == "combustivel":
                tela.blit(combustivel_pickup_img, p)
        # HUDs de informações
        tela.blit(combustivel_display_img, (20, 20))
        texto_comb = fonte.render(f"{int(combustivel)}%", True, BRANCO)
        tela.blit(texto_comb, (60, 25))
        pygame.draw.rect(tela, CINZA, (150, 25, 150, 20), border_radius=10)
        cor_combustivel = VERDE if combustivel > 30 else AMARELO if combustivel > 15 else VERMELHO
        pygame.draw.rect(tela, cor_combustivel, (150, 25, 150 * (combustivel/100), 20), border_radius=10)
        pygame.draw.rect(tela, BRANCO, (150, 25, 150, 20), 2, border_radius=10)
        tela.blit(tempo_img, (20, 60))
        texto_tempo = fonte.render(f"{minutos:02d}:{segundos:02d}", True, BRANCO)
        tela.blit(texto_tempo, (60, 65))
        texto_pontos = fonte.render(f"Pontos: {pontos}", True, BRANCO)
        tela.blit(texto_pontos, (20, 100))
        tela.blit(turbo_img, (20, 130))
        texto_turbo = fonte.render(f"x{turbo}", True, BRANCO)
        tela.blit(texto_turbo, (60, 135))
        texto_dificuldade = fonte.render(f"Nível: {nivel_dificuldade}", True, BRANCO)
        tela.blit(texto_dificuldade, (20, 160))
        for i in range(vidas):
            tela.blit(heart_img, (largura - 40 - i * 35, 20))
        pygame.display.flip()
        clock.tick(fps)
    # Ao terminar jogo, para música e registra pontuação
    if musica_fundo and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    if som_game_over:
        som_game_over.play()
    adicionar_ao_ranking(nome_jogador, pontos)
    tela_final(pontos, nome_jogador)

def tela_final(pontos, nome_jogador):
    # Tela rápida de game over
    fundo = carregar_sprite_redimensionado("fundo_pista.png", largura, altura)
    fundo_y = 0
    tempo_inicio = pygame.time.get_ticks()
    while True:
        tempo_atual = pygame.time.get_ticks() - tempo_inicio
        if tempo_atual > 5000:
            return
        fundo_y += 2
        if fundo_y >= altura:
            fundo_y = 0
        tela.blit(fundo, (0, fundo_y - altura))
        tela.blit(fundo, (0, fundo_y))
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        tela.blit(overlay, (0, 0))
        fim = fonte_grande.render("GAME OVER", True, AMARELO)
        tela.blit(fim, (largura // 2 - fim.get_width() // 2, altura // 2 - 100))
        nome_texto = fonte_media.render(f"Jogador: {nome_jogador}", True, BRANCO)
        tela.blit(nome_texto, (largura // 2 - nome_texto.get_width() // 2, altura // 2 - 30))
        placar = fonte_media.render(f"Pontos: {pontos}", True, BRANCO)
        tela.blit(placar, (largura // 2 - placar.get_width() // 2, altura // 2 + 20))
        continuar = fonte.render("Voltando ao menu em 5 segundos...", True, BRANCO)
        tela.blit(continuar, (largura // 2 - continuar.get_width() // 2, altura // 2 + 100))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            if evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(fps)

def main():
    # Loop principal do jogo (menu->jogo->ranking)
    while True:
        if musica_fundo and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(musica_fundo)
            pygame.mixer.music.play(-1)
        nome_jogador = menu_principal()
        jogo(nome_jogador)

if __name__ == "__main__":
    main()
    pygame.quit()



