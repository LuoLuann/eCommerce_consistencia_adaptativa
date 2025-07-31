import requests
import time
import random
import csv
from datetime import datetime

PROXY_URL = "http://proxy:5000/write"

# --- Configuração do CSV ---
now = datetime.now()
file_name = f"avaliacoes_{now.strftime('%Y-%m-%d_%H-%M')}.csv"
csv_file = open(file_name, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['timestamp', 'latency_seconds', 'consistency_type', 'success'])

# --- Configuração do Throughput ---
request_count = 0
start_time_throughput = time.time()

print(f"Iniciando serviço de Avaliações. Métricas serão salvas em {file_name}")

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
        print(f"!!! Erro no Serviço de Avaliações: {e}")

    finally:
        end_time_latency = time.time()
        latency = end_time_latency - start_time_latency
        timestamp = datetime.now().isoformat()
        
        csv_writer.writerow([timestamp, f"{latency:.4f}", "eventual", success])
        csv_file.flush()
        
        request_count += 1
    
    # Calcula e exibe o throughput a cada 10 segundos
    current_time = time.time()
    elapsed_time = current_time - start_time_throughput
    if elapsed_time >= 10:
        throughput = request_count / elapsed_time
        print(f"--- Throughput de Avaliações: {throughput:.2f} reqs/segundo ---")
        request_count = 0
        start_time_throughput = current_time

    time.sleep(1.5)