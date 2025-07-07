import streamlit as st
import pandas as pd
import plotly.express as px
from babel.dates import format_datetime
from datetime import datetime
import io

# Configuração da página
st.set_page_config(page_title="📊 Dashboard Ministério BRIDGE - 2025", layout="wide")

# Função para formatar datas sem depender de locale do sistema
def formatar_data(data):
    return format_datetime(data, "EEEE, d 'de' MMMM 'de' yyyy", locale='pt_BR')

@st.cache_data
def load_data():
    file_path = "Consolidado_Bridge_2025.xlsx"
    df = pd.read_excel(file_path, sheet_name="2025 Consolidado")
    df["Quando"] = pd.to_datetime(df["Quando"], dayfirst=True)

    # Normalizar a coluna "Conseguiu fazer contato?"
    df["Conseguiu fazer contato?"] = (
        df["Conseguiu fazer contato?"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"sim": "Sim", "não": "Não", "nao": "Não"})
        .fillna("Não informado")
    )

    return df

@st.cache_data
def load_start_data():
    file_path = "Paricipantes_Start.xlsx"
    df = pd.read_excel(file_path)
    return df

df = load_data()
df_start = load_start_data()

# Limpeza de dados
df["Bairro"] = df["Bairro"].replace(r'^\s*$|--', 'Não informado', regex=True)

# Estilização do Sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
            color: white !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select {
            color: white !important;
        }
        span[data-baseweb="tag"] {
            background-color: #2297EF !important;
        }
        .spacer {
            margin-bottom: 150px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar para Filtros
st.sidebar.header("🎯 Filtros")
selected_decisao = st.sidebar.multiselect("📌 Filtrar por Tipo de Decisão", df["Decisão"].unique(), placeholder="Selecione uma opção")
filtered_df = df[df["Decisão"].isin(selected_decisao)] if selected_decisao else df

# Exibir logo
st.image("images/logo.svg", width=200)

st.title("Dashboard Ministério BRIDGE - 2025")

# Calcular a data mais recente do arquivo Excel
data_mais_recente = df["Quando"].max().strftime('%d/%m/%Y')

# Adicionar subtítulo com o período
st.markdown(f"### Período: 01/01/2025 até {data_mais_recente}")

st.markdown("---")

# Métricas principais
total_decisoes = filtered_df.shape[0]
total_contato_sucesso = filtered_df[filtered_df["Conseguiu fazer contato?"] == "Sim"].shape[0]
media_idade = round(filtered_df["Idade"].mean())
percentual_contato_sucesso = round((total_contato_sucesso / total_decisoes) * 100) if total_decisoes > 0 else 0

# Top 5 bairros com mais decisões
top_bairros = filtered_df[filtered_df["Bairro"] != "Não informado"]["Bairro"].value_counts().head(5).reset_index()
top_bairros.columns = ["Bairro", "Quantidade"]
top_bairros.index = top_bairros.index + 1

# Layout de métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("📝 Total de Decisões", total_decisoes)
col2.metric("📞 Contatos Bem-Sucedidos", total_contato_sucesso)
col3.metric("📊 % Contatos", f"{percentual_contato_sucesso}%")
col4.metric("🎂 Média de Idade", f"{media_idade} anos")

# Exibir os top 5 bairros com mais decisões
st.subheader("🏙️ Top 5 Bairros com Mais Decisões")
st.table(top_bairros)

# Gráfico de pizza - Decisões por tipo
#decisoes_count = filtered_df["Decisão"].value_counts().reset_index()
#decisoes_count.columns = ["Tipo de Decisão", "Quantidade"]
#fig1 = px.pie(decisoes_count, names="Tipo de Decisão", values="Quantidade", 
#              title="📊 Distribuição das Decisões",
#              color_discrete_sequence=["#2297EF"])
#fig1.update_traces(textinfo='percent+label')
#st.plotly_chart(fig1, use_container_width=True)

decisoes_count = filtered_df["Decisão"].value_counts().reset_index()
decisoes_count.columns = ["Tipo de Decisão", "Quantidade"]

# Gráficos de pizza - Decisões por tipo (quantidade e percentual)
col1, col2 = st.columns(2)

with col1:
    fig_pizza_qtd = px.pie(
        decisoes_count,
        names="Tipo de Decisão",
        values="Quantidade",
        title="📊 Distribuição das Decisões (Quantidade)",
        color_discrete_sequence=px.colors.sequential.PuBu  # tons de azul suaves
    )
    fig_pizza_qtd.update_traces(textinfo='label+value')
    st.plotly_chart(fig_pizza_qtd, use_container_width=True)

with col2:
    fig_pizza_pct = px.pie(
        decisoes_count,
        names="Tipo de Decisão",
        values="Quantidade",
        title="📊 Distribuição das Decisões (Percentual)",
        color_discrete_sequence=px.colors.sequential.Blues  # tons de azul mais fortes
    )
    fig_pizza_pct.update_traces(textinfo='label+percent')
    st.plotly_chart(fig_pizza_pct, use_container_width=True)

# Gráfico de barras - Distribuição das decisões por bairro
bairro_count_sorted = filtered_df[filtered_df["Bairro"] != "Não informado"]["Bairro"].value_counts().reset_index()
bairro_count_sorted.columns = ["Bairro", "Quantidade"]
bairro_count_sorted = bairro_count_sorted.sort_values(by="Quantidade", ascending=False).head(10)
fig3 = px.bar(bairro_count_sorted, x="Bairro", y="Quantidade", title="📍 Distribuição das Decisões por Bairro",
              color_discrete_sequence=["#2297EF"], text="Quantidade")
fig3.update_traces(textposition='inside')
fig3.update_layout(height=int((fig3.layout.height or 400) * 1.05))
st.plotly_chart(fig3, use_container_width=True)

# Gráfico de pizza - Percentual das decisões por bairro
bairro_count = bairro_count_sorted.head(10)
fig4 = px.pie(bairro_count, names="Bairro", values="Quantidade", 
              title="📊 Percentual das Decisões por Bairro",
              color_discrete_sequence=px.colors.sequential.Blues)
fig4.update_traces(textinfo='percent+label')
fig4.update_layout(height=int((fig4.layout.height or 400) * 1.05))
st.plotly_chart(fig4, use_container_width=True)

# Adicionar espaçamento abaixo do gráfico de pizza
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# Evolução mensal de novos começos
st.subheader("🚀 Evolução Mensal de Novos Começos")

# Garantir que a coluna de datas está em datetime
df["Quando"] = pd.to_datetime(df["Quando"], dayfirst=True)

# Agrupar por mês
df["AnoMes"] = df["Quando"].dt.to_period("M").astype(str)
novos_comecos_mensal = df.groupby("AnoMes").size().reset_index(name="Quantidade")

# Criar gráfico
fig_evolucao_ano = px.line(novos_comecos_mensal, x="AnoMes", y="Quantidade",
                    title="📈 Novos Começos por Mês",
                    markers=True, line_shape='spline', text="Quantidade",
                    labels={"AnoMes": "Mês", "Quantidade": "Novos Começos"},
                    color_discrete_sequence=["#2297EF"])

fig_evolucao_ano.update_traces(textposition="top center", texttemplate="%{y}")
fig_evolucao_ano.update_layout(xaxis_tickangle=-45)
fig_evolucao_ano.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=novos_comecos_mensal["AnoMes"],
        ticktext=novos_comecos_mensal["AnoMes"],
        tickangle=-45
    )
)

