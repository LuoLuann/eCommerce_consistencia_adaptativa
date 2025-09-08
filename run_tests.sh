#!/bin/bash

# --- Configurações dos Testes ---
declare -a REPLICAS=("1" "2" "3")
declare -a CONSISTENCY_MODES=("strong" "eventual" "dynamic")

# Carga POR CLIENTE (Total = Carga x 20)
declare -a REQUESTS_PER_CLIENT=("100" "400" "800")
# Nomes para as pastas de log, refletindo a CARGA TOTAL
declare -a TOTAL_LOAD_NAMES=("5000k" "20000k" "40000k")

# --- Loop Principal de Testes ---
for replicas in "${REPLICAS[@]}"; do
  for mode in "${CONSISTENCY_MODES[@]}"; do
    for i in "${!REQUESTS_PER_CLIENT[@]}"; do

      # Extrai a carga por cliente e o nome da carga total
      load_per_client=${REQUESTS_PER_CLIENT[i]}
      total_load_name=${TOTAL_LOAD_NAMES[i]}

      # --- Nome do Cenário ---
      SCENARIO_NAME="replicas_${replicas}/${mode}/total_${total_load_name}"
      echo "========================================================================="
      echo "EXECUTANDO CENÁRIO: $SCENARIO_NAME"
      echo "Total de Geradores de Carga: 20"
      echo "Requisições por gerador: $load_per_client"
      echo "========================================================================="

      # --- Criação do Diretório de Logs ---
      LOG_DIR_ABSOLUTE="$(pwd)/logs/$SCENARIO_NAME"
      mkdir -p "$LOG_DIR_ABSOLUTE"
      echo "Diretório de log: $LOG_DIR_ABSOLUTE"

      # --- Exportação das Variáveis de Ambiente ---
      export NUM_REPLICAS=$replicas
      export CONSISTENCY_TYPE=$mode
      export NUM_REQUESTS=$load_per_client # Passa a carga por cliente
      export LOG_DIR_CLIENTS=$LOG_DIR_ABSOLUTE

      # --- Inicia o Docker Swarm ---
      docker swarm init 2>/dev/null || true

      # --- PASSO 1: Sobe a infraestrutura (proxy, redis) em background ---
      echo "Subindo a infraestrutura (proxy, redis)..."
      docker-compose up -d --build redis-master redis-replica proxy

      echo "Aguardando o proxy ficar disponível..."
      sleep 15

      # --- PASSO 2: Executa os 20 clientes (5 serviços x 4 réplicas) e aguarda a finalização ---
      echo "Iniciando os 20 clientes e aguardando a conclusão dos testes..."
      docker-compose up --build --remove-orphans avaliacoes catalogo pagamentos pedidos carrinho

      # --- PASSO 3: Derruba todo o ambiente ---
      echo "Testes finalizados. Derrubando todos os containers..."
      docker-compose down

      # --- Limpa o estado do Swarm ---
      docker swarm leave --force 2>/dev/null

      echo "CENÁRIO $SCENARIO_NAME FINALIZADO."
      echo "========================================================================="
      echo ""
      sleep 5

    done
  done
done

echo "TODOS OS CENÁRIOS DE TESTE FORAM EXECUTADOS."