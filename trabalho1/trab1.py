# trabalho 1 => gear up!
"""
objetivos:
    1. o programa deve mostrar polígonos 2D e permitir que eles sejam alterados durante a execução
    2. definir cores por ponto, linha e área
    3. permitir clicar e encontrar a geometria onde foi clicado
    4. gerar um arquivo logando: 
        4.1. todo o percurso do mouse na tela 
        4.2. quantos cliques
        4.3. quais objetos clicou e em que momento
        4.4. tempo de execução
"""

# importando as bibliotecas necessárias
import pygame
import sys
import random
import time
import csv
import math

# inicializando pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gear Up!")

# definindo as cores RGB
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
ROXO = (160, 32, 240)
VERMELHO_SELECIONADO = (255, 0, 0) # ao selecionar, a cor muda para vermelho
AZUL_QUADRADO = (0, 0, 255) # quadrados serão azuis para diferenciar
VERDE_PENTAGONO = (0, 255, 0) # pentágonos serão verdes para diferenciar
AMARELO_TRIANGULO = (255, 255, 0) # triângulos serão amarelos para diferenciar

# configurações dos pontos
N_PONTOS = 5
RAIO_PONTO = 6

# classe para representar um ponto
class Ponto:
    def __init__(self, x, y, cor):
        self.pos = pygame.Vector2(x, y)
        self.raio = RAIO_PONTO
        self.cor = cor
        self.selecionado = False

    # desenha o ponto na tela
    def desenhar(self, surface):
        cor_desenho = ROXO if self.selecionado else self.cor # se clicado, muda de cor para roxo
        pygame.draw.circle(surface, cor_desenho, (int(self.pos.x), int(self.pos.y)), self.raio)
        pygame.draw.circle(surface, PRETO, (int(self.pos.x), int(self.pos.y)), self.raio, 2)

    # checa se foi clicado
    def checar_clique(self, pos_mouse):
        dist = self.pos.distance_to(pygame.Vector2(pos_mouse))
        return dist <= self.raio

# classe para representar polígonos (quadrados, pentágonos)
class Poligono:
    def __init__(self, pontos, cor, tipo): 
        self.pontos = pontos
        self.cor = cor
        self.selecionado = False
        self.tipo = tipo

    # desenha os polígonos
    def desenhar(self, surface):
        lista_pos = [p.pos for p in self.pontos]
        if len(lista_pos) >= 3:
            cor_desenho = VERMELHO_SELECIONADO if self.selecionado else self.cor
            pygame.draw.polygon(surface, cor_desenho, lista_pos, 2)

    # checa cliques considerando a posição do mouse
    def checar_clique(self, pos_mouse):
        pontos_poly = [p.pos for p in self.pontos]
        if len(pontos_poly) < 3:
            return False

        for i in range(1, len(pontos_poly) - 1):
            if ponto_dentro_triangulo(pygame.Vector2(pos_mouse), pontos_poly[0], pontos_poly[i], pontos_poly[i+1]):
                return True
        return False

# classe para representar triângulos
class Triangulo:
    def __init__(self, p1, p2, p3, cor):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.cor = cor
        self.selecionado = False
        self.tipo = "Triângulo"

    # desenha os triângulos
    def desenhar(self, surface):
        cor_desenho = VERMELHO_SELECIONADO if self.selecionado else self.cor
        pygame.draw.polygon(surface, cor_desenho, [self.p1.pos, self.p2.pos, self.p3.pos], 2)
        
    # checa cliques considerando a posição do mouse
    def checar_clique(self, pos_mouse):
        return ponto_dentro_triangulo(pygame.Vector2(pos_mouse), self.p1.pos, self.p2.pos, self.p3.pos)

# função para salvar o log
def salvar_log():
    fim = time.time()
    tempo_total = fim - inicio
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Evento", "Detalhes", "Tempo"])
        for pos, t in caminho_mouse:
            writer.writerow(["Caminho do mouse", pos, t])
        for pos, obj, t in cliques:
            writer.writerow(["Click", f"{pos}, Objeto: {obj}", t])
        writer.writerow(["Execução", f"Tempo total: {tempo_total:.2f} segundos", fim])

# função para verificar se a localização do mouse está dentro de um triângulo (detecta clique nos polígonos!)
def ponto_dentro_triangulo(p, a, b, c):
    def sign(p1, p2, p3):
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)

# criando os pontos
pontos = [Ponto(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50),
                 (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)))
          for _ in range(N_PONTOS)]

# criando triângulos, quadrados e pentágonos
triangulos = []
for i in range(len(pontos)):
    for j in range(i + 1, len(pontos)):
        for k in range(j + 1, len(pontos)):
            triangulos.append(Triangulo(pontos[i], pontos[j], pontos[k], AMARELO_TRIANGULO))

quadrado = Poligono([pontos[0], pontos[1], pontos[2], pontos[3]], AZUL_QUADRADO, "Quadrado")
pentagono = Poligono(pontos, VERDE_PENTAGONO, "Pentágono")
poligonos = [quadrado, pentagono]

# guarda as áreas clicadas
selecionado = None
# guarda os pontos que foram arrastados
ponto_arrastado = None

# variáveis de logging para analisar
inicio = time.time()
caminho_mouse = []
cliques = []
log_file = "log_gearup.csv"

# loop de execução principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            salvar_log()
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            selecionado = None

            # checa cliques nos polígonos
            for poly in poligonos:
                if poly.checar_clique(event.pos):
                    selecionado = poly
                    selecionado.selecionado = True
                    cliques.append((event.pos, poly.tipo, time.time() - inicio))
                    break
            
            # se nenhum polígono foi clicado, checa os triângulos
            if not selecionado:
                for tri in triangulos:
                    if tri.checar_clique(event.pos):
                        selecionado = tri
                        selecionado.selecionado = True
                        cliques.append((event.pos, tri.tipo, time.time() - inicio))
                        break

            # se nada foi clicado, checa os pontos
            if not selecionado:
                for p in pontos:
                    if p.checar_clique(event.pos):
                        ponto_arrastado = p
                        p.selecionado = True
                        cliques.append((event.pos, f"Ponto {pontos.index(p)}", time.time() - inicio))
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if ponto_arrastado:
                ponto_arrastado.selecionado = False
            ponto_arrastado = None
            if selecionado:
                selecionado.selecionado = False

        elif event.type == pygame.MOUSEMOTION:
            caminho_mouse.append((event.pos, time.time() - inicio))
            if ponto_arrastado:
                ponto_arrastado.pos.x = event.pos[0]
                ponto_arrastado.pos.y = event.pos[1]

    # renderização da execução
    screen.fill(BRANCO)

    # desenha todos os triângulos
    for tri in triangulos:
        tri.desenhar(screen)

    # desenha polígonos
    for poly in poligonos:
        poly.desenhar(screen)
    
    # desenha pontos
    for p in pontos:
        p.desenhar(screen)

    pygame.display.flip()