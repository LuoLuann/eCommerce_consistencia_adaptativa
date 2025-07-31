import requests
import time
import random
import csv
from datetime import datetime
import os

PROXY_URL = "http://proxy:5000/write"

# --- Configuração dos arquivos CSV ---
now = datetime.now()
date_str = now.strftime('%Y-%m-%d_%H-%M')
service_name = "avaliacoes"
log_dir = "logs"

# Cria a pasta de logs se ela não existir
os.makedirs(log_dir, exist_ok=True)


# Arquivo para latência
latency_file = open(os.path.join(log_dir, f"latencias_{service_name}_{date_str}.csv"), 'w', newline='')
latency_writer = csv.writer(latency_file)
latency_writer.writerow(['timestamp', 'latency_seconds', 'consistency_type', 'success'])

# Arquivo para throughput
throughput_file = open(os.path.join(log_dir, f"throughput_{service_name}_{date_str}.csv"), 'w', newline='')
throughput_writer = csv.writer(throughput_file)
throughput_writer.writerow(['timestamp', 'requests_per_second'])

# Arquivo para conflitos/erros
conflicts_file = open(os.path.join(log_dir, f"conflitos_{service_name}_{date_str}.csv"), 'w', newline='')
conflicts_writer = csv.writer(conflicts_file)
conflicts_writer.writerow(['timestamp', 'error_message'])

# --- Configuração do Throughput ---
request_count = 0
start_time_throughput = time.time()

print(f"Iniciando serviço de Avaliações. Logs serão salvos na pasta '{log_dir}'.")

while True:
    review_id = f"review_{random.randint(10000, 99999)}"
    review_data = {
        "product_id": f"item{random.randint(1, 10)}",
        "user_id": f"user{random.randint(1, 100)}",
        "rating": random.randint(1, 5)
    }
    success = False

    start_time_latency = time.time()
    
    try:
        response = requests.post(PROXY_URL, json={
            "key": review_id,
            "value": str(review_data),
            "consistency": "eventual"
        }, timeout=2)

        response.raise_for_status()
        success = True
        print(f"Serviço de Avaliações: Requisição EVENTUAL para a chave {review_id} bem-sucedida.")

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        print(f"!!! Erro no Serviço de Avaliações: {error_msg}")
        # Salva o erro no CSV
        conflicts_writer.writerow([datetime.now().isoformat(), error_msg])
        conflicts_file.flush()

    finally:
        end_time_latency = time.time()
        latency = end_time_latency - start_time_latency
        timestamp = datetime.now().isoformat()
        
        # Salva a latência no CSV
        latency_writer.writerow([timestamp, f"{latency:.4f}", "eventual", success])
        latency_file.flush()
        
        request_count += 1
    
    # Calcula e salva o throughput a cada 10 segundos
    current_time = time.time()
    elapsed_time = current_time - start_time_throughput
    if elapsed_time >= 10:
        throughput = request_count / elapsed_time
        print(f"--- Throughput de Avaliações: {throughput:.2f} reqs/segundo ---")
        # Salva o throughput no CSV
        throughput_writer.writerow([datetime.now().isoformat(), f"{throughput:.2f}"])
        throughput_file.flush()
        
        request_count = 0
        start_time_throughput = current_time

    time.sleep(1.5)