# Trabalho 4: Soma de Minkowski

""""
Objetivos:
    Implementar um algoritmo de soma de Minkowski
    1. Criar alguns polígonos (mouse e procedural) => obstáculos e robô
    2. Usar como entrada para o seu algoritmo a soma de Minkowski
    3. Mostrar os polígonos de entrada e os de saída
    Gráficos:
        - crescimento conforme mais pontos são adicionados
        - pense sobre o desempenho do algoritmo e tente montar algum gráfico que demonstra o comportamento
        - tabela de distância mínima entre cada par de polígonos após o algoritmo gerar a soma
"""
# importando as bibliotecas necessárias
from scipy.spatial import ConvexHull
import numpy as np
import random, csv, pygame, time, sys, os
from math import pi, cos, sin 

# inicializando o pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soma de Minkowski")
FONT = pygame.font.Font(None, 24)
TAMANHO_VISUALIZACAO = 350 
CENTRO_X = WIDTH / 2
CENTRO_Y = HEIGHT / 2

# definindo constantes
NUM_OBSTACLES = 3
RAIO_PONTO_MOUSE = 4

# definindo as cores RBG
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
AZUL = (0, 0, 255)        # cor do robô (p1)
VERDE = (0, 150, 0)       # reflexão do robô (-p1)
LARANJA = (255, 100, 0)   # obstáculos
VERMELHO_FORTE = (200, 0, 0) # configuration space obstacle
CINZA = (150, 150, 150)  # linhas e informações

# variáveis de controle
MODO_EXECUCAO = None
FORMA_P1_INICIAL = 5 # número de vértices inicial para o robô => modo aleatório
VERTICES_OBSTACULOS = [6, 4, 7] # número de vértices inicial para os obstáculos => modo aleatório

# função para salvar log
log_file = "log_minkowski.csv"
def salvar_log(modo_execucao, num_vertices_p1, num_vertices_o, num_pontos_soma, tempo_ms):
    file_exists = os.path.isfile(log_file)
    try:
        with open(log_file, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Timestamp", "Modo", "Vertices_P1", "Vertices_O_Max", 
                    "Pontos_Soma_Gerados", "Tempo_Minkowski_ms"
                ])
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                modo_execucao, num_vertices_p1, num_vertices_o, 
                num_pontos_soma, f"{tempo_ms:.4f}"
            ])
    except Exception as e:
        print(f"ERRO CRÍTICO ao salvar o log. Erro: {e}")

# função de reflexão para o robô
def reflection(P_verts):
    if len(P_verts) == 0:
        return P_verts
    return -P_verts

# soma de minkowski p1 + p2
def minkowski_sum(P1_verts, P2_verts):
    pontos_soma = []
    for p1 in P1_verts:
        for p2 in P2_verts:
            pontos_soma.append(p1 + p2)
    pontos_soma_np = np.array(pontos_soma, dtype=float)
    if len(pontos_soma_np) < 3:
        return np.array([]), pontos_soma_np  
    try:
        hull = ConvexHull(pontos_soma_np)
        minkowski_verts = pontos_soma_np[hull.vertices]
        return minkowski_verts, pontos_soma_np
    except Exception:
        return np.array([]), pontos_soma_np

# função para criar polígonos com o mouse
def criar_poligono_mouse_interativo(titulo, cor):
    poligono = []
    desenhando = True
    while desenhando:
        screen.fill(BRANCO)
        # desenhando as instruções
        texto_instrucao = FONT.render(
            f"{titulo}: Clique para adicionar vértices. ENTER para finalizar (min 3 vértices).", 
            True, PRETO
        )
        screen.blit(texto_instrucao, (10, 10))
        # desenhando o polígono ao criar
        for p in poligono:
            pygame.draw.circle(screen, cor, (int(p[0]), int(p[1])), RAIO_PONTO_MOUSE)
        if len(poligono) > 1:
            pygame.draw.lines(screen, cor, True, [(int(p[0]), int(p[1])) for p in poligono], 2)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # adiciona o vértice onde foi clicado
                pos = event.pos
                poligono.append(np.array(pos, dtype=float))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # finaliza o desenho
                if len(poligono) >= 3:
                    desenhando = False
                else:
                    print("AVISO: Polígono deve ter no mínimo 3 vértices.")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print("Criação cancelada.")
                return np.array([])
                
    # centralizando o polígono no ponto (0, 0) para melhorar a visualização => se não definir os polígonos somem no modo aleatório
    if len(poligono) > 0:
        centroide = np.mean(poligono, axis=0)
        return np.array(poligono) - centroide
    return np.array([])