fig_evolucao_ano.update_traces(textposition="top center", texttemplate="%{y}")

st.plotly_chart(fig_evolucao_ano, use_container_width=True)

# 🙌 Evolução mensal de decisões "Aceitou Jesus"
st.subheader("🙌 Evolução Mensal de Decisões: Aceitou Jesus")

# Filtrar apenas os registros com decisão "Aceitou Jesus"
df_aceitou = filtered_df[filtered_df["Decisão"].str.lower().str.strip() == "aceitou jesus"]

# Agrupar por mês
df_aceitou["AnoMes"] = df_aceitou["Quando"].dt.to_period("M").astype(str)
aceitou_mensal = df_aceitou.groupby("AnoMes").size().reset_index(name="Quantidade")

# Gráfico de linha
fig_aceitou = px.line(
    aceitou_mensal,
    x="AnoMes",
    y="Quantidade",
    title="📈 Aceitaram Jesus por Mês",
    markers=True,
    line_shape="spline",
    text="Quantidade",
    labels={"AnoMes": "Mês", "Quantidade": "Aceitaram Jesus"},
    color_discrete_sequence=["#1B77D3"]
)
fig_aceitou.update_traces(textposition="top center", texttemplate="%{y}")
fig_aceitou.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=aceitou_mensal["AnoMes"],
        ticktext=aceitou_mensal["AnoMes"],
        tickangle=-45
    )
)

st.plotly_chart(fig_aceitou, use_container_width=True)

# 📞 Evolução mensal de contatos bem-sucedidos
st.subheader("📞 Evolução Mensal de Contatos Bem-Sucedidos")

# Criar coluna Mês/Ano
df["AnoMes"] = df["Quando"].dt.to_period("M").astype(str)

# Agrupar por mês e resposta
contato_mensal = df.groupby(["AnoMes", "Conseguiu fazer contato?"]).size().reset_index(name="Quantidade")

# Pivotar para gráfico de barras
pivot_qtd = contato_mensal.pivot(index="AnoMes", columns="Conseguiu fazer contato?", values="Quantidade").fillna(0)
pivot_qtd["Total"] = pivot_qtd.sum(axis=1)
pivot_qtd = pivot_qtd.reset_index()

