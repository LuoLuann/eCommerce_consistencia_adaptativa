import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

LOGS_DIR = "logs"
GRAFICOS_DIR = "graficos"

def analyze_and_plot(scenario_folder):
    """Lê todos os CSVs de uma pasta de cenário e gera análises e gráficos detalhados."""
    
    scenario_path = os.path.join(LOGS_DIR, scenario_folder)
    os.makedirs(GRAFICOS_DIR, exist_ok=True)

    all_files = [os.path.join(scenario_path, f) for f in os.listdir(scenario_path) if f.endswith('.csv')]
    if not all_files:
        print(f"Nenhum arquivo CSV encontrado em '{scenario_folder}'.")
        return

    df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
    
    print(f"\n--- Análise do Cenário: {scenario_folder} ---")
    print(f"Total de requisições registradas: {len(df)}")

    success_df = df[df['success'] == True].copy()
    if success_df.empty:
        print("Nenhuma requisição bem-sucedida encontrada para análise.")
        return
        
    # --- 1. Análise de Latência ---
    plt.figure(figsize=(12, 8))
    ax = sns.boxplot(x='service', y='latency_ms', hue='consistency', data=success_df, palette={"strong": "salmon", "eventual": "skyblue"})
    plt.title(f'Distribuição de Latência por Serviço ({scenario_folder})', fontsize=16)
    plt.ylabel('Latência (ms)', fontsize=12)
    plt.xlabel('Serviço', fontsize=12)
    plt.yscale('log')
    plt.grid(True, which="both", ls="--", linewidth=0.5)
    plt.tight_layout()
    
    # Adiciona anotações de mediana no gráfico
    medians = success_df.groupby(['service'])['latency_ms'].median().round(2)
    for i, service in enumerate(ax.get_xticklabels()):
        service_name = service.get_text()
        if service_name in medians:
            ax.text(i, medians[service_name], f' {medians[service_name]} ms', 
                    horizontalalignment='center', size='small', color='black', weight='semibold')

    grafico_latencia_path = os.path.join(GRAFICOS_DIR, f"{scenario_folder}_latencia.png")
    plt.savefig(grafico_latencia_path)
    print(f"\nGráfico de latência salvo em '{grafico_latencia_path}'.")

    # Imprime estatísticas detalhadas de latência
    latency_stats = success_df.groupby('service')['latency_ms'].agg(['mean', 'median', lambda x: x.quantile(0.95), lambda x: x.quantile(0.99)]).round(2)
    latency_stats.columns = ['Média', 'Mediana (P50)', 'Percentil 95', 'Percentil 99']
    print("\n--- Estatísticas Detalhadas de Latência (ms) ---")
    print(latency_stats)
    
    # --- 2. Análise de Throughput ---
    success_df['timestamp'] = pd.to_datetime(success_df['timestamp'])
    
    def calculate_throughput(x):
        duration_seconds = (x['timestamp'].max() - x['timestamp'].min()).total_seconds()
        return len(x) / duration_seconds if duration_seconds > 0 else 0

    throughput_stats = success_df.groupby('service').apply(calculate_throughput)
    
    print("\n--- Throughput Médio (Requisições por Segundo) ---")
    print(throughput_stats.round(2))
    
    if not success_df.empty:
        service_consistency_map = success_df.drop_duplicates('service').set_index('service')['consistency']
        color_map = {'strong': 'salmon', 'eventual': 'skyblue'}
        bar_colors = throughput_stats.index.map(service_consistency_map).map(color_map)

        plt.figure(figsize=(10, 6))
        bars = throughput_stats.plot(kind='bar', color=bar_colors)
        plt.title(f'Throughput Médio por Serviço ({scenario_folder})', fontsize=16)
        plt.ylabel('Requisições por Segundo (RPS)', fontsize=12)
        plt.xlabel('Serviço', fontsize=12)
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', linewidth=0.7)
        
        for bar in bars.patches:
            bars.annotate(f'{bar.get_height():.2f}', 
                          (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                          ha='center', va='center',
                          size=10, xytext=(0, 8),
                          textcoords='offset points')

        plt.tight_layout()
        grafico_throughput_path = os.path.join(GRAFICOS_DIR, f"{scenario_folder}_throughput.png")
        plt.savefig(grafico_throughput_path)
        print(f"Gráfico de throughput salvo em '{grafico_throughput_path}'.")

    # --- 3. Análise de Erros ---
    error_df = df[df['success'] == False]
    if not error_df.empty:
        error_counts = error_df['service'].value_counts()
        print("\n--- Contagem de Erros ---")
        print(error_counts)
        
        plt.figure(figsize=(10, 6))
        error_bars = error_counts.plot(kind='bar', color='red')
        plt.title(f'Contagem de Erros por Serviço ({scenario_folder})', fontsize=16)
        plt.ylabel('Número de Erros', fontsize=12)
        plt.xlabel('Serviço', fontsize=12)
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', linewidth=0.7)

        # Adiciona os valores no topo das barras
        for bar in error_bars.patches:
            error_bars.annotate(f'{int(bar.get_height())}', 
                                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                                ha='center', va='center',
                                size=10, xytext=(0, 8),
                                textcoords='offset points')

        plt.tight_layout()
        grafico_erros_path = os.path.join(GRAFICOS_DIR, f"{scenario_folder}_erros.png")
        plt.savefig(grafico_erros_path)
        print(f"Gráfico de erros salvo em '{grafico_erros_path}'.")
    else:
        print("\nNenhum erro registrado.")
        
    # --- 4. Análise de Conflitos ---
    if 'conflict_detected' in df.columns:
        conflict_df = df[df['conflict_detected'] == True]
        if not conflict_df.empty:
            conflict_counts = conflict_df['service'].value_counts()
            print("\n--- Contagem de Conflitos de Duplicação ---")
            print(conflict_counts)
            
            plt.figure(figsize=(10, 6))
            conflict_bars = conflict_counts.plot(kind='bar', color='orange')
            plt.title(f'Contagem de Conflitos por Serviço ({scenario_folder})', fontsize=16)
            plt.ylabel('Número de Conflitos', fontsize=12)
            plt.xlabel('Serviço', fontsize=12)
            plt.xticks(rotation=0)
            plt.grid(axis='y', linestyle='--', linewidth=0.7)

            for bar in conflict_bars.patches:
                conflict_bars.annotate(f'{int(bar.get_height())}', 
                                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                                    ha='center', va='center',
                                    size=10, xytext=(0, 8),
                                    textcoords='offset points')

            plt.tight_layout()
            grafico_conflitos_path = os.path.join(GRAFICOS_DIR, f"{scenario_folder}_conflitos.png")
            plt.savefig(grafico_conflitos_path)
            print(f"Gráfico de conflitos salvo em '{grafico_conflitos_path}'.")
        else:
            print("\nNenhum conflito de duplicação detectado.")

    plt.close('all')

# --- Execução Principal ---
if __name__ == "__main__":
    if not os.path.exists(LOGS_DIR):
        print(f"Pasta '{LOGS_DIR}' não encontrada.")
    else:
        # Pede ao usuário para escolher qual cenário analisar
        scenarios = [d for d in os.listdir(LOGS_DIR) if os.path.isdir(os.path.join(LOGS_DIR, d))]
        if not scenarios:
            print(f"Nenhuma pasta de cenário encontrada em '{LOGS_DIR}'.")
        else:
            print("Selecione o cenário para analisar:")
            for i, s in enumerate(scenarios):
                print(f"  {i+1}: {s}")
            
            try:
                choice = int(input("Digite o número do cenário: ")) - 1
                if 0 <= choice < len(scenarios):
                    analyze_and_plot(scenarios[choice])
                else:
                    print("Escolha inválida.")
            except (ValueError, IndexError):
                print("Entrada inválida. Por favor, digite um número da lista.")