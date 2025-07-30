import requests
import time
import random

PROXY_URL = "http://proxy:5000/write"

while True:
    try:
        # Gera dados de exemplo para uma avaliação de produto
        review_id = f"review_{random.randint(10000, 99999)}"
        review_data = {
            "product_id": f"item{random.randint(1, 10)}",
            "user_id": f"user{random.randint(1, 100)}",
            "rating": random.randint(1, 5)
        }
        
        print(f"Serviço de Avaliações: Enviando avaliação EVENTUAL para a chave {review_id}")

        # Envia a requisição ao proxy, utilizando consistência eventual
        response = requests.post(PROXY_URL, json={
            "key": review_id,
            "value": str(review_data),
            "consistency": "eventual"
        }, timeout=2)

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"!!! Erro no Serviço de Avaliações: {e}")

    # Gera uma nova avaliação a cada 1.5 segundos
    time.sleep(1.5)