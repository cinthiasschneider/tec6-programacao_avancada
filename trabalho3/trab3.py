# Trabalho 3
""""
Objetivos:
    Escolher um algoritmo de envoltória convexa => QuickHull (padrão SciPy)
    1. Com o mouse clicar e criar pontos, o algoritmo calcula automaticamente a nova envoltória.
    2. Faça uma função que gera pontos aleatórios.
    3. Faça uma função que cria formas geométricas básicas: triângulo, retângulo, etc.
    obs.: permita escolher o número de pontos que serão gerados
    Gráficos:
        - custo computacional
        - número de pontos dentro da região e na envoltória, pense em mais alguma informação sobre o conjunto e a solução
        - existe diferença de custo computacional dependendo da distribuição de pontos?
        - pense sobre o desempenho do algoritmo e tente montar algum gráfico que demonstre o comportamento
"""
# importando as bibliotecas necessárias
from scipy.spatial import ConvexHull
import numpy as np
import random, csv, pygame, time, sys, os

# inicializando o pygane
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Envoltória Convexa")

# definindo as cores RBG
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0) # pontos na envoltória
AZUL = (0, 0, 255)     # pontos internos
VERDE = (0, 200, 0)    # arestas da envoltória

# configurações dos pontos
RAIO_PONTO = 4
n_pontos_inicial = 20 # variável de n de pontos padrão

# variáveis de logging para analisar
pontos = []
envoltoria_hull = None 
pontos_na_envoltoria = [] 
tempo_computacao = 0.0 

# função que gera pontos aleatórios
def gerar_pontos_aleatorios(n):
    return [np.array([random.randint(50, WIDTH - 50), 
                      random.randint(50, HEIGHT - 50)]) 
            for _ in range(n)]

# função auxiliar para verificar se o ponto p está dentro do triângulo (v1, v2, v3) usando o teste de mesma orientação
def is_inside_triangle(p, v1, v2, v3):
    p, v1, v2, v3 = p.tolist(), v1.tolist(), v2.tolist(), v3.tolist()
    def sign(p1, p2, p3):
        # produto vetorial
        return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
    d1 = sign(v1, v2, p)
    d2 = sign(v2, v3, p)
    d3 = sign(v3, v1, p)
    # verifica se há sinais opostos (indica que está fora da forma)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    # se todos os sinais forem iguais ou zero (está dentro ou na borda), retorna true
    return not (has_neg and has_pos)

# função que gera a geometria escolhida (triângulo ou retângulo)
def gerar_forma_geometria(tipo_forma, n_total):
    
    pontos_forma = []
    vertices = []
    V = 0 # número de vértices
    
    # definindo padding mínimo para que caiba na tela
    min_padding = 80
    
    # gera centro aleatório
    centro_x = random.randint(min_padding, WIDTH - min_padding)
    centro_y = random.randint(min_padding, HEIGHT - min_padding)
    
    # raio máximo baseado na menor distância da borda
    max_radius = min(centro_x, WIDTH - centro_x, centro_y, HEIGHT - centro_y)
    
    if tipo_forma == "triangulo":
        
        # gera um raio e um ângulo inicial aleatório para rotação
        raio = random.randint(30, max_radius)
        angulo_inicial = random.uniform(0, 2 * np.pi) 
        # gera 3 vértices espaçados angularmente com rotação aleatória
        for i in range(3):
            angulo = angulo_inicial + i * 2 * np.pi / 3
            x = centro_x + raio * np.cos(angulo)
            y = centro_y + raio * np.sin(angulo)
            vertices.append(np.array([int(x), int(y)]))
        V = 3
        
    elif tipo_forma == "retangulo":
        # define um tamanho aleatório para o retângulo
        largura = random.randint(60, 2 * max_radius)
        altura = random.randint(60, 2 * max_radius)
        # define os limites do retângulo
        x_min = centro_x - largura // 2
        x_max = centro_x + largura // 2
        y_min = centro_y - altura // 2
        y_max = centro_y + altura // 2
        vertices = [
            np.array([x_min, y_min]),
            np.array([x_max, y_min]),
            np.array([x_max, y_max]),
            np.array([x_min, y_max])
        ]
        V = 4
    
    # gerando os pontos
    if n_total < V:
        # se n é muito pequeno, retorna apenas os vértices iniciais
        return vertices[:n_total]
    # adiciona os vértices ao conjunto de pontos
    pontos_forma.extend(vertices)
    
    # usando bounding box para otimizar a geração de pontos internos 
    x_min_bb, x_max_bb = min(v[0] for v in vertices), max(v[0] for v in vertices)
    y_min_bb, y_max_bb = min(v[1] for v in vertices), max(v[1] for v in vertices)
    
    pontos_internos_gerados = 0
    
    while pontos_internos_gerados < n_total - V:
        # gerando ponto aleatório dentro do interior do Bounding Box
        x = random.randint(int(x_min_bb) + 1, int(x_max_bb) - 1)
        y = random.randint(int(y_min_bb) + 1, int(y_max_bb) - 1)
        p = np.array([x, y])
        
        is_inside = False
        if tipo_forma == "triangulo":
            is_inside = is_inside_triangle(p, vertices[0], vertices[1], vertices[2])
        elif tipo_forma == "retangulo":
            # bounding box já verifica o retângulo
            is_inside = True
        if is_inside:
            pontos_forma.append(p)
            pontos_internos_gerados += 1
            
    return pontos_forma

