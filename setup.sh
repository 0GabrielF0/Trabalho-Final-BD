#!/bin/bash

set -e

cd ..

echo "Removendo arquivos originais..."
rm -rf streamlit mongodb

echo "Copiando novos arquivos..."
cp -r Trabalho-Final-BD/app ./streamlit
cp -r Trabalho-Final-BD/data ./mongodb

echo "Removendo arquivos de instalação..."
rm -rf Trabalho-Final-BD

echo "Configurando permissões..."
cd streamlit
chmod +x start.sh stop.sh

echo ""
echo "Instalação concluída com sucesso!"
echo "Você está agora na pasta: $(pwd)"
echo ""
echo "Para iniciar o ambiente, execute:"
echo "    bash start.sh"