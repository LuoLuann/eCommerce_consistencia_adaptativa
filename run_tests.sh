#!/bin/bash

# --- Configurações dos Testes ---
declare -a REPLICAS=("1" "2" "3")
declare -a CONSISTENCY_MODES=("strong" "eventual" "dynamic")
declare -a REQUEST_LOADS=("1000" "10000" "20000")

# --- Loop Principal de Testes ---
for replicas in "${REPLICAS[@]}"; do
  for mode in "${CONSISTENCY_MODES[@]}"; do
    for load in "${REQUEST_LOADS[@]}"; do

      # --- Nome do Cenário ---
      SCENARIO_NAME="replicas_${replicas}/${mode}/${load}k"
      echo "========================================================================="
      echo "EXECUTANDO CENÁRIO: $SCENARIO_NAME"
      echo "========================================================================="

      # --- Criação do Diretório de Logs ---
      LOG_DIR="./logs/$SCENARIO_NAME"
      mkdir -p "$LOG_DIR"

      # --- Exportação das Variáveis de Ambiente ---
      export NUM_REPLICAS=$replicas
      export CONSISTENCY_TYPE=$mode
      export NUM_REQUESTS=$load
      export LOG_DIR_CLIENTS=$LOG_DIR # Passa o diretório de log para o docker-compose

      # --- Inicia o Docker Swarm (necessário para 'deploy') ---
      docker swarm init 2>/dev/null || true

      # --- Executa o Docker Compose ---
      echo "Subindo os containers..."
      docker-compose up -d --build

      # --- Aguarda a finalização dos clientes ---
      echo "Aguardando a finalização dos testes dos clientes..."
      # A lógica é esperar que os containers 'client_runner' parem de executar
      while [ "$(docker ps -q -f name=ecommerce_consistencia_adaptativa_avaliacoes)" ] || \
            [ "$(docker ps -q -f name=ecommerce_consistencia_adaptativa_catalogo)" ] || \
            [ "$(docker ps -q -f name=ecommerce_consistencia_adaptativa_pagamentos)" ] || \
            [ "$(docker ps -q -f name=ecommerce_consistencia_adaptativa_pedidos)" ]; do
        sleep 10
        echo " - Ainda aguardando..."
      done

      echo "Testes finalizados. Derrubando os containers..."
      docker-compose down

      # --- Limpa o estado do Swarm ---
      docker swarm leave --force 2>/dev/null

      echo "CENÁRIO $SCENARIO_NAME FINALIZADO."
      echo "========================================================================="
      echo ""
      sleep 5 # Pequeno intervalo entre os testes

    done
  done
done

echo "TODOS OS CENÁRIOS DE TESTE FORAM EXECUTADOS."