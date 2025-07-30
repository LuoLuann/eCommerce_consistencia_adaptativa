import requests
import random
import time

PROXY_URL = "http://proxy:5000/write"

while True:
    try:
        key = f"order:{random.randint(1000, 9999)}"
        value = {"item": "livro", "quantidade": 1}

        print(f"Serviço de Pedidos: Enviando requisição FORTE para a chave {key}")
        response = requests.post(PROXY_URL, json={
            "key": key,
            "value": str(value),
            "consistency": "strong"
        }, timeout=5)

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Erro no serviço de pedidos: {e}")

    time.sleep(5) # Gera uma requisição forte a cada 5 segundos