# Gráfico de barras com quantidades
fig_contato_qtd = px.bar(
    pivot_qtd,
    x="AnoMes",
    y=["Sim", "Não"],
    title="📊 Contatos por Mês - Quantidade",
    labels={"value": "Quantidade", "AnoMes": "Mês", "variable": "Contato"},
    barmode="group",
    color_discrete_map={"Sim": "#2297EF", "Não": "#08519C"},
    text_auto=True
)
fig_contato_qtd.update_traces(textposition="inside")
fig_contato_qtd.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=pivot_qtd["AnoMes"],
        ticktext=pivot_qtd["AnoMes"],
        tickangle=-45
    )
)
st.plotly_chart(fig_contato_qtd, use_container_width=True)

# Calcular percentuais
pivot_pct = pivot_qtd.copy()
pivot_pct["Sim %"] = (pivot_pct["Sim"] / pivot_pct["Total"] * 100).round(1)
pivot_pct["Não %"] = (pivot_pct["Não"] / pivot_pct["Total"] * 100).round(1)

# Gráfico de barras com percentuais
fig_contato_pct = px.bar(
    pivot_pct,
    x="AnoMes",
    y=["Sim %", "Não %"],
    title="📊 Contatos por Mês - Percentual",
    labels={"value": "Percentual (%)", "AnoMes": "Mês", "variable": "Contato"},
    barmode="group",
    color_discrete_map={"Sim %": "#2297EF", "Não %": "#08519C"},
    text_auto=True
)
fig_contato_pct.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=pivot_pct["AnoMes"],
        ticktext=pivot_pct["AnoMes"],
        tickangle=-45
    ),
    yaxis=dict(ticksuffix='%')
)
st.plotly_chart(fig_contato_pct, use_container_width=True)

#########
# START #
#########

# df_merged = df.merge(df_start, left_on="Chave", right_on="Telefone", how="left", indicator=True)
# df_participantes_start = df_merged[df_merged["_merge"] == "both"]

# total_participantes_start = df_participantes_start.shape[0]
# total_participantes_start_geral = df_start.shape[0]

# total_contato_sucesso_start = df_participantes_start[df_participantes_start["Conseguiu fazer contato?"] == "Sim"].shape[0]

# percentual_participantes_start = round((total_participantes_start / total_contato_sucesso_start) * 100) if df.shape[0] > 0 else 0

# percentual_contato_sucesso_start = round((total_contato_sucesso_start / total_participantes_start_geral) * 100) if total_participantes_start_geral > 0 else 0

# # Top bairros dos participantes do Start
# top_bairros_start = df_participantes_start[df_participantes_start["Bairro"] != "Não informado"]["Bairro"].value_counts().head(5).reset_index()
# top_bairros_start.columns = ["Bairro", "Quantidade"]
# top_bairros_start.index = top_bairros_start.index + 1

# st.subheader("📊 Análise dos Participantes do Start x Contatos Bridge")
# col1, col2 = st.columns(2)
# col1.metric("🎓 Total de Participantes do Start", total_participantes_start_geral)
# col2.metric("📊 % Contatados pelo Bridge que fizeram o Start", f"{percentual_participantes_start}%")

# col3, col4 = st.columns(2)
# col3.metric("📞 Contatados pelo Bridge", total_contato_sucesso_start)
# col4.metric("📊 % Contatados pelo Bridge x Total de Participantes do Start", f"{percentual_contato_sucesso_start}%")

# # Gráfico de barras - Participantes do Start contatados pelo Bridge por Bairro
# fig_start_bairros = px.bar(top_bairros_start, x="Bairro", y="Quantidade", title="📍 Participantes do Start contatados pelo Bridge por Bairro",
#               color_discrete_sequence=["#2297EF"], text="Quantidade")
# fig_start_bairros.update_traces(textposition='outside')
# st.plotly_chart(fig_start_bairros, use_container_width=True)

# # Gráfico de pizza - Percentual de Participantes do Start contatados pelo Bridge por Bairro
# fig_start_pizza = px.pie(top_bairros_start, names="Bairro", values="Quantidade", 
#               title="📊 Percentual de Participantes do Start contatados pelo Bridge por Bairro",
#               color_discrete_sequence=px.colors.sequential.Blues)
# fig_start_pizza.update_traces(textinfo='percent+label')
# st.plotly_chart(fig_start_pizza, use_container_width=True)

# # Gráfico de funil - Contatos bem-sucedidos vs. Participantes do Start
# fig_funnel = px.funnel(pd.DataFrame({
#     "Categoria": ["Total Contatos Sucesso", "Participantes do Start Contato Sucesso"],
#     "Quantidade": [total_contato_sucesso, total_contato_sucesso_start]
# }), x="Quantidade", y="Categoria", title="📉 Contatos Sucesso vs. Start")
# st.plotly_chart(fig_funnel, use_container_width=True)

# # Exibir dados em formato de tabela interativa
# with st.expander("🔍 Ver Dados Detalhados do Bridge"):
#     st.dataframe(filtered_df)

# # Exibir dados em formato de tabela interativa
# with st.expander("🔍 Ver Dados Detalhados do Bridge x Start"):
#     st.dataframe(df_participantes_start)