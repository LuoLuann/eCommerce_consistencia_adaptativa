import os
import pandas as pd

def parse_carga_total(nome_pasta):
    """
    Converte o nome da pasta de carga (ex: '1k', '4k', '10k') para um valor numérico.
    Retorna o valor numérico ou None se o formato for inválido.
    """
    nome_pasta = nome_pasta.lower()
    if nome_pasta.endswith('k'):
        try:
            # Remove o 'k' e converte o número para inteiro, depois multiplica por 1000
            numero = int(nome_pasta[:-1])
            return numero * 1000
        except ValueError:
            # Se a conversão falhar (ex: 'total_abc'), retorna None
            return None
    return None

def analisar_logs(diretorio_base='.'):
    """
    Lê os logs de teste de várias execuções, extrai informações do cenário
    a partir da estrutura de diretórios e consolida tudo em um único arquivo CSV.

    Args:
        diretorio_base (str): O caminho para o diretório que contém as pastas
                              de execução (ex: '1', '2', '3', '4', '5').
    """
    todos_os_dados = []
    pastas_execucao = ['1', '2', '3', '4', '5']

    print("Iniciando a análise dos logs...")

    for execucao in pastas_execucao:
        caminho_execucao = os.path.join(diretorio_base, execucao, 'logs')
        if not os.path.isdir(caminho_execucao):
            print(f"Aviso: Diretório de logs para a execução '{execucao}' não encontrado em '{caminho_execucao}'. Pulando.")
            continue

        print(f"Processando execução: {execucao}")

        for root, dirs, files in os.walk(caminho_execucao):
            for nome_arquivo in files:
                if nome_arquivo.endswith('.csv'):
                    caminho_completo = os.path.join(root, nome_arquivo)
                    
                    try:
                        partes_caminho = caminho_completo.split(os.sep)
                        
                        num_replicas = int(partes_caminho[-4].split('_')[1])
                        modo_consistencia = partes_caminho[-3]
                        
                        # Usa a nova função para interpretar a carga total
                        nome_pasta_carga = partes_caminho[-2].split('_')[1]
                        num_requests = parse_carga_total(nome_pasta_carga)
                        
                        if num_requests is None:
                            print(f"Aviso: Não foi possível determinar o número de requests para a pasta '{partes_caminho[-2]}'. Pulando arquivo: {caminho_completo}")
                            continue
                        
                        df_log = pd.read_csv(caminho_completo)
                        
                        df_log['execucao_teste'] = int(execucao)
                        df_log['replicas_redis'] = num_replicas
                        df_log['modo_consistencia'] = modo_consistencia
                        df_log['total_requests'] = num_requests
                        
                        todos_os_dados.append(df_log)
                        
                    except (IndexError, ValueError) as e:
                        print(f"Erro ao processar o arquivo '{caminho_completo}'. O formato do diretório pode ser inesperado. Erro: {e}")
                    except Exception as e:
                        print(f"Ocorreu um erro inesperado ao ler '{caminho_completo}': {e}")

    if not todos_os_dados:
        print("Nenhum dado de log foi encontrado ou processado. Verifique os caminhos e a estrutura dos diretórios.")
        return

    df_final = pd.concat(todos_os_dados, ignore_index=True)

    arquivo_saida = 'resultados_consolidados.csv'
    df_final.to_csv(arquivo_saida, index=False)

    print("\nAnálise concluída com sucesso!")
    print(f"Os dados foram consolidados e salvos em: '{arquivo_saida}'")
    print(f"Total de registros processados: {len(df_final)}")

if __name__ == '__main__':
    analisar_logs()