# função que calcula a envoltória convexa
def calcular_envoltoria(pontos_array):
    global envoltoria_convexa, pontos_na_envoltoria, tempo_computacao
    if len(pontos_array) < 3:
        envoltoria_convexa = None
        pontos_na_envoltoria = []
        tempo_computacao = 0.0
        return
    inicio = time.perf_counter() # iniciando o relógio
    try:
        # usa o algoritmo ConvexHull (Quickhull) da biblioteca SciPy
        envoltoria_convexa = ConvexHull(pontos_array)
        pontos_na_envoltoria = pontos_array[envoltoria_convexa.vertices]
    except Exception: # lidando com casos degenerados
        envoltoria_convexa = None
        pontos_na_envoltoria = []

    fim = time.perf_counter()
    tempo_computacao = fim - inicio

# função que desenha os pontos na tela
def desenhar_pontos(surface, lista_pontos):
    """ Desenha todos os pontos. """
    for p in lista_pontos:
        # Testa se o ponto é um dos vértices da envoltória
        is_on_hull = any(np.array_equal(p, hull_p) for hull_p in pontos_na_envoltoria)
        
        if is_on_hull:
            cor = VERMELHO 
        else:
            cor = AZUL 
        pygame.draw.circle(surface, cor, (int(p[0]), int(p[1])), RAIO_PONTO)
        pygame.draw.circle(surface, PRETO, (int(p[0]), int(p[1])), RAIO_PONTO, 1)

# função que desenha as arestas da envoltória
def desenhar_envoltoria(surface, hull_obj, pontos_array):
    if hull_obj is None:
        return
    for simplex in hull_obj.simplices:
        p1 = pontos_array[simplex[0]]
        p2 = pontos_array[simplex[1]]
        pygame.draw.line(surface, VERDE, (p1[0], p1[1]), (p2[0], p2[1]), 2)

# função para exibir informações e métricas na execução
def desenhar_info(surface):
    font = pygame.font.Font(None, 24)
    n_total = len(pontos)
    n_na_hull = len(pontos_na_envoltoria)
    n_internos = n_total - n_na_hull
    info = [
        f"Total de Pontos: {n_total}",
        f"Pontos na Envoltória: {n_na_hull}",
        f"Pontos internos à Envoltória: {n_internos}",
        f"Custo Computacional: {tempo_computacao*1000:.4f} ms"
    ]
    y_offset = 10
    for linha in info:
        texto = font.render(linha, True, PRETO)
        surface.blit(texto, (10, y_offset))
        y_offset += 25
    
    font_small = pygame.font.Font(None, 20)
    instrucoes = f"Modo: {modo} | Pressione 'R' para Resetar Pontos."
    inst_texto = font_small.render(instrucoes, True, PRETO)
    surface.blit(inst_texto, (WIDTH - inst_texto.get_width() - 10, 10))