# função de geração aleatória de polígonos 
# gera vértices de um polígono convexo aleatório centralizado em (0, 0)
def gerar_poligono_aleatorio(num_vertices, raio_max=40):
    radii = [random.uniform(10, raio_max) for _ in range(num_vertices)]
    angles = [random.uniform(0, 2 * pi) for _ in range(num_vertices)]
    angles.sort()
    pontos = []
    for r, a in zip(radii, angles):
        x = r * cos(a)
        y = r * sin(a)
        pontos.append([x, y])
    return np.array(pontos, dtype=float)

# função de execução da soma de minkowski => calcula cso e métricas com base nos polígonos de entrada
def executar_minkowski(modo, p1_verts, obstacles_verts):
    # robô
    P1_local = p1_verts
    Obstacles_local = obstacles_verts
    if len(P1_local) < 3:
        print("ERRO: Polígono P1 inválido.")
        return P1_local, reflection(P1_local), [], [], 0.0
    # reflexão
    N_P1_local = reflection(P1_local)
    # m_i = o_i + (-p1) (cso)
    CSOs_local = []
    total_time = 0
    total_pontos_soma = 0
    max_o_verts = 0
    for O_i_verts_local in Obstacles_local:
        if len(O_i_verts_local) < 3:
            print(f"AVISO: Obstáculo ignorado por ter menos de 3 vértices.")
            CSOs_local.append(np.array([]))
            continue   
        start_time = time.perf_counter()
        M_i_verts_local, _ = minkowski_sum(O_i_verts_local, N_P1_local)
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
        total_pontos_soma += len(O_i_verts_local) * len(N_P1_local) # Pontos gerados (N1*N2)
        CSOs_local.append(M_i_verts_local)
        max_o_verts = max(max_o_verts, len(O_i_verts_local))
    tempo_execucao_ms = total_time * 1000
    # salvando o log
    salvar_log(modo, len(P1_local), max_o_verts, total_pontos_soma, tempo_execucao_ms)
    return P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_execucao_ms

# função que desenha o polígono na tela
def desenhar_poligono(superficie, poligono, cor, espessura=2, nome="", preencher=False, cor_borda=PRETO):
    if len(poligono) >= 3:
        pontos_int = [(int(p[0]), int(p[1])) for p in poligono]
        if preencher:
            pygame.draw.polygon(superficie, cor, pontos_int, 0)
            pygame.draw.polygon(superficie, cor_borda, pontos_int, 1)
        else:
            pygame.draw.polygon(superficie, cor, pontos_int, espessura)
        if nome:
            centro = np.mean(poligono, axis=0) 
            texto = FONT.render(nome, True, PRETO)
            superficie.blit(texto, (int(centro[0] - texto.get_width() / 2), int(centro[1] - texto.get_height() / 2)))

