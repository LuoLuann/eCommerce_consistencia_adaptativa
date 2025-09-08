import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob

LOGS_DIR = 'logs'
GRAPH_DIR = 'graficos'
os.makedirs(GRAPH_DIR, exist_ok=True)

print("Iniciando a análise dos resultados...")

def parse_path(path):
    """Extrai os parâmetros do teste a partir do caminho do diretório."""
    parts = path.split(os.sep)
    try:
        replicas = int(parts[-3].replace('replicas_', ''))
        consistency = parts[-2]
        total_load = parts[-1].replace('total_', '')
        return replicas, consistency, total_load
    except (IndexError, ValueError) as e:
        print(f"Aviso: Não foi possível parsear o diretório: {path}. Erro: {e}")
        return None, None, None

def calculate_metrics(df):
    """Calcula as métricas agregadas para um DataFrame de um cenário."""
    df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
    df = df.dropna(subset=['latency_ms'])

    avg_latency = df['latency_ms'].mean()
    error_count = df[df['success'] == False].shape[0]

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    total_duration_seconds = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
    successful_requests = df[df['success'] == True].shape[0]

    throughput = successful_requests / total_duration_seconds if total_duration_seconds > 0 else 0

    return {
        'avg_latency': avg_latency,
        'error_count': error_count,
        'throughput_rps': throughput
    }

# --- Coleta e Processamento dos Dados ---
all_results = []
scenario_paths = set(os.path.dirname(p) for p in glob.glob(f'{LOGS_DIR}/**/*.csv', recursive=True))

for path in scenario_paths:
    replicas, consistency, total_load = parse_path(path)
    if not all((replicas, consistency, total_load)):
        continue

    all_csvs = glob.glob(os.path.join(path, '*.csv'))
    if not all_csvs:
        continue

    df_scenario = pd.concat((pd.read_csv(f) for f in all_csvs), ignore_index=True)
    metrics = calculate_metrics(df_scenario)
    
    all_results.append({
        'replicas': replicas,
        'consistency': consistency,
        'total_load': total_load,
        **metrics
    })

if not all_results:
    print("Nenhum resultado encontrado. Verifique se a pasta 'logs' contém os CSVs no formato esperado.")
else:
    # --- Geração dos Gráficos ---
    results_df = pd.DataFrame(all_results)
    results_df['total_load_numeric'] = results_df['total_load'].str.replace('k', '').astype(int)
    results_df = results_df.sort_values('total_load_numeric')

    sns.set_theme(style="whitegrid")

    for consistency_type in results_df['consistency'].unique():
        print(f"--- Gerando gráficos para o modo de consistência: '{consistency_type}' ---")
        
        df_group = results_df[results_df['consistency'] == consistency_type]

        # --- Gráfico 1: Latência Média ---
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(data=df_group, x='total_load', y='avg_latency', hue='replicas', palette='viridis')
        ax.set_title(f'Latência Média - Consistência: {consistency_type.upper()}')
        ax.set_xlabel('Carga de Trabalho Total')
        ax.set_ylabel('Latência Média (ms)')
        ax.legend(title='Nº de Réplicas')
        output_path = os.path.join(GRAPH_DIR, f'latencia_{consistency_type}.png')
        plt.savefig(output_path)
        plt.close()
        print(f"Gráfico de latência salvo em: {output_path}")

        # --- Gráfico 2: Vazão (Throughput) ---
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(data=df_group, x='total_load', y='throughput_rps', hue='replicas', palette='plasma')
        ax.set_title(f'Vazão (Throughput) - Consistência: {consistency_type.upper()}')
        ax.set_xlabel('Carga de Trabalho Total')
        ax.set_ylabel('Vazão (Requisições / Segundo)')
        ax.legend(title='Nº de Réplicas')
        output_path = os.path.join(GRAPH_DIR, f'vazao_{consistency_type}.png')
        plt.savefig(output_path)
        plt.close()
        print(f"Gráfico de vazão salvo em: {output_path}")

        # --- Gráfico 3: Contagem de Erros ---
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(data=df_group, x='total_load', y='error_count', hue='replicas', palette='magma')
        ax.set_title(f'Contagem de Erros - Consistência: {consistency_type.upper()}')
        ax.set_xlabel('Carga de Trabalho Total')
        ax.set_ylabel('Número Total de Erros')
        ax.legend(title='Nº de Réplicas')
        output_path = os.path.join(GRAPH_DIR, f'erros_{consistency_type}.png')
        plt.savefig(output_path)
        plt.close()
        print(f"Gráfico de erros salvo em: {output_path}")

    print("\nAnálise finalizada. Todos os gráficos foram gerados.")