import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

def parse_total_reqs(req_str):
    """
    Converte uma string de carga como '5k' ou '20000k' para um inteiro.
    """
    req_str = req_str.lower()
    if 'k' in req_str:
        # Remove 'k' e multiplica por 1000
        return int(re.sub(r'[^0-9]', '', req_str)) * 1000
    return int(req_str)

def load_all_logs(base_dir):
    """
    Carrega todos os arquivos de log CSV recursivamente de um diretório base
    e extrai os parâmetros (modo, réplicas, carga) do caminho do arquivo.
    """
    all_data = []
    
    if not os.path.isdir(base_dir):
        print(f"Diretório de logs base não encontrado: '{base_dir}'")
        return pd.DataFrame()

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    parts = file_path.split(os.sep)
                    
                    if len(parts) >= 4:
                        replicas_str = [p for p in parts if p.startswith('replicas_')]
                        mode_str = parts[-3] 
                        total_reqs_folder_str = [p for p in parts if p.startswith('total_')]

                        if replicas_str and total_reqs_folder_str:
                            num_replicas = int(replicas_str[0].split('_')[1])
                            # Extrai o valor e processa o 'k'
                            total_reqs_value = total_reqs_folder_str[0].split('_')[1]
                            total_reqs = parse_total_reqs(total_reqs_value)
                            mode = mode_str.capitalize()

                            df = pd.read_csv(file_path)
                            df['replicas'] = num_replicas
                            df['modo'] = mode
                            df['carga_total'] = total_reqs
                            all_data.append(df)
                except (IndexError, ValueError) as e:
                    print(f"Não foi possível processar o caminho do arquivo: {file_path}. Erro: {e}")
                except Exception as e:
                    print(f"Erro ao ler o arquivo {file_path}: {e}")
    
    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

# --- Carregar Dados ---
logs_directory = 'logs'
combined_data = load_all_logs(logs_directory)

# --- Geração do Gráfico ---
if combined_data.empty:
    print("Nenhum dado de log foi encontrado. Verifique a estrutura de pastas.")
    print("Gerando um gráfico de exemplo com dados fictícios.")
    data = {
        'latency_ms': [10, 12, 15, 11, 13, 50, 20, 22, 25, 21, 23, 60, 110, 115, 120, 112, 118, 200],
        'modo': ['Eventual', 'Forte', 'Dinâmico'] * 6,
        'carga_total': [5000] * 9 + [40000] * 9,
        'replicas': [1] * 18
    }
    combined_data = pd.DataFrame(data)

# Criar uma coluna de string para a carga para melhor rotulagem e ordenação
combined_data['carga_str'] = combined_data['carga_total'].apply(
    lambda x: f'{x // 1000}k' if x >= 1000 else str(x)
) + ' Requisições'

# Ordenar os rótulos do eixo X com base no valor numérico da carga
carga_order = sorted(
    combined_data['carga_str'].unique(), 
    key=lambda x: int(re.sub(r'[^0-9]', '', x.split()[0]))
)

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(16, 9))

sns.boxplot(
    data=combined_data,
    x='carga_str',
    y='latency_ms',
    hue='modo',
    ax=ax,
    palette='viridis',
    order=carga_order
)

ax.set_title('Distribuição da Latência por Cenário e Carga de Trabalho', fontsize=18, pad=20)
ax.set_xlabel('Carga de Trabalho Total', fontsize=14)
ax.set_ylabel('Latência por Requisição (ms)', fontsize=14)
ax.tick_params(axis='x', rotation=0, labelsize=12)
ax.tick_params(axis='y', labelsize=12)
ax.legend(title='Modo de Consistência', fontsize=12)

plt.tight_layout(pad=1.5)

output_filename = 'latencia_distribuicao_boxplot_final.png'
plt.savefig(output_filename, dpi=300)
print(f"Gráfico salvo como: {output_filename}")