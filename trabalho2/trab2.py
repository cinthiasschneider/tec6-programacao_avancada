# Trabalho 2

""""
Objetivos:
    1. Com o mouse, clicar e criar pontos, o algoritmo calcula automaticamente o novo diagrama
    2. Mostrar o gráfico dual do diagrama (Triangulação de Delaunay)
    3. Descrever uma aplicação que ache interessante e que utiliza diagrama de Voronoi, colocar junto no GitHub 
"""

# importando bibliotecas necessárias
import sys, random, math, pygame
import numpy as np
from scipy.spatial import Delaunay
from pygame.locals import QUIT

# inicializando o pygame
pygame.init()
size = (800, 600)
surf = pygame.display.set_mode((size[0], size[1]))
pygame.display.set_caption('Voronoi & Delaunay')

# guardando a posição (x, y) de onde foi clicado
pontos = [] 

# função que desenha a triangulação de Delaunay
def draw_delaunay(surface, lista_pontos):
    # definindo o número mínimo para desenhar a triangulação
    if len(lista_pontos) < 3:
        return

    # extrai as coordenadas em um array 
    coords = np.array([p[0] for p in lista_pontos])
    
    # calcula a triangulação usando o array de coordenadas acima
    tri = Delaunay(coords)
    
    # desenha as arestas dos triângulos
    # para cada triângulo em uma lista de índices de pontos (simplices) que formam um triângulo => simplices vem da biblioteca
    for triangulo in tri.simplices:
        a, b, c = triangulo # vértices de um triângulo
        
        # linha entre A e B
        pygame.draw.line(surface, (255, 255, 255), tuple(coords[a]), tuple(coords[b]), 1)
        # linha ente B e C
        pygame.draw.line(surface, (255, 255, 255), tuple(coords[b]), tuple(coords[c]), 1)
        # linha entre C e A
        pygame.draw.line(surface, (255, 255, 255), tuple(coords[c]), tuple(coords[a]), 1)


# loop principal
while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            posx, posy = pygame.mouse.get_pos()
            
            # a cada clique, adiciona um ponto, com uma cor aleatória 
            # para a célula de Voronoi criada baseando-se na localização desse ponto
            new_point = [[posx, posy], (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))]
            pontos.append(new_point)

            # recalcula as células e desenha novamente todo o diagrama
            surf.fill((100, 100, 100)) # limpa a tela antes de desenhar as regiões de novo
            
            # usando Minkowski distance para que o cálculo continue o mesmo
            for x, y in [(x, y) for x in range(size[0]) for y in range(size[1])]:
                # acha o ponto i que minimiza a distância para a coordenada (x, y)
                min_distance_color = min([(math.sqrt((x - i[0][0])**2 + (y - i[0][1])**2), i[1]) 
                                          for i in pontos])[1]
                surf.set_at((x, y), min_distance_color)
            
            # desenha a triangulação de Delaunay encima usando os pontos
            draw_delaunay(surf, pontos)
            
            # desenha os pontos para torná-los visíveis (se não fizer isso, eles ficam embaixo das células e desaparecem)
            for p in pontos:
                pygame.draw.circle(surf, (0, 0, 0), p[0], 5, 1) # volta preta
                pygame.draw.circle(surf, p[1], p[0], 3) # cor do ponto

        # fim da execução
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    
    pygame.display.update() 