import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Constrói o caminho. BASE_DIR -> ".." (sobe para tema5-visualizacao) -> data_processed
FILE_PATH = os.path.join(BASE_DIR, "..", "data_processed", "dataset_final_simple.csv")

@st.cache_data
def load_data():
  return pd.read_csv(FILE_PATH, low_memory=False)

df = load_data()
# Converter datas
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

st.set_page_config(page_title="Dashboard Olist", layout="wide")
st.title("📊 Dashboard de Vendas – Olist")

# ============================================================
# Métricas principais
# ============================================================

# Faturamento Total (corrigido)
total_revenue = df["payment_value_total"].sum()

# Número de pedidos
num_orders = df["order_id"].nunique()

# Nota média
avg_review = df["review_score"].mean()

col1, col2, col3 = st.columns(3)

col1.metric("💰 Faturamento Total", f"R$ {total_revenue:,.2f}")
col2.metric("📦 Total de Pedidos", num_orders)
col3.metric("⭐ Nota Média", f"{avg_review:.2f}")

# ============================================================
# Distribuição de tipos de pagamento
# ============================================================
col_cat = "payment_types"
col_val = "payment_value_total"

if col_cat in df.columns and col_val in df.columns:

    # Preparar quantidade
    counts = df[col_cat].value_counts().reset_index()
    counts.columns = ["payment_types", "Quantidade"]

    # Preparar receita
    revenue = (
        df.groupby(col_cat)[col_val]
        .sum()
        .reset_index()
        .rename(columns={col_val: "Receita"})
    )

    # Juntar tudo
    merged = counts.merge(revenue, on="payment_types")
    merged = merged.sort_values("Receita", ascending=False)

    fig = go.Figure()
    # Barras — Quantidade
    fig.add_trace(
        go.Bar(
            x=merged["payment_types"],
            y=merged["Quantidade"],
            name="Quantidade",
        )
    )

    # Linha — Receita
    fig.add_trace(
        go.Scatter(
            x=merged["payment_types"],
            y=merged["Receita"],
            mode="lines+markers",
            name="Receita (R$)",
            yaxis="y2"
        )
    )

    fig.update_layout(
        title="Quantidade vs Receita por Método de Pagamento",
        xaxis=dict(title="Payment Types"),
        yaxis=dict(title="Quantidade"),
        yaxis2=dict(
            title="Receita (R$)",
            overlaying="y",
            side="right"
        ),
        height=550,
        legend=dict(x=1.01, y=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info(f"As colunas '{col_cat}' ou '{col_val}' não existem no dataset.")

# ============================================================
# Faturamento por mês
# ============================================================
st.subheader("📈 Faturamento por Mês")

revenue_by_month = (
    df.groupby(df["order_purchase_timestamp"].dt.to_period("M"))["payment_value_total"]
    .sum()
    .reset_index()
)

revenue_by_month["order_purchase_timestamp"] = revenue_by_month["order_purchase_timestamp"].astype(str)

fig1 = px.line(
    revenue_by_month,
    x="order_purchase_timestamp",
    y="payment_value_total",
    labels={"order_purchase_timestamp": "Mês", "payment_value_total": "Faturamento (R$)"},
)

st.plotly_chart(fig1, use_container_width=True)

# ============================================================
#   Nota média por mês
# ============================================================
st.subheader("⭐ Evolução da Nota Média")

review_by_month = (
    df.groupby(df["order_purchase_timestamp"].dt.to_period("M"))["review_score"]
    .mean()
    .reset_index()
)

review_by_month["order_purchase_timestamp"] = review_by_month["order_purchase_timestamp"].astype(str)

fig3 = px.bar(
    review_by_month,
    x="order_purchase_timestamp",
    y="review_score",
    labels={"order_purchase_timestamp": "Mês", "review_score": "Nota Média"},
)

st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# Proporção de Pedidos por Status
# ============================================================
st.subheader("Proporção de Pedidos por Status")

# Contagem de pedidos por status
status_counts = df["order_status"].value_counts()

# Selecionar top 3 categorias + "Outros"
top3 = status_counts.nlargest(3)
outros = status_counts.sum() - top3.sum()
status_final = pd.concat([top3, pd.Series({"Outros": outros})]).reset_index()
status_final.columns = ["Status", "Quantidade"]

fig_bar = px.bar(
    status_final,
    x="Quantidade",
    y="Status",
    orientation='h',
    color="Status",
    text="Quantidade",
    color_discrete_sequence=px.colors.qualitative.Pastel
)

fig_bar.update_layout(
    height=400,
    yaxis=dict(autorange="reversed"),
    showlegend=False
)
fig_bar.update_traces(textposition='outside')

st.plotly_chart(fig_bar, use_container_width=True)

