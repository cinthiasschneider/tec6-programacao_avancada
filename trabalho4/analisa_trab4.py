# importando as bibliotecas necessárias
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configuração do estilo dos gráficos
sns.set_theme(style="whitegrid")

# definindo o nome do arquivo
FILE_NAME = 'log_minkowski.csv' 

# definindo cores RGB
AZUL_HEX = '#0000FF'
VERMELHO_HEX = '#C80000'

# função para analisar o desempenho do algoritmo
def analisar_desempenho_minkowski():
    print("--- ANÁLISE DE DESEMPENHO DA SOMA DE MINKOWSKI (TRABALHO 4) ---")
    
    # carrega o arquivo csv
    try:
        df = pd.read_csv(FILE_NAME)
        
    except pd.errors.EmptyDataError:
        print("\nERRO: O arquivo CSV está vazio. Execute o código Pygame para gerar dados.")
        return
    except Exception as e:
        print(f"\nERRO ao ler o arquivo CSV: {e}")
        return

    # exibir as primeiras linhas
    df.columns = df.columns.str.strip() # remove espaços em branco
    print("\nEstrutura dos dados (df.head()):")
    print(df.head())
    
    # preparando os dados pra processar
    df = df.rename(columns={
        'Vertices_P1': 'N1',
        'Vertices_O_Max': 'N2',
        'Pontos_Soma_Gerados': 'N_soma',
        'Tempo_Minkowski_ms': 'Tempo_ms'
    })
    
    # coluna para a complexidade teórica N*log(N)
    df['Complexidade_teorica'] = df['N_soma'].apply(lambda n: n * np.log(n) if n > 0 else 0)
    
    print("\nInformações estatísticas do tempo (ms):")
    print(df['Tempo_ms'].describe())

    # gráfico de crescimento (tempo vs pontos gerados)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='N_soma', y='Tempo_ms', data=df, hue='Modo', style='Modo', s=100)
    
    if len(df) > 1:
        sns.regplot(x='N_soma', y='Tempo_ms', data=df, scatter=False, color=VERMELHO_HEX, label='Tendência linear')

    plt.title('Desempenho: tempo vs pontos gerados (n1 * n2)')
    plt.xlabel('Número de pontos gerados na soma (n1 * n2)')
    plt.ylabel('Tempo de computação (ms)')
    plt.legend(title='Modo de execução (manual ou procedural)')
    plt.grid(True)
    plt.show()

    # gráfico de tempo real vs complexidade teórica
    plt.figure(figsize=(10, 6))
    
    # normalizar a complexidade teórica para caber no gráfico
    max_tempo = df['Tempo_ms'].max()
    max_comp = df['Complexidade_teorica'].max()
    if max_comp > 0:
        df['Complexidade_normalizada'] = df['Complexidade_teorica'] * (max_tempo / max_comp)
    else:
        df['Complexidade_normalizada'] = 0
    
    # plot de tempo real
    sns.lineplot(x=df.index, y='Tempo_ms', data=df, marker='o', label='Tempo real (ms)', color=AZUL_HEX, linewidth=2)
    # plot de tendência teórica
    sns.lineplot(x=df.index, y='Complexidade_normalizada', data=df, linestyle='--', label='Complexidade teórica normalizada (O(N log N))', color='orange', linewidth=2)
    
    plt.title('Comparação: tempo real vs complexidade teórica')
    plt.xlabel('Ordem de execução')
    plt.ylabel('Valor normalizado e tempo')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    print("\nAnálise concluída.")

# --- Execução Principal ---

if __name__ == '__main__':
    analisar_desempenho_minkowski()
