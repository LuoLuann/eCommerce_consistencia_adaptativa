import requests
import time
import random

PROXY_URL = "http://proxy:5000/write"

while True:
    try:
        # Gera dados de exemplo para uma transação de pagamento
        transaction_id = f"txn_{random.randint(100000, 999999)}"
        payment_data = {
            "order_id": f"ord_{random.randint(1000, 9999)}",
            "amount": round(random.uniform(20.50, 500.0), 2),
            "status": "approved"
        }
        
        print(f"Serviço de Pagamentos: Enviando transação FORTE para a chave {transaction_id}")
        
        # Envia a requisição ao proxy, exigindo consistência forte
        response = requests.post(PROXY_URL, json={
            "key": transaction_id,
            "value": str(payment_data),
            "consistency": "strong"
        }, timeout=5) # Adiciona um timeout na chamada do cliente
        
        response.raise_for_status() # Lança um erro se a resposta for 4xx ou 5xx

    except requests.exceptions.RequestException as e:
        print(f"!!! Erro no Serviço de Pagamentos: {e}")
        
    # Simula uma nova transação de pagamento a cada 4 segundos
    time.sleep(4)