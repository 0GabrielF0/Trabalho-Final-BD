import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(
    page_title="Dashboard Olist",
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
    .section-title { margin: 8px 0 4px 0; color: #e5e7eb; font-weight: 700; letter-spacing: 0.3px; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Caminho do dataset
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#FILE_PATH = os.path.join(BASE_DIR, "..", "data_processed", "dataset_final_simple.csv")
FILE_PATH = os.path.join(BASE_DIR, "data_processed", "dataset_final_simple.csv")

# ----------------------------
# Carga de dados
# ----------------------------
@st.cache_data(show_spinner=True)
def load_data(path: str):
    return pd.read_csv(path, low_memory=False)

try:
    df = load_data(FILE_PATH)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado em: {FILE_PATH}. Coloque o CSV em data_processed/ e recarregue.")
    st.stop()

# ----------------------------
# Pré-processamento
# ----------------------------
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
df["order_purchase_date"] = df["order_purchase_timestamp"].dt.date
df["year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)

# Normalizar colunas categóricas para evitar tipos mistos no sorted()
df["payment_types"] = df["payment_types"].fillna("not_defined").astype(str)
df["order_status"] = df["order_status"].fillna("not_defined").astype(str)

# ----------------------------
# Sidebar - filtros
# ----------------------------
st.sidebar.header("Filtros")
min_date, max_date = df["order_purchase_date"].min(), df["order_purchase_date"].max()
date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
selected_status = st.sidebar.multiselect(
    "Status do pedido",
    options=sorted(df["order_status"].unique()),
    default=sorted(df["order_status"].unique()),
)
selected_payments = st.sidebar.multiselect(
    "Métodos de pagamento",
    options=sorted(df["payment_types"].unique()),
    default=sorted(df["payment_types"].unique()),
)

# Aplica filtros
df_f = df.copy()
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_f = df_f[(df_f["order_purchase_timestamp"] >= start_d) & (df_f["order_purchase_timestamp"] <= end_d)]
df_f = df_f[df_f["order_status"].isin(selected_status)]
df_f = df_f[df_f["payment_types"].isin(selected_payments)]

# ----------------------------
# KPIs
# ----------------------------
total_revenue = df_f["payment_value_total"].sum()
num_orders = df_f["order_id"].nunique()
avg_review = df_f["review_score"].mean()

st.title("📊 Dashboard de Vendas – Olist")
st.caption("Visualização e exploração – Tema 5")

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("💰 Faturamento Total", f"R$ {total_revenue:,.2f}")
kpi2.metric("📦 Total de Pedidos", f"{num_orders:,}")
kpi3.metric("⭐ Nota Média", f"{avg_review:.2f}")

st.markdown("---")

# ----------------------------
# Gráfico: Quantidade vs Receita por pagamento
# ----------------------------
col_cat = "payment_types"
col_val = "payment_value_total"
if col_cat in df_f.columns and col_val in df_f.columns:
    counts = df_f[col_cat].value_counts().reset_index()
    counts.columns = ["payment_types", "Quantidade"]
    revenue = (
        df_f.groupby(col_cat)[col_val]
        .sum()
        .reset_index()
        .rename(columns={col_val: "Receita"})
    )
    merged = counts.merge(revenue, on="payment_types").sort_values("Receita", ascending=False)

    fig_pay = go.Figure()
    fig_pay.add_trace(
        go.Bar(
            x=merged["payment_types"],
            y=merged["Quantidade"],
            name="Quantidade",
            marker_color="#38bdf8",
        )
    )
    fig_pay.add_trace(
        go.Scatter(
            x=merged["payment_types"],
            y=merged["Receita"],
            mode="lines+markers",
            name="Receita (R$)",
            yaxis="y2",
            marker=dict(color="#fbbf24", size=8),
            line=dict(color="#fbbf24", width=3),
        )
    )
    fig_pay.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        title="Quantidade vs Receita por Método de Pagamento",
        xaxis=dict(title="Payment Types"),
        yaxis=dict(title="Quantidade"),
        yaxis2=dict(title="Receita (R$)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=520,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_pay, use_container_width=True)
else:
    st.info(f"As colunas '{col_cat}' ou '{col_val}' não existem no dataset.")

st.markdown("---")

# ----------------------------
# Séries temporais: Faturamento e Nota
# ----------------------------
left, right = st.columns(2)

# Faturamento por mês
revenue_by_month = (
    df_f.groupby(df_f["order_purchase_timestamp"].dt.to_period("M"))["payment_value_total"]
    .sum()
    .reset_index()
)
revenue_by_month["order_purchase_timestamp"] = revenue_by_month["order_purchase_timestamp"].astype(str)

fig_rev = px.line(
    revenue_by_month,
    x="order_purchase_timestamp",
    y="payment_value_total",
    labels={"order_purchase_timestamp": "Mês", "payment_value_total": "Faturamento (R$)"},
    markers=True,
    template="plotly_dark",
)
fig_rev.update_traces(line_color="#22d3ee")
fig_rev.update_layout(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#0f172a",
    height=400,
    margin=dict(t=40, b=40),
)

# Nota média por mês
review_by_month = (
    df_f.groupby(df_f["order_purchase_timestamp"].dt.to_period("M"))["review_score"]
    .mean()
    .reset_index()
)
review_by_month["order_purchase_timestamp"] = review_by_month["order_purchase_timestamp"].astype(str)

fig_revscore = px.bar(
    review_by_month,
    x="order_purchase_timestamp",
    y="review_score",
    labels={"order_purchase_timestamp": "Mês", "review_score": "Nota Média"},
    template="plotly_dark",
    color_discrete_sequence=["#fbbf24"],
)
fig_revscore.update_layout(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#0f172a",
    height=400,
    margin=dict(t=40, b=40),
    yaxis=dict(range=[0, max(5, review_by_month["review_score"].max() + 0.5)]),
)

with left:
    st.subheader("📈 Faturamento por Mês")
    st.plotly_chart(fig_rev, use_container_width=True)
with right:
    st.subheader("⭐ Evolução da Nota Média")
    st.plotly_chart(fig_revscore, use_container_width=True)

st.markdown("---")

# ----------------------------
# Proporção de Status
# ----------------------------
st.subheader("🚚 Proporção de Pedidos por Status")
status_counts = df_f["order_status"].value_counts()
top3 = status_counts.nlargest(3)
outros = status_counts.sum() - top3.sum()
status_final = pd.concat([top3, pd.Series({"Outros": outros})]).reset_index()
status_final.columns = ["Status", "Quantidade"]

fig_status = px.bar(
    status_final,
    x="Quantidade",
    y="Status",
    orientation="h",
    color="Status",
    text="Quantidade",
    template="plotly_dark",
    color_discrete_sequence=px.colors.sequential.Blues_r,
)
fig_status.update_layout(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#0f172a",
    height=380,
    yaxis=dict(autorange="reversed"),
    showlegend=False,
    margin=dict(t=30, b=30),
)
fig_status.update_traces(textposition="outside")

st.plotly_chart(fig_status, use_container_width=True)