# transforma para que o polígono caiba na tela
def transformar_e_desenhar(surface, poligono, cor, nome, target_center, max_size, preencher=False, cor_borda=PRETO):
    if len(poligono) < 3:
        return poligono  
    min_x, min_y = np.min(poligono, axis=0)
    max_x, max_y = np.max(poligono, axis=0)
    largura = max_x - min_x
    altura = max_y - min_y
    escala_x = max_size / largura if largura > 0 else 1
    escala_y = max_size / altura if altura > 0 else 1
    fator_escala = min(escala_x, escala_y) * 0.9 
    poligono_escalado = poligono * fator_escala
    cm_escalado = np.mean(poligono_escalado, axis=0)
    vetor_translacao = np.array(target_center) - cm_escalado
    poligono_final = poligono_escalado + vetor_translacao
    desenhar_poligono(surface, poligono_final, cor, espessura=3, nome=nome, preencher=preencher, cor_borda=cor_borda)
    return poligono_final

# função para exibir as informações e métricas de desempenho
def desenhar_info(surface, n_p1, n_o, n_m_list, tempo_ms, modo):
    n_m_total = sum(n_m_list)
    info = [
        f"Modo: {'Mouse' if modo == '2' else 'Aleatório'}",
        f"P1 (Robô): {n_p1} Vértices",
        f"{NUM_OBSTACLES} Obstáculos O_i: {n_o} Vértices Máx.",
        f"{NUM_OBSTACLES} CSOs M_i: {n_m_total} Vértices Totais",
        f"Custo Computacional Total: {tempo_ms:.4f} ms",
        "Pressione 'R' para Resetar | 'ESC' para sair"
    ]
    y_offset = HEIGHT - 90
    for linha in info:
        texto = FONT.render(linha, True, PRETO)
        surface.blit(texto, (10, y_offset))
        y_offset += 25

