# Dashboard de Vendas Olist - Big Data

Este projeto realiza a integração entre um dashboard Streamlit e um banco de dados MongoDB para visualização de dados de e-commerce. O sistema conta com scripts de automação para deploy e carga inicial de dados (auto-seeding) a partir de arquivos CSV.

## Guia de Instalação e Deploy

Siga os passos abaixo para configurar o ambiente do zero no servidor.

### 1. Preparação do Ambiente

Execute os comandos abaixo para garantir permissões e preparar o diretório.

Nota: Execute como root ou utilize sudo se necessário.

```bash
sudo su -

# Certifique-se de estar no diretório /opt/
chown -R labihc ceub-bigdata

cd ceub-bigdata
```

### 2. Clonagem e Atualização dos Arquivos

Clone o repositório e execute o script de instalação

```bash
git clone https://github.com/0GabrielF0/Trabalho-Final-BD.git

cd Trabalho-Final-BD

bash setup.sh
```

### 3. Execução do Projeto

Utilize o script automatizado para subir todo o ambiente.

```bash
bash start.sh
```

## Estrutura do Repositório
```
.
├── setup.sh                        # Script de automação para instalação
├── mongodb/
│   ├── docker-compose.yml          # Configuração dos serviços MongoDB e Mongo Express
│   └── wait-for-it.sh              # Utilitário de rede para aguardar o banco
└── streamlit/
    ├── app.py                      # Código principal da aplicação Dashboard
    ├── start.sh                    # Script de inicialização (gerencia rede, banco e app)
    ├── stop.sh                     # Script para encerrar todos os serviços
    └── data_processed/
        └── dataset_final_simple.csv # Arquivo CSV para carga inicial
```

## Acesso aos Serviços

Após a execução do `start.sh`, os serviços estarão disponíveis nos seguintes endereços:

| Serviço | URL | Credenciais (se houver) |
| :--- | :--- | :--- |
| **Dashboard Olist** | `http://localhost:8501` | - |
| **Mongo Express** | `http://localhost:8081` | **User:** admin / **Pass:** pass |

## Parar o Ambiente
Para derrubar todos os containers de forma organizada:

```bash
cd streamlit
bash stop.sh
```
