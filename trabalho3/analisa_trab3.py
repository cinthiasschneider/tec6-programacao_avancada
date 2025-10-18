# código rodado no Google Colab para facilitar a utilização das bibliotecas matplotlib, seaborn e pandas.

"""
PERGUNTAS:
Algoritmo de Envoltória Convexa escolhido?
- Escolhi o algoritmo QuickHull por conveniência, já que ele já é utilizado na biblioteca SciPy como padrão para a função ConvexHull. 
- Este algoritmo tem a característica de divisão e conquista, tendo uma complexidade de tempo média de 0(n log n).
Existe diferença de custo computacional dependendo da distribuição de pontos?
- Sim, quanto mais pontos são adicionados (no caso da opção 1 - clicar e criar pontos) ou no número fixo de pontos aleatórios, o custo computacional tende a ser maior.
"""
# importar as bibliotecas
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# importando arquivo csv
df = pd.read_csv('log_trab3.csv')
print(df.head())

# análise dos dados
print("\n" + "="*50)
print("Gráficos e visualizações")
print("="*50)

# identifica as colunas numéricas e categóricas
colunas_numericas = df.select_dtypes(include=np.number).columns
colunas_categoricas = df.select_dtypes(include=['object', 'category']).columns

# visualizar as distribuições numéricas
for col in colunas_numericas:
    # pula as colunas de id ou com poucos valores
    if df[col].nunique() > 10:
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))

        # histograma => mostra a frequência dos valores em diferentes bins
        sns.histplot(df[col].dropna(), kde=True, ax=axes[0])
        axes[0].set_title(f'Histograma de {col}')

        # violin plot => mostra a densidade de probabilidade
        sns.violinplot(y=df[col].dropna(), ax=axes[1], inner="quartile")
        axes[1].set_title(f'Violin Plot de {col}')

        plt.suptitle(f"Análise da variável: {col}", fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

# visualiza frequências categóricas
for col in colunas_categoricas:
    if df[col].nunique() < 20 and df[col].nunique() > 1: # limita para gráficos legíveis
        plt.figure(figsize=(10, 5))
        sns.countplot(y=df[col], order = df[col].value_counts().index)
        plt.title(f'Frequência de ocorrência: {col}')
        plt.xlabel('Contagem')
        plt.ylabel(col)
        plt.show()

# matriz de correlação => mede a distribuição de frequência de cada categoria
if len(colunas_numericas) >= 2:
    print("\n--- Matriz de correlação ---")
    corr_matrix = df[colunas_numericas].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Heatmap da matriz de correlação')
    plt.show()
