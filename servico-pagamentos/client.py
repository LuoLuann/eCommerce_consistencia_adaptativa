import requests
import time
import random
import csv
from datetime import datetime

PROXY_URL = "http://proxy:5000/write"

# --- Configuração do CSV ---
now = datetime.now()
file_name = f"pagamentos_{now.strftime('%Y-%m-%d_%H-%M')}.csv"
csv_file = open(file_name, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['timestamp', 'latency_seconds', 'consistency_type', 'success'])

# --- Configuração do Throughput ---
request_count = 0
start_time_throughput = time.time()

print(f"Iniciando serviço de Pagamentos. Métricas serão salvas em {file_name}")


while True:
    transaction_id = f"txn_{random.randint(100000, 999999)}"
    payment_data = {
        "order_id": f"ord_{random.randint(1000, 9999)}",
        "amount": round(random.uniform(20.50, 500.0), 2),
        "status": "approved"
    }
    success = False
    
    start_time_latency = time.time()
    
    try:
        response = requests.post(PROXY_URL, json={
            "key": transaction_id,
            "value": str(payment_data),
            "consistency": "strong"
        }, timeout=5)
        
        response.raise_for_status()
        success = True
        print(f"Serviço de Pagamentos: Requisição FORTE para a chave {transaction_id} bem-sucedida.")

    except requests.exceptions.RequestException as e:
        print(f"!!! Erro no Serviço de Pagamentos: {e}")
        
    finally:
        end_time_latency = time.time()
        latency = end_time_latency - start_time_latency
        timestamp = datetime.now().isoformat()
        
        csv_writer.writerow([timestamp, f"{latency:.4f}", "strong", success])
        csv_file.flush()

        request_count += 1
        
    # Calcula e exibe o throughput a cada 10 segundos
    current_time = time.time()
    elapsed_time = current_time - start_time_throughput
    if elapsed_time >= 10:
        throughput = request_count / elapsed_time
        print(f"--- Throughput de Pagamentos: {throughput:.2f} reqs/segundo ---")
        request_count = 0
        start_time_throughput = current_time

    time.sleep(4)