# função para salvar o log
log_file = "log_trab3.csv"
def salvar_log(modo_execucao, num_pontos, tempo_ms):  
    file_exists = os.path.isfile(log_file)
    try:
        with open(log_file, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Modo", "NumPontos", "PontosNaEnvoltoria", "Tempo_ms"])
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                modo_execucao, 
                num_pontos, 
                len(pontos_na_envoltoria), 
                tempo_ms
            ])
            
        print(f"Log salvo com sucesso em: {os.path.abspath(log_file)}. N={num_pontos}, Tempo={tempo_ms:.4f} ms")
    except Exception as e:
        print(f"ERRO CRÍTICO ao salvar o log.Erro: {e}")


# seleção da opção
def escolher_opcao():
    global n_pontos_inicial  # global para permitir modificação
    
    print("\n") # dando espaço para organizar
    while True:
        try:
            print("Escolha uma opção:")
            print("1 - Modo Interativo (Clicar e criar pontos)")
            print("2 - Pontos Aleatórios (Definir N)")
            print("3 - Forma Geométrica (Definir N)")
            opcao = input("Opção (1/2/3): ")
            
            if opcao not in ("1", "2", "3"):
                raise ValueError
            
            if opcao in ("2", "3"):
                n_str = input(f"Digite o número de pontos (padrão: {n_pontos_inicial}): ")
                if n_str:
                    n = int(n_str)
                    if n < 3:
                        print("É necessário pelo menos 3 pontos para geração da envoltória convexa!")
                        continue
                    n_pontos_inicial = n 
                    
            if opcao == "3":
                forma = input("Digite a forma (triangulo/retangulo): ").lower()
                if forma not in ("triangulo", "retangulo"):
                    print("Forma inválida. Usando retângulo.")
                    forma = "retangulo"
                return opcao, forma
                
            return opcao, None
        
        except ValueError:
            print("Entrada inválida ou número de pontos inválido!")
        except Exception as e:
            print(f"Erro: {e}. Tente novamente.")

# chamando a função e definindo o modo e forma selecionados => se não ficar no global dá erro aqui!
modo, forma_selecionada = escolher_opcao()

# preenchendo os pontos iniciais
if modo == "2":
    print(f"Iniciando com {n_pontos_inicial} pontos aleatórios.")
    pontos = gerar_pontos_aleatorios(n_pontos_inicial)
    calcular_envoltoria(np.array(pontos))
    if tempo_computacao > 0:
        salvar_log(modo, len(pontos), tempo_computacao * 1000)
elif modo == "3":
    print(f"Iniciando com {n_pontos_inicial} pontos em formato de {forma_selecionada}.")
    pontos = gerar_forma_geometria(forma_selecionada, n_pontos_inicial)
    if len(pontos) >= 3:
        calcular_envoltoria(np.array(pontos))
        if tempo_computacao > 0:
            salvar_log(modo, len(pontos), tempo_computacao * 1000)
    else:
        print("Aviso: Número insuficiente de pontos para calcular a envoltória convexa!")
else:
    print("Clique para adicionar pontos!")

    
# loop principal
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # gerencia a escolha pela opção 1
        if modo == "1" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            novo_ponto = np.array([x, y])
            pontos.append(novo_ponto)
            
            calcular_envoltoria(np.array(pontos))
            
            if tempo_computacao > 0:
                salvar_log(modo, len(pontos), tempo_computacao * 1000)
    screen.fill(BRANCO) # atualiza o display
    if pontos:
        pontos_array = np.array(pontos) 
        desenhar_envoltoria(screen, envoltoria_convexa, pontos_array)
        desenhar_pontos(screen, pontos)
    desenhar_info(screen)
    clock.tick(60) 
    pygame.display.flip()
pygame.quit()
sys.exit()