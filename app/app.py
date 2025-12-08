import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(
    page_title="Dashboard Olist (MongoDB)",
    layout="wide",
    page_icon="📊",
)

st.markdown(
    """
    <style>
    .main { background-color: #0f172a; }
    .stMetric { background: #111827 !important; padding: 12px 16px; border-radius: 12px; border: 1px solid #1f2937; }
    h1, h2, h3, h4, h5, h6 { color: #e5e7eb; }
    .stMarkdown p, .stMarkdown span, .stMarkdown li { color: #cbd5e1 !important; }
    section[data-testid="stSidebar"] { background-color: #0b1220; border-right: 1px solid #1f2937; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Configuração MongoDB
# ----------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:mongo@mongo_service:27017/")
DB_NAME = "olist"
COLLECTION_NAME = "orders"
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_processed", "dataset_final_simple.csv")

@st.cache_resource
def get_mongo_client():
    """Cria e retorna o cliente MongoDB com timeout definido."""
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

def init_db(client):
    """Verifica se há dados no Mongo. Se vazio, carrega do CSV."""
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Verifica se a coleção está vazia
    if collection.count_documents({}) == 0:
        try:
            if os.path.exists(CSV_PATH):
                df_csv = pd.read_csv(CSV_PATH)
                
                # Converter datas para datetime nativo do Python/Mongo
                if "order_purchase_timestamp" in df_csv.columns:
                    df_csv["order_purchase_timestamp"] = pd.to_datetime(df_csv["order_purchase_timestamp"])
                
                # Tratar nulos para evitar erros de inserção
                df_csv = df_csv.fillna({
                    "payment_types": "not_defined",
                    "order_status": "not_defined"
                })

                data_dict = df_csv.to_dict("records")
                collection.insert_many(data_dict)
                return True, "Dados importados do CSV para o MongoDB com sucesso."
            else:
                return False, f"CSV não encontrado em {CSV_PATH} para carga inicial."
        except Exception as e:
            return False, f"Erro ao popular banco: {e}"
    return True, "Banco de dados já populado."

@st.cache_data(ttl=300)
def load_data_from_mongo():
    """Busca todos os dados do MongoDB e converte para DataFrame."""
    client = get_mongo_client()
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Projeção: excluir _id para o DataFrame ficar limpo
    cursor = collection.find({}, {"_id": 0})
    df = pd.DataFrame(list(cursor))
    
    return df

# ----------------------------
# Inicialização e Carga
# ----------------------------
try:
    client = get_mongo_client()
    # Teste de conexão
    client.server_info()
    
    # Auto-seed (Carga inicial se necessário)
    status, msg = init_db(client)
    if not status:
        st.error(msg)
    
    df = load_data_from_mongo()

except ServerSelectionTimeoutError:
    st.error("❌ Não foi possível conectar ao MongoDB. Verifique se o container 'mongo_service' está rodando na rede 'mybridge'.")
    st.stop()
except Exception as e:
    st.error(f"Erro inesperado: {e}")
    st.stop()

if df.empty:
    st.warning("A coleção do MongoDB está vazia e o CSV não foi encontrado.")
    st.stop()

# ----------------------------
# Pré-processamento (Garante tipos após carga do Mongo)
# ----------------------------
# O Mongo retorna datetime, mas garantimos aqui caso venha string
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
df["order_purchase_date"] = df["order_purchase_timestamp"].dt.date
df["payment_types"] = df["payment_types"].astype(str)
df["order_status"] = df["order_status"].astype(str)

# ----------------------------
# Sidebar - filtros
# ----------------------------
st.sidebar.header("Filtros (MongoDB Source)")
min_date, max_date = df["order_purchase_date"].min(), df["order_purchase_date"].max()

date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

status_opts = sorted(df["order_status"].unique())
selected_status = st.sidebar.multiselect("Status do pedido", options=status_opts, default=status_opts)

pay_opts = sorted(df["payment_types"].unique())
selected_payments = st.sidebar.multiselect("Métodos de pagamento", options=pay_opts, default=pay_opts)

# Aplica filtros no DataFrame
df_f = df.copy()
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    # Ajuste para pegar o dia final completo
    end_d = end_d.replace(hour=23, minute=59, second=59)
    df_f = df_f[(df_f["order_purchase_timestamp"] >= start_d) & (df_f["order_purchase_timestamp"] <= end_d)]

df_f = df_f[df_f["order_status"].isin(selected_status)]
df_f = df_f[df_f["payment_types"].isin(selected_payments)]

# ----------------------------
# KPIs
# ----------------------------
total_revenue = df_f["payment_value_total"].sum()
num_orders = df_f["order_id"].nunique()
avg_review = df_f["review_score"].mean()

st.title("📊 Dashboard Olist (MongoDB Integration)")
st.caption("Dados extraídos da coleção 'orders' no MongoDB")

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("💰 Faturamento Total", f"R$ {total_revenue:,.2f}")
kpi2.metric("📦 Total de Pedidos", f"{num_orders:,}")
kpi3.metric("⭐ Nota Média", f"{avg_review:.2f}")

st.markdown("---")

# ----------------------------
# Gráficos (Mantidos originais)
# ----------------------------

# 1. Quantidade vs Receita
col_cat = "payment_types"
col_val = "payment_value_total"

if not df_f.empty:
    counts = df_f[col_cat].value_counts().reset_index()
    counts.columns = [col_cat, "Quantidade"]
    revenue = df_f.groupby(col_cat)[col_val].sum().reset_index().rename(columns={col_val: "Receita"})
    merged = counts.merge(revenue, on=col_cat).sort_values("Receita", ascending=False)

    fig_pay = go.Figure()
    fig_pay.add_trace(go.Bar(x=merged[col_cat], y=merged["Quantidade"], name="Quantidade", marker_color="#38bdf8"))
    fig_pay.add_trace(go.Scatter(x=merged[col_cat], y=merged["Receita"], mode="lines+markers", name="Receita (R$)", yaxis="y2", marker=dict(color="#fbbf24", size=8), line=dict(color="#fbbf24", width=3)))
    
    fig_pay.update_layout(
        template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        title="Quantidade vs Receita por Pagamento",
        xaxis=dict(title="Método"), yaxis=dict(title="Qtd"),
        yaxis2=dict(title="Receita", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.02, x=1), height=450
    )
    st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("---")

    # 2. Séries Temporais
    left, right = st.columns(2)
    
    # Agrupamento mensal
    rev_month = df_f.groupby(df_f["order_purchase_timestamp"].dt.to_period("M"))[col_val].sum().reset_index()
    rev_month["order_purchase_timestamp"] = rev_month["order_purchase_timestamp"].astype(str)
    
    fig_rev = px.line(rev_month, x="order_purchase_timestamp", y=col_val, markers=True, template="plotly_dark", title="Faturamento Mensal")
    fig_rev.update_traces(line_color="#22d3ee")
    fig_rev.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")

    rev_score_month = df_f.groupby(df_f["order_purchase_timestamp"].dt.to_period("M"))["review_score"].mean().reset_index()
    rev_score_month["order_purchase_timestamp"] = rev_score_month["order_purchase_timestamp"].astype(str)

    fig_score = px.bar(rev_score_month, x="order_purchase_timestamp", y="review_score", template="plotly_dark", title="Nota Média Mensal", color_discrete_sequence=["#fbbf24"])
    fig_score.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", yaxis=dict(range=[0, 5.5]))

    with left: st.plotly_chart(fig_rev, use_container_width=True)
    with right: st.plotly_chart(fig_score, use_container_width=True)

    st.markdown("---")

    # 3. Status
    st.subheader("🚚 Status dos Pedidos")
    status_c = df_f["order_status"].value_counts().nlargest(5).reset_index()
    status_c.columns = ["Status", "Qtd"]
    
    fig_st = px.bar(status_c, y="Status", x="Qtd", orientation="h", text="Qtd", template="plotly_dark", color="Status", color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_st.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", showlegend=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_st, use_container_width=True)

else:
    st.info("Nenhum dado encontrado para os filtros selecionados.")