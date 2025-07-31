import requests
import time
import random
import csv
from datetime import datetime
import os
import json

# --- CONFIGURAÇÕES DO EXPERIMENTO (EDITAR AQUI) ---
NUM_REQUESTS = 1000  # <-- MUDE AQUI: 1000, 10000 ou 100000
SERVICE_NAME = "avaliacoes"
CONSISTENCY_TYPE = "eventual"
SLEEP_INTERVAL = 0.05 # Intervalo entre requisições em segundos

# --- NÃO EDITAR ABAIXO DISSO ---

PROXY_URL = "http://proxy:5000/write"

# --- Configuração dos Arquivos de Log ---
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)

# Gera um nome de arquivo único com data e hora para não sobrescrever resultados
timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file_path = os.path.join(log_dir, f"{SERVICE_NAME}_{NUM_REQUESTS}reqs_{timestamp_str}.csv")

# --- Execução do Teste ---
print(f"Iniciando {SERVICE_NAME} com {NUM_REQUESTS} requisições do tipo '{CONSISTENCY_TYPE}'.")

results = []
start_time_total = time.time()

try:
    for i in range(NUM_REQUESTS):
        key = f"{SERVICE_NAME}_{random.randint(10000, 99999)}"
        value = {"data": f"payload_{i}"} # Payload simples
        success = False
        error_msg = ""
        
        start_time_latency = time.time()
        
        try:
            response = requests.post(PROXY_URL, json={
                "key": key,
                "value": json.dumps(value),
                "consistency": CONSISTENCY_TYPE
            }, timeout=10) # Timeout de 10 segundos para a requisição
            response.raise_for_status()
            success = True
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"!!! Erro em {SERVICE_NAME}: {error_msg}")

        end_time_latency = time.time()
        latency_ms = (end_time_latency - start_time_latency) * 1000
        
        results.append({
            "timestamp": datetime.now().isoformat(),
            "service": SERVICE_NAME,
            "consistency": CONSISTENCY_TYPE,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_msg
        })

        # Imprime o progresso a cada 10%
        if (i + 1) % (NUM_REQUESTS / 10) == 0:
            print(f"Serviço {SERVICE_NAME}: Progresso - {i+1}/{NUM_REQUESTS} requisições enviadas.")
        
        time.sleep(SLEEP_INTERVAL)

finally:
    end_time_total = time.time()
    total_duration = end_time_total - start_time_total
    overall_throughput = NUM_REQUESTS / total_duration if total_duration > 0 else 0
    
    # Salva todos os resultados de uma vez no final
    if results:
        with open(output_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResultados de {SERVICE_NAME} salvos em {output_file_path}")
    
    print(f"--- {SERVICE_NAME} Finalizado ---")
    print(f"Tempo total: {total_duration:.2f} segundos")
    print(f"Throughput geral: {overall_throughput:.2f} reqs/segundo")