# Experimento de Consistência Adaptativa com Redis

Este projeto simula um ambiente de microserviços de e-commerce para avaliar o impacto de diferentes níveis de consistência (Forte vs. Eventual) em métricas de performance como latência, vazão (throughput), erros e conflitos de dados.

O ambiente é orquestrado com Docker Compose e utiliza um cluster Redis (Master/Replica) para persistência de dados.

## Pré-requisitos

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

## Estrutura do Projeto

-   **/proxy**: Um proxy em Flask que atua como gateway, recebendo requisições dos clientes e aplicando a lógica de consistência antes de escrever no Redis.
-   **/client_runner**: Contém o cliente padronizado que simula as requisições dos serviços. A lógica de qual serviço simular é definida dinamicamente.
-   **/logs**: Diretório onde os resultados dos experimentos (arquivos `.csv`) são salvos.
-   **/graficos**: Diretório onde os gráficos gerados pela análise são salvos.
-   `docker-compose.yml`: Arquivo principal que define e orquestra todos os serviços do ambiente.
-   `analise.py`: Script em Python para processar os arquivos de log e gerar gráficos de performance.

## Como Executar o Experimento

A execução é feita em um ambiente Docker Swarm para permitir a replicação dinâmica dos clientes.

### 1. Inicialize o Docker Swarm

Se esta for a primeira vez que você está usando o Swarm, execute este comando. Você só precisa fazer isso uma vez.
```bash
docker swarm init
```

### 2. Construa as Imagens Docker

Este comando irá construir as imagens para o proxy e para o cliente padronizado, com base nos `Dockerfile`s do projeto.
```bash
docker-compose build
```


### 3. Inicie o Experimento
Use o comando stack deploy para iniciar todos os serviços definidos no docker-compose.yml.

```bash
docker stack deploy -c docker-compose.yml meu_experimento
```
Os contêineres dos clientes executarão seus testes e, ao final, salvarão os logs e se encerrarão.

### 4.  Como Configurar Novos Experimentos
Para reiniciar ou começar um novo experimento com parâmetros diferentes, basta editar o arquivo docker-compose.yml.

Modificando Parâmetros
Abra o docker-compose.yml e localize os serviços dos clientes (ex: avaliacoes, pedidos, etc.). Você pode alterar:

Número de Clientes: Mude o valor de replicas para aumentar ou diminuir o número de instâncias de um serviço.

Nível de Consistência: Altere a variável de ambiente CONSISTENCY_TYPE para 'strong' ou 'eventual'.

Carga de Trabalho: Ajuste NUM_REQUESTS (número de requisições) e SLEEP_INTERVAL (intervalo em segundos entre elas).


#### Reiniciando o Experimento
Após salvar suas alterações no docker-compose.yml:

Pare a execução atual:

```Bash
docker stack rm meu_experimento
```
Reimplante a stack com as novas configurações:

```Bash

docker stack deploy -c docker-compose.yml meu_experimento
```
(Não é necessário rodar docker-compose build novamente, a menos que você tenha alterado o código-fonte de algum serviço).

### 5. Visualizando os Resultados
Arquivos de Log: Os resultados brutos de cada cliente são salvos em arquivos .csv dentro da pasta ./logs.

Análise Gráfica: Para gerar os gráficos de latência, vazão, erros e conflitos, execute o script de análise:

```Bash
python analise.py
```
O script irá encontrar os subdiretórios de cenários dentro de /logs, pedir para você escolher qual analisar, e salvará as imagens dos gráficos na pasta /graficos.