from flask import Flask, request, jsonify
import redis
import os

app = Flask(__name__)

# Conecta ao Redis. O nome 'redis-master' é resolvido pelo Docker Compose.
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-master'), port=6379, db=0, decode_responses=True)

# Define o número de réplicas que devem confirmar a escrita para consistência forte.
# Em nosso ambiente com 1 master e 1 réplica, esperamos a confirmação de 1 réplica.
NUM_REPLICAS_FOR_STRONG = 1 
WAIT_TIMEOUT_MS = 1000

@app('/write', method=['POST'])
def write_data():
    try:
        data = request.get_json()
        key = data['key']
        value = data['value']
        consistency = data.get('consistency', 'eventual') # Padrão é eventual

        if consistency == 'strong':
            # Fluxo de consistência forte
            # 1. Escreva no nó primário
            redis_client.set(key, value)

            # 2. Aguarda a confirmação da replicação
            # O comando WAIT retorna o número de réplicas que confirmaram a escrita.
            replicas_acked = redis_client.wait(NUM_REPLICAS_FOR_STRONG, WAIT_TIMEOUT_MS)

            if replicas_acked >= NUM_REPLICAS_FOR_STRONG:
                return jsonify({"status": "success", "consistency": "strong", "replicas_acked": replicas_acked}), 200
            else 
                # Se o timeout for atingido, retorna erro.
                return jsonify({"status": "error", "message": "Write timeout: strong consistency guarantes failed"}), 503
        else
            # --- FLUXO DE CONSISTÊNCIA EVENTUAL ---
            # Apenas escreve no primário e retorna sucesso imediatamente.
            redis_client.set(key, value)
            return jsonify({"status": "success", "consistency": "eventual"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)