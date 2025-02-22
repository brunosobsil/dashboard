import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Definir a localidade para português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Carregar os dados
def load_data():
    file_path = "Consolidado_Bridge_2025.xlsx"
    df = pd.read_excel(file_path, sheet_name="2025 Consolidado")
    df["Quando"] = pd.to_datetime(df["Quando"], dayfirst=True)
    return df

df = load_data()

# Substituir valores em branco, contendo apenas espaços ou a sequência de caracteres "--" na coluna "Bairro" por "Não informado"
df["Bairro"] = df["Bairro"].replace(r'^\s*$|--', 'Não informado', regex=True)

# Tabela interativa com filtros
st.sidebar.header("Filtros")
selected_decisao = st.sidebar.multiselect("Filtrar por Tipo de Decisão", df["Decisão"].unique(), placeholder="Selecione uma opção")

filtered_df = df.copy()
if selected_decisao:
    filtered_df = filtered_df[filtered_df["Decisão"].isin(selected_decisao)]
else:
    filtered_df = df

# Configurar o layout do dashboard
st.title("Dashboard Min. BRIDGE - 2025")

# Métricas principais
total_decisoes = filtered_df.shape[0]
total_contato_sucesso = filtered_df[filtered_df["Conseguiu fazer contato?"] == "Sim"].shape[0]
media_idade = round(filtered_df["Idade"].mean())
percentual_contato_sucesso = round((total_contato_sucesso / total_decisoes) * 100) if total_decisoes > 0 else 0

# Top 5 bairros com mais decisões (excluindo "Não informado")
top_bairros = filtered_df[filtered_df["Bairro"] != "Não informado"]["Bairro"].value_counts().head(5).reset_index()
top_bairros.columns = ["Bairro", "Quantidade"]
top_bairros.index = top_bairros.index + 1  # Ajustar o índice para começar em 1

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Decisões", total_decisoes)
col2.metric("Contatos Bem-Sucedidos", total_contato_sucesso)
col3.metric("% Contatos", f"{percentual_contato_sucesso}%")
col4.metric("Média de Idade", f"{media_idade} anos")

# Exibir os top 5 bairros com mais decisões
st.subheader("Top 5 Bairros com Mais Decisões")
st.table(top_bairros)

# Gráfico de barras - Decisões por tipo
decisoes_count = filtered_df["Decisão"].value_counts().reset_index()
decisoes_count.columns = ["Tipo de Decisão", "Quantidade"]
fig1 = px.bar(decisoes_count, x="Tipo de Decisão", y="Quantidade", 
              labels={"Tipo de Decisão": "Tipo de Decisão", "Quantidade": "Quantidade"},
              title="Distribuição das Decisões")
fig1.update_layout(xaxis_title="Tipo de Decisão", yaxis_title="Quantidade")
fig1.update_traces(texttemplate='%{y}', textposition='inside', textfont_color='white')
st.plotly_chart(fig1)

# Gráfico de linha - Evolução das decisões ao longo do tempo
df_time = filtered_df.groupby("Quando").size().reset_index(name="Quantidade")
fig2 = px.line(df_time, x="Quando", y="Quantidade", title="Evolução das Decisões ao Longo do Tempo")
st.plotly_chart(fig2)

# Mapa interativo - Distribuição das decisões por bairro
fig3 = px.histogram(filtered_df, x="Bairro", title="Distribuição das Decisões por Bairro")
fig3.update_layout(xaxis_title="Bairro", yaxis_title="Quantidade")
st.plotly_chart(fig3)

st.dataframe(filtered_df)