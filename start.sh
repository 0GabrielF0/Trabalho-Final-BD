#!/bin/bash

set -e

cd ..

echo "Removendo arquivos originais..."
rm -rf streamlit mongodb

echo "Copiando novos arquivos..."
cp -r Trabalho-Final-BD/app ./streamlit
cp -r Trabalho-Final-BD/data ./mongodb

echo "Configurando permissões..."
cd streamlit
chmod +x start.sh stop.sh

echo ""
echo "Instalação concluída com sucesso!"

echo""
echo "Iniciando ambiente ..."

# Garante que a rede existe
docker network create mybridge 2>/dev/null || echo "--- Rede 'mybridge' verificada."

# Inicia MongoDB
echo "Iniciando MongoDB"
cd ../mongodb
chmod +x wait-for-it.sh
docker-compose up -d


# Aguarda o MongoDB
./wait-for-it.sh localhost 27017 echo "MongoDB disponível"

cd ../streamlit

# Inicia Streamlit
echo "Subindo Dashboard"
docker-compose up --build -d

echo ""
echo "Ambiente pronto!"
echo ""
echo "Segure Ctrl e Clique no link abaixo:"
echo "http://localhost:8501"
echo ""
echo "Mongo Express: http://localhost:8081"
