# importando bibliotecas necessárias
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
import ast # biblioteca que converte a string de tupla (x, y) em uma tupla real => estava dando erro antes de converter

# importando o arquivo de log gerado na execução
df = pd.read_csv('log_gearup.csv')
print(df.head())

"""
função para analisar o arquivo e gerar:
1. gráfico de linha para o acúmulo de cliques (mostra que os cliques foram logados)
2. gráfico de dispersão da trajetória do mouse (mostra que o caminho do mouse foi logado)
"""
def analisar_e_plotar_eventos(nome_arquivo):
  
    tempos_clique = []
    caminho_mouse_pos = []

    try:
        with open(nome_arquivo, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # pula o cabeçalho do arquivo
            for row in reader:
                evento = row[0]
                tempo = float(row[2])

                if evento == "Click":
                    tempos_clique.append(tempo)
                elif evento == "Caminho do mouse":
                    pos_str = row[1].strip()
                    # converte a string "(x, y)" em uma tupla => estava dando erro
                    pos_tuple = ast.literal_eval(pos_str)
                    caminho_mouse_pos.append(pos_tuple)
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return

    # criando os gráficos!
    
    # configuração da figura e dos subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Análise de Eventos do Usuário', fontsize=16)

    # gráfico de linha
    ax1.plot(tempos_clique, range(1, len(tempos_clique) + 1), marker='o', linestyle='-', color='b')
    ax1.set_title('Acúmulo de Cliques ao Longo do Tempo', fontsize=12)
    ax1.set_xlabel('Tempo (segundos)', fontsize=10)
    ax1.set_ylabel('Número de Cliques', fontsize=10)
    ax1.grid(True)
    ax1.tick_params(axis='x', rotation=45)

    # gráfico de dispersão
    if caminho_mouse_pos:
        x_coords = [pos[0] for pos in caminho_mouse_pos]
        y_coords = [pos[1] for pos in caminho_mouse_pos]
        ax2.scatter(x_coords, y_coords, s=5, alpha=0.5, color='r')
        ax2.set_title('Trajetória do Mouse na Tela', fontsize=12)
        ax2.set_xlabel('Coordenada X', fontsize=10)
        ax2.set_ylabel('Coordenada Y', fontsize=10)
        ax2.set_xlim(0, 800) # limites do eixo x
        ax2.set_ylim(600, 0) # limites do eixo Y e inverte (Pygame gera diferente)
        ax2.grid(True)
    else:
        ax2.set_title('Nenhum movimento do mouse registrado')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

# executa a função para o arquivo
analisar_e_plotar_eventos("log_gearup.csv")


"""
criando mais uma função para plotar um gráficos de barras, tem objetivo de indicar a frequência de cliques nas áreas
"""
def analisar_e_plotar_cliques(nome_arquivo):
    # define os tipos de clique de acordo com a legenda
    cliques_por_tipo = {
        'Pontos': 0,
        'Triângulos': 0,
        'Quadrados': 0,
        'Pentágonos': 0
    }

    try:
        with open(nome_arquivo, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # pula o cabeçalho do arquivo
            for row in reader:
                if len(row) > 1 and row[0] == 'Click':
                    detalhes = row[1]
                    if 'Ponto' in detalhes:
                        cliques_por_tipo['Pontos'] += 1
                    elif 'Triângulo' in detalhes:
                        cliques_por_tipo['Triângulos'] += 1
                    elif 'Quadrado' in detalhes:
                        cliques_por_tipo['Quadrados'] += 1
                    elif 'Pentágono' in detalhes:
                        cliques_por_tipo['Pentágonos'] += 1
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return

    if sum(cliques_por_tipo.values()) == 0:
        print("Nenhum clique de polígono ou ponto foi encontrado no arquivo de log.")
        return

    # lista os nomes e valores
    nomes = list(cliques_por_tipo.keys())
    valores = list(cliques_por_tipo.values())

    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    # configurações de plot
    ax.bar(nomes, valores, color=['purple', 'red', 'blue', 'green'])
    ax.set_title('Frequência de Cliques por Tipo de Objeto', fontsize=16, pad=20)
    ax.set_ylabel('Número de Cliques', fontsize=12)
    ax.set_xlabel('Tipo de Objeto', fontsize=12)
    ax.tick_params(axis='x', rotation=0, labelsize=10)
    ax.set_ylim(0, max(valores) * 1.2)

    for i, valor in enumerate(valores):
        ax.text(i, valor + max(valores) * 0.05, str(valor), ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig('frequencia_cliques_grafico.png')
    plt.show()

# executa a função para o arquivo
analisar_e_plotar_cliques("log_gearup.csv")
