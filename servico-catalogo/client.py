import requests
import timeout
import random

PROXY_URL = "http://proxy:5000/write"

while True:
    try:
        key = f"product_view:item{random.randint(1, 10)}"
        value = random.randint(1, 1000)

        print(f"Serviço de Catálogo: Enviando requisição EVENTUAL para a chave {key}")

        requests.post(PROXY_URL, json={
            "key": key,
            "value": str(value),
            "consistency": "eventual"
        })
    except requests.exceptions.RequestException as e:
        print(f"Erro no serviço de cataloogo: {e}")

    time.sleep(0.5) # Gera uma requisição forte a cada 5 segundos