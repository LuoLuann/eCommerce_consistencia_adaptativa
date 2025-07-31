import requests
import random
import time
import csv
from datetime import datetime

PROXY_URL = "http://proxy:5000/write"

now = datetime.now()
file_name = f"pedidos_{now.strftime('%Y-%m-%d_%H-%M')}.csv"
csv_file = open(file_name, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['timestamp', 'latency_seconds', 'consistency_type', 'success'])

request_count = 0
start_time_throughput = time.time()

print(f"Iniciando serviço de Pedidos. Métricas serão salvas em {file_name}")

while True:
    key = f"order:{random.randint(1000, 9999)}"
    value = {"item": "livro", "quantidade": 1}
    success = False
    
    start_time_latency = time.time()
    
    try:
        response = requests.post(PROXY_URL, json={
            "key": key,
            "value": str(value),
            "consistency": "strong"
        }, timeout=5)

        response.raise_for_status()
        success = True
        print(f"Serviço de Pedidos: Requisição FORTE para a chave {key} bem-sucedida.")

    except requests.exceptions.RequestException as e:
        print(f"!!! Erro no serviço de pedidos: {e}")
    
    finally:
        end_time_latency = time.time()
        latency = end_time_latency - start_time_latency
        timestamp = datetime.now().isoformat()
        
        csv_writer.writerow([timestamp, f"{latency:.4f}", "strong", success])
        csv_file.flush() # Garante que os dados sejam escritos no disco
        
        request_count += 1

    current_time = time.time()
    elapsed_time = current_time - start_time_throughput
    if elapsed_time >= 10:
        throughput = request_count / elapsed_time
        print(f"--- Throughput de Pedidos: {throughput:.2f} reqs/segundo ---")
        request_count = 0
        start_time_throughput = current_time

    time.sleep(5)