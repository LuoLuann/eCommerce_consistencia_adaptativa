from flask import Flask, request, jsonify
import redis
import os
import logging
import time
from threading import Lock

app = Flask(__name__)

# --- CONFIGURAÇÕES GERAIS ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-master'), port=6379, db=0, decode_responses=True)

# --- CONFIGURAÇÕES DE CONSISTÊNCIA ---

# Tipo de consistência forçada (strong, eventual) ou dinâmica.
# O padrão é 'dynamic' se a variável não for definida.
FORCED_CONSISTENCY = os.getenv('CONSISTENCY_TYPE', 'dynamic')

# Limiar para o modo dinâmico
THROUGHPUT_THRESHOLD = 100
TIME_WINDOW_SECONDS = 10

# Configurações para consistência forte
# O número de réplicas é lido do ambiente, com padrão 1.
NUM_REPLICAS_FOR_STRONG = int(os.getenv('NUM_REPLICAS_FOR_STRONG', 1))
WAIT_TIMEOUT_MS = 1000

# Variáveis globais para o modo dinâmico
request_count = 0
window_start_time = time.time()
lock = Lock()

def get_consistency_mode():
    """
    Decide o nível de consistência.
    Se um modo for forçado via variável de ambiente, o utiliza.
    Caso contrário, decide dinamicamente com base na vazão.
    """
    if FORCED_CONSISTENCY in ['strong', 'eventual']:
        return FORCED_CONSISTENCY

    # Lógica dinâmica original
    global request_count, window_start_time
    current_time = time.time()

    with lock:
        if current_time - window_start_time > TIME_WINDOW_SECONDS:
            window_start_time = current_time
            request_count = 0
        request_count += 1
        elapsed_time = current_time - window_start_time or 1
        current_throughput = request_count / elapsed_time

    if current_throughput > THROUGHPUT_THRESHOLD:
        print(f"VAZÃO ALTA DETECTADA ({current_throughput:.2f} rps). Usando consistência EVENTUAL.")
        return 'eventual'
    else:
        print(f"Vazão normal ({current_throughput:.2f} rps). Usando consistência STRONG.")
        return 'strong'

@app.route('/write', methods=['POST'])
def write_data():
    try:
        data = request.get_json()
        key = data['key']
        value = data['value']
        
        consistency = get_consistency_mode()

        if consistency == 'strong':
            redis_client.set(key, value)
            # Garante a escrita no número de réplicas configurado
            replicas_acked = redis_client.wait(NUM_REPLICAS_FOR_STRONG, WAIT_TIMEOUT_MS)

            if replicas_acked >= NUM_REPLICAS_FOR_STRONG:
                return jsonify({"status": "success", "consistency": "strong", "replicas_acked": replicas_acked}), 200
            else:
                return jsonify({"status": "error", "message": f"Write timeout: strong consistency failed. Replicas acked: {replicas_acked}"}), 503
        else: # 'eventual'
            redis_client.set(key, value)
            return jsonify({"status": "success", "consistency": "eventual"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# ... (o restante do arquivo /read e app.run continua igual)
@app.route('/read/<key>', methods=['GET'])
def read_data(key):
    try:
        value = redis_client.get(key)
        if value is not None:
            return jsonify({"key": key, "value": value}), 200
        else:
            return jsonify({"status": "error", "message": "Key not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)