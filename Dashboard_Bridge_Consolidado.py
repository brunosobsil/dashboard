import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Configuração da página
st.set_page_config(page_title="📊 Dashboard Ministério BRIDGE - 2025", layout="wide")

# Definir a localidade para português do Brasil
#locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
locale.setlocale(locale.LC_TIME, 'pt_BR')

# Carregar os dados com cache para otimização de performance
@st.cache_data
def load_data():
    file_path = "Consolidado_Bridge_2025.xlsx"
    df = pd.read_excel(file_path, sheet_name="2025 Consolidado")
    df["Quando"] = pd.to_datetime(df["Quando"], dayfirst=True)
    return df

df = load_data()

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
decisoes_count = filtered_df["Decisão"].value_counts().reset_index()
decisoes_count.columns = ["Tipo de Decisão", "Quantidade"]
fig1 = px.pie(decisoes_count, names="Tipo de Decisão", values="Quantidade", 
              title="📊 Distribuição das Decisões",
              color_discrete_sequence=["#2297EF"])
fig1.update_traces(textinfo='percent+label')
st.plotly_chart(fig1, use_container_width=True)

# Gráfico de linha - Evolução das decisões ao longo do tempo
df_time = filtered_df.groupby("Quando").size().reset_index(name="Quantidade")
df_time["Quando"] = df_time["Quando"].dt.strftime('%d/%m/%y')  # Formatar as datas
fig2 = px.line(df_time, x="Quando", y="Quantidade", 
               title="📅 Evolução das Decisões ao Longo do Tempo",
               markers=True, line_shape='spline', text="Quantidade")
fig2.update_layout(xaxis=dict(tickmode='linear'))
fig2.update_traces(textposition='top center', texttemplate='%{y}')
st.plotly_chart(fig2, use_container_width=True)

# Gráfico de barras - Distribuição das decisões por bairro
fig3 = px.bar(filtered_df, x="Bairro", title="📍 Distribuição das Decisões por Bairro",
              color_discrete_sequence=["#2297EF"])
st.plotly_chart(fig3, use_container_width=True)

# Gráfico de pizza - Percentual das decisões por bairro
bairro_count = filtered_df["Bairro"].value_counts().reset_index()
bairro_count.columns = ["Bairro", "Quantidade"]

# Agrupar os bairros que não estão no top 25 em "Outros"
top_25_bairros = bairro_count.head(25)
outros = pd.DataFrame([{'Bairro': 'Outros', 'Quantidade': bairro_count['Quantidade'][25:].sum()}])
bairro_count = pd.concat([top_25_bairros, outros], ignore_index=True)

fig4 = px.pie(bairro_count, names="Bairro", values="Quantidade", 
              title="📊 Percentual das Decisões por Bairro",
              color_discrete_sequence=px.colors.sequential.Blues)
fig4.update_traces(textinfo='percent+label')
st.plotly_chart(fig4, use_container_width=True)

# Adicionar espaçamento abaixo do gráfico de pizza
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# Exibir dados em formato de tabela interativa
with st.expander("🔍 Ver Dados Detalhados"):
    st.dataframe(filtered_df)