from flask import Flask, request, jsonify
import redis
import os
import logging
import time
from threading import Lock

app = Flask(__name__)

# Configuração para logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Conexão com o Redis
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-master'), port=6379, db=0, decode_responses=True)

# --- CONFIGURAÇÕES PARA CONSISTÊNCIA DINÂMICA ---

# Se a vazão (requests/segundo) for maior que este valor, usaremos consistência eventual.
THROUGHPUT_THRESHOLD = 100 
# Janela de tempo em segundos para calcular a vazão.
TIME_WINDOW_SECONDS = 10

# Variáveis globais para rastrear a vazão
request_count = 0
window_start_time = time.time()
lock = Lock() # Lock para garantir a segurança em ambiente com múltiplas threads

NUM_REPLICAS_FOR_STRONG = 1 
WAIT_TIMEOUT_MS = 1000

def get_dynamic_consistency():
    """
    Decide o nível de consistência com base na vazão atual.
    """
    global request_count, window_start_time
    
    current_time = time.time()
    
    with lock:
        # Verifica se a janela de tempo expirou e reseta se necessário
        if current_time - window_start_time > TIME_WINDOW_SECONDS:
            window_start_time = current_time
            request_count = 0

        request_count += 1
        
        # Calcula a vazão atual (requests por segundo)
        elapsed_time = current_time - window_start_time
        if elapsed_time == 0:
            elapsed_time = 1 # Evita divisão por zero
            
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
        
        # A decisão de consistência é tomada dinamicamente pelo proxy
        consistency = get_dynamic_consistency()

        if consistency == 'strong':
            redis_client.set(key, value)
            replicas_acked = redis_client.wait(NUM_REPLICAS_FOR_STRONG, WAIT_TIMEOUT_MS)

            if replicas_acked >= NUM_REPLICAS_FOR_STRONG:
                return jsonify({"status": "success", "consistency": "strong", "replicas_acked": replicas_acked}), 200
            else:
                # Se a escrita forte falhar, podemos opcionalmente tentar uma escrita eventual como fallback
                # redis_client.set(key, value)
                # return jsonify({"status": "fallback", "consistency": "eventual", "message": "Strong consistency failed, fell back to eventual"}), 200
                return jsonify({"status": "error", "message": "Write timeout: strong consistency guarantees failed"}), 503
        else:
            redis_client.set(key, value)
            return jsonify({"status": "success", "consistency": "eventual"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

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