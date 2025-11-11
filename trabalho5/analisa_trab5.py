import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

sns.set_style("whitegrid")
file_path = 'log_trab5.csv' 
pd.set_option('display.max_columns', None)

try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Timestamp", "Modo", "Acao", "Detalhes"])
    raise SystemExit(0)
    
if df.empty:
      raise SystemExit(0)

# normalização
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Num_Agentes'] = 1 
df['Modo_Norm'] = df['Modo'].apply(lambda x: 'Interativo' if str(x) in ['1', 'Interativo'] else 
                                               'Procedural' if str(x).startswith(('2', 'Procedural')) else 'Outro')
# modo procedural
procedural_mask = df['Modo'].str.startswith('Procedural', na=False)
df.loc[procedural_mask, 'Num_Agentes'] = (
    df.loc[procedural_mask, 'Modo']
    .str.extract(r'\((\d+)\sAgs\)', expand=False)
)
agente_detail_mask = df['Acao'].isin(['RUN_MULTI_AGENTE', 'GERAR_PROCEDURAL', 'FIM_MOVIMENTO'])
df.loc[agente_detail_mask, 'Num_Agentes'] = (
    df.loc[agente_detail_mask, 'Detalhes']
    .str.extract(r'(\d+)\sagentes', expand=False)
    .fillna(df['Num_Agentes'])
)

df['Num_Agentes'] = pd.to_numeric(df['Num_Agentes'], errors='coerce').fillna(1).astype(int)

# análise de custo computacional e crescimento dos agentes
df_runs = df[df['Acao'].isin(['INICIO_SESSAO', 'GERAR_PROCEDURAL', 'FIM_MOVIMENTO'])].copy()
df_runs = df_runs.sort_values('Timestamp')

# encontra inícios e fins + id para cada sessão
run_start_mask = (df_runs['Acao'].isin(['INICIO_SESSAO', 'GERAR_PROCEDURAL']))
df_runs['Run_ID'] = run_start_mask.cumsum()

analise_crescimento = []
for run_id, run_group in df_runs.groupby('Run_ID'):
    inicio_time = run_group['Timestamp'].min()
    fim_movimento_rows = run_group[run_group['Acao'] == 'FIM_MOVIMENTO']  
    if not fim_movimento_rows.empty:
        fim_time = fim_movimento_rows['Timestamp'].iloc[0]
        num_ags = run_group['Num_Agentes'].iloc[0]      
        if fim_time > inicio_time and num_ags > 0:
            duracao_segundos = (fim_time - inicio_time).total_seconds()
            analise_crescimento.append({
                'Num_Agentes': num_ags,
                'Duracao_Total_Segundos': duracao_segundos,
                'Tempo_Medio_Por_Agente': duracao_segundos / num_ags,
                'Modo': run_group['Modo_Norm'].iloc[0]
            })

df_crescimento = pd.DataFrame(analise_crescimento)
if not df_crescimento.empty:
    df_agrupado = df_crescimento.groupby('Num_Agentes').agg(
        Tempo_Total_Medio=('Duracao_Total_Segundos', 'mean'),
        Tempo_Por_Agente_Medio=('Tempo_Medio_Por_Agente', 'mean'),
        Num_Rodadas=('Num_Agentes', 'count')
    ).reset_index()
    plt.figure(figsize=(18, 6))

    # crescimento do custo total
    plt.subplot(1, 3, 1)
    sns.lineplot(x='Num_Agentes', y='Tempo_Total_Medio', data=df_agrupado, marker='o', color='blue')
    plt.title('1. Crescimento do Custo Total (Média)')
    plt.xlabel('Número de Agentes')
    plt.ylabel('Tempo Total Médio (s)')

    # tempo por agente
    plt.subplot(1, 3, 2)
    sns.lineplot(x='Num_Agentes', y='Tempo_Por_Agente_Medio', data=df_agrupado, marker='o', color='red')
    plt.title('2. Tempo Médio por Agente (Overhead)')
    plt.xlabel('Número de Agentes')
    plt.ylabel('Tempo Médio por Agente (s)')
    
    # dispersão => comportamento do custo
    plt.subplot(1, 3, 3)
    sns.regplot(x='Num_Agentes', y='Duracao_Total_Segundos', data=df_crescimento, scatter_kws={'alpha':0.6}, line_kws={'color':'green'})
    plt.title('3. Custo Computacional: Dispersão e Tendência')
    plt.xlabel('Número de Agentes')
    plt.ylabel('Duração Total da Rodada (s)')

    plt.suptitle('Análise do Custo Computacional e Crescimento de Agentes', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.9])
    plt.show()

# frequência de ações
acoes_foco = ['CLIQUE_ESQUERDO', 'CLIQUE_DIREITO', 'RUN_1_AGENTE', 'RUN_MULTI_AGENTE', 'LIMPAR_GRID']
df_acoes = df[df['Acao'].isin(acoes_foco)]

if not df_acoes.empty:
    plt.figure(figsize=(10, 5))
    sns.countplot(y='Acao', data=df_acoes, order=df_acoes['Acao'].value_counts().index, palette='rocket')
    plt.title('4. Frequência das Principais Ações Registradas')
    plt.xlabel('Contagem')
    plt.ylabel('Ação')
    plt.show()


# complexidade do ambiente (barreiras/obstáculos)
df_barriers = df[(df['Acao'].str.contains('Barreira', na=False)) & (df['Modo_Norm'] == 'Interativo')].copy()

if not df_barriers.empty:
    cliques_df = df_barriers[df_barriers['Detalhes'].str.contains('@\(', na=False)].copy()
    
    if not cliques_df.empty:
        cliques_df[['Row', 'Col']] = cliques_df['Detalhes'].str.extract(r'@\((\d+),(\d+)\)').astype(int)
        heatmap_data = cliques_df.groupby(['Row', 'Col']).size().unstack(fill_value=0)
        
        plt.figure(figsize=(8, 8))
        sns.heatmap(heatmap_data, cmap="hot_r", linewidths=.1, linecolor='lightgray', 
                    cbar_kws={'label': 'Frequência de Criação de Barreiras'}, 
                    vmin=0, vmax=heatmap_data.values.max() * 0.75) 
        plt.title('5. Mapa de Calor da Criação de Barreiras (Densidade do Mapa)')
        plt.xlabel('Coluna (Col)')
        plt.ylabel('Linha (Row)')
        plt.gca().invert_yaxis() 
        plt.show()
    else:
        print("\nNão há dados de coordenadas de barreiras válidas")
else:
    print("\nNão foram registradas ações de 'Barreira'")
