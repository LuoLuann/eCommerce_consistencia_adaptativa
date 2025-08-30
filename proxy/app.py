from flask import Flask, request, jsonify
import redis
import os
import logging

app = Flask(__name__)

# Configuração para logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Conexão com o Redis
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-master'), port=6379, db=0, decode_responses=True)

NUM_REPLICAS_FOR_STRONG = 1 
WAIT_TIMEOUT_MS = 1000

@app.route('/write', methods=['POST'])
def write_data():
    try:
        data = request.get_json()
        key = data['key']
        value = data['value']
        consistency = data.get('consistency', 'eventual')

        if consistency == 'strong':
            redis_client.set(key, value)
            replicas_acked = redis_client.wait(NUM_REPLICAS_FOR_STRONG, WAIT_TIMEOUT_MS)

            if replicas_acked >= NUM_REPLICAS_FOR_STRONG:
                return jsonify({"status": "success", "consistency": "strong", "replicas_acked": replicas_acked}), 200
            else:
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