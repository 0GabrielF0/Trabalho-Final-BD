#!/bin/bash

echo "Parando serviços..."

# Derruba Streamlit
cd streamlit
docker-compose down

# Derruba MongoDB
cd ../mongodb
docker-compose down
cd ../streamlit

echo "Todos os serviços foram encerrados."
