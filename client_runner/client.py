import requests
import time
import random
import csv
from datetime import datetime
import os
import json

print("--- SCRIPT DO CLIENTE INICIADO ---")

# --- DANDO UM TEMPO PARA OS OUTROS SERVIÇOS INICIAREM ---
time.sleep(5) 

# --- CONFIGURAÇÕES VINDAS DE VARIÁVEIS DE AMBIENTE ---
SERVICE_NAME = os.getenv("SERVICE_NAME", "default-service")
CONSISTENCY_TYPE = os.getenv("CONSISTENCY_TYPE", "eventual")
NUM_REQUESTS = int(os.getenv("NUM_REQUESTS", 1000))
SLEEP_INTERVAL = float(os.getenv("SLEEP_INTERVAL", 0.1))
NODE_ID = os.getenv("NODE_ID", "node-unknown")

PROXY_WRITE_URL = "http://proxy:5000/write"
PROXY_READ_URL = "http://proxy:5000/read"

# --- Configuração dos Arquivos de Log ---
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file_path = os.path.join(log_dir, f"{SERVICE_NAME}_{NODE_ID}_{timestamp_str}.csv")

print(f"Configurações carregadas para: {SERVICE_NAME} ({NODE_ID})")
print(f"Salvando logs em: {output_file_path}")


def generate_payload(service_name, index):
    """Gera um payload de exemplo baseado no nome do serviço."""
    if service_name == "pedidos":
        return f"order:{random.randint(1000, 9999)}", {"item": "livro", "quantidade": 1, "client_id": NODE_ID}
    elif service_name == "pagamentos":
        return f"txn_{random.randint(100000, 999999)}", {"order_id": f"ord_{random.randint(1000, 9999)}", "amount": round(random.uniform(20.50, 500.0), 2), "status": "approved", "client_id": NODE_ID}
    elif service_name == "catalogo":
        return f"product_view:item{random.randint(1, 10)}", {"view_count": random.randint(1, 1000), "client_id": NODE_ID}
    elif service_name == "avaliacoes":
        return f"{SERVICE_NAME}_{random.randint(10000, 99999)}", {"data": f"payload_{index}", "client_id": NODE_ID}
    else:
        return f"key_{index}", {"data": f"payload_{index}", "client_id": NODE_ID}

results = []
start_time_total = time.time()

print(f"Iniciando loop de {NUM_REQUESTS} requisições para o serviço '{SERVICE_NAME}'.")

try:
    for i in range(NUM_REQUESTS):
        key, value = generate_payload(SERVICE_NAME, i)
        success = False
        error_msg = ""
        conflict_detected = False
        
        old_value = None
        try:
            read_response = requests.get(f"{PROXY_READ_URL}/{key}", timeout=5)
            if read_response.status_code == 200:
                old_value = read_response.json().get("value")
        except requests.exceptions.RequestException:
            pass 

        start_time_latency = time.time()
        
        try:
            write_response = requests.post(PROXY_WRITE_URL, json={
                "key": key,
                "value": json.dumps(value),
                "consistency": CONSISTENCY_TYPE
            }, timeout=10)
            write_response.raise_for_status()
            success = True
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"!!! ERRO NA REQUISIÇÃO para {SERVICE_NAME}: {error_msg}")

        end_time_latency = time.time()
        latency_ms = (end_time_latency - start_time_latency) * 1000
        
        if old_value is not None and old_value != json.dumps(value):
            conflict_detected = True

        results.append({
            "timestamp": datetime.now().isoformat(),
            "service": SERVICE_NAME,
            "consistency": CONSISTENCY_TYPE,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_msg,
            "conflict_detected": conflict_detected
        })

        if (i + 1) % (NUM_REQUESTS / 10) == 0:
            print(f"Serviço {SERVICE_NAME} ({NODE_ID}): Progresso - {i+1}/{NUM_REQUESTS} requisições enviadas.")
        
        time.sleep(SLEEP_INTERVAL)

finally:
    print(f"--- BLOCO FINALLY ALCANÇADO para {SERVICE_NAME} ({NODE_ID}) ---")
    end_time_total = time.time()
    total_duration = end_time_total - start_time_total
    
    if results:
        print(f"Salvando {len(results)} resultados no arquivo CSV...")
        with open(output_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"Resultados de {SERVICE_NAME} ({NODE_ID}) salvos em {output_file_path}")
    else:
        print("Nenhum resultado para salvar. O arquivo CSV não será criado.")
    
    print(f"--- {SERVICE_NAME} ({NODE_ID}) Finalizado ---")