# função para escolher a opção (mouse ou procedural)
def escolher_opcao():
    global MODO_EXECUCAO
    while MODO_EXECUCAO is None:
        screen.fill(BRANCO)
        texto_titulo = FONT.render("Selecione o Modo de Execução (Soma de Minkowski)", True, PRETO)
        texto_op1 = FONT.render("1: Modo Aleatório (P1 e Obstáculos gerados automaticamente)", True, AZUL)
        texto_op2 = FONT.render("2: Modo Interativo (Cria P1 e Obstáculos com o Mouse)", True, VERMELHO_FORTE)
        screen.blit(texto_titulo, (CENTRO_X - texto_titulo.get_width()/2, CENTRO_Y - 100))
        screen.blit(texto_op1, (CENTRO_X - texto_op1.get_width()/2, CENTRO_Y))
        screen.blit(texto_op2, (CENTRO_X - texto_op2.get_width()/2, CENTRO_Y + 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    MODO_EXECUCAO = '1'
                    return
                elif event.key == pygame.K_2:
                    MODO_EXECUCAO = '2'
                    return
# chama a função de escolher a opção
escolher_opcao()

# prepara os polígonos iniciais
P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_computacao_ms = np.array([]), np.array([]), [], [], 0.0
if MODO_EXECUCAO == '1':
    print("Iniciando Modo Aleatório...")
    P1_local_init = gerar_poligono_aleatorio(num_vertices=FORMA_P1_INICIAL, raio_max=40)
    Obstacles_local_init = [gerar_poligono_aleatorio(n, raio_max=40) for n in VERTICES_OBSTACULOS]
    P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_computacao_ms = executar_minkowski(MODO_EXECUCAO, P1_local_init, Obstacles_local_init)
elif MODO_EXECUCAO == '2':
    print("Iniciando Modo Interativo (Mouse)...")
    # cria p1
    P1_local_init = criar_poligono_mouse_interativo("Crie o Robô (P1)", AZUL)
    # cria obstáculos
    Obstacles_local_init = []
    for i in range(NUM_OBSTACLES):
        O_i = criar_poligono_mouse_interativo(f"Crie o Obstáculo O{i+1}", LARANJA)
        Obstacles_local_init.append(O_i) 
    # calcula
    P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_computacao_ms = executar_minkowski(MODO_EXECUCAO, P1_local_init, Obstacles_local_init)

# loop principal
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r: # reseta com 'r'
                if MODO_EXECUCAO == '1':
                    # reinicia a geração aleatória
                    P1_local_init = gerar_poligono_aleatorio(num_vertices=FORMA_P1_INICIAL, raio_max=40)
                    Obstacles_local_init = [gerar_poligono_aleatorio(n, raio_max=40) for n in VERTICES_OBSTACULOS]
                    P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_computacao_ms = executar_minkowski(MODO_EXECUCAO, P1_local_init, Obstacles_local_init)
                elif MODO_EXECUCAO == '2':
                    # volta para o modo de criação por mouse
                    P1_local_init = criar_poligono_mouse_interativo("Crie o Robô (P1)", AZUL)
                    Obstacles_local_init = []
                    for i in range(NUM_OBSTACLES):
                        O_i = criar_poligono_mouse_interativo(f"Crie o Obstáculo O{i+1}", LARANJA)
                        Obstacles_local_init.append(O_i)
                    P1_local, N_P1_local, Obstacles_local, CSOs_local, tempo_computacao_ms = executar_minkowski(MODO_EXECUCAO, P1_local_init, Obstacles_local_init)

    screen.fill(BRANCO)
    # desenho de estrutura de layout
    pygame.draw.line(screen, CINZA, (CENTRO_X, 0), (CENTRO_X, HEIGHT - 120), 1)
    pygame.draw.line(screen, CINZA, (0, HEIGHT - 120), (WIDTH, HEIGHT - 120), 1)
    pygame.draw.line(screen, CINZA, (0, CENTRO_Y - 100), (WIDTH, CENTRO_Y - 100), 1)
    
    # robô + reflexão
    ROBOT_AREA_CENTER_Y = (CENTRO_Y - 100) / 2
    ROBOT_MAX_SIZE = 150
    P1_final = transformar_e_desenhar( # robô
        screen, P1_local, AZUL, "P1", 
        target_center=(WIDTH/4 - 60, ROBOT_AREA_CENTER_Y), 
        max_size=ROBOT_MAX_SIZE / 2, preencher=True
    )
    transformar_e_desenhar( # reflexão
        screen, N_P1_local, VERDE, "-P1", 
        target_center=(WIDTH/4 + 60, ROBOT_AREA_CENTER_Y), 
        max_size=ROBOT_MAX_SIZE / 2, preencher=False, cor_borda=VERDE
    )
    # obstáculos => o1, o2, o3
    OBSTACLE_MAX_SIZE = 100
    obstacle_centers = [
        (CENTRO_X + WIDTH / 8, ROBOT_AREA_CENTER_Y), 
        (CENTRO_X + WIDTH / 4, ROBOT_AREA_CENTER_Y), 
        (CENTRO_X + WIDTH * 3 / 8, ROBOT_AREA_CENTER_Y)
    ]
    max_o_verts_count = 0
    for i, O_i in enumerate(Obstacles_local):
        transformar_e_desenhar(
            screen, O_i, LARANJA, f"O{i+1}", 
            target_center=obstacle_centers[i], 
            max_size=OBSTACLE_MAX_SIZE, preencher=True
        )
        max_o_verts_count = max(max_o_verts_count, len(O_i))
    # cso => m1, m2, m3
    CSO_CENTER_Y = CENTRO_Y + 70
    n_m_verts = []
    for i, M_i in enumerate(CSOs_local):
        M_final = transformar_e_desenhar(
            screen, M_i, VERMELHO_FORTE, f"M{i+1}", 
            target_center=(CENTRO_X, CSO_CENTER_Y), 
            max_size=TAMANHO_VISUALIZACAO, preencher=False, cor_borda=VERMELHO_FORTE
        )
        n_m_verts.append(len(M_final) if M_final.ndim > 1 else 0)
    # exibindo as informações
    desenhar_info(
        screen, 
        len(P1_local), 
        max_o_verts_count, 
        n_m_verts, 
        tempo_computacao_ms,
        MODO_EXECUCAO
    )
    clock.tick(60) 
    pygame.display.flip()
pygame.quit()
sys.exit()