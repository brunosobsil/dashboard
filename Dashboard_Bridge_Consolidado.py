import streamlit as st
import pandas as pd
import plotly.express as px
from babel.dates import format_datetime
from datetime import datetime
import io
import unicodedata  # <-- adicionado para normalização de espaços/unicode

# Configuração da página
st.set_page_config(page_title="📊 Dashboard Ministério BRIDGE - 2026", layout="wide")

# Função para formatar datas sem depender de locale do sistema
def formatar_data(data):
    return format_datetime(data, "EEEE, d 'de' MMMM 'de' yyyy", locale='pt_BR')

@st.cache_data
def load_data():
    file_path = "Consolidado_Bridge_2026.xlsx"
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

# Normalizar "Decisão" para evitar categorias duplicadas (case/acentos/espaços invisíveis)
def _norm_text_label(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", str(s))
    s = (s
         .replace("\u00A0", " ")   # NBSP
         .replace("\u2007", " ")   # figure space
         .replace("\u202F", " ")   # narrow NBSP
         .replace("\u200b", ""))   # zero-width space
    s = " ".join(s.split()).strip()

    # padroniza para comparação (sem perder o "bonito" final)
    key = s.casefold()

    mapa = {
        "aceitou jesus": "Aceitou Jesus",
        "reconciliou com jesus": "Reconciliou com Jesus",
        "pedido de oração": "Pedido de oração",
        "pedido de oracao": "Pedido de oração",
    }
    return mapa.get(key, s)

df["Decisão"] = (
    df["Decisão"]
    .apply(_norm_text_label)
    .replace(r"^\s*$|^--$", "Não informado", regex=True)
)

# Limpeza de dados — normalização global do Bairro (resolve duplicados como 'Copacabana' x 'Copacabana ')
def _norm_unicode_spaces(s: str) -> str:
    if s is None:
        return ""
    # normaliza forma Unicode (NFC), troca NBSP e espaços estreitos por espaço comum e colapsa múltiplos
    s = unicodedata.normalize("NFC", str(s))
    s = (s
         .replace("\u00A0", " ")   # NBSP
         .replace("\u2007", " ")   # figure space
         .replace("\u202F", " "))  # narrow no-break space
    s = " ".join(s.split())
    return s.strip()

df["Bairro"] = (
    df["Bairro"]
    .apply(_norm_unicode_spaces)
    .replace(r"^\s*$|^--$", "Não informado", regex=True)
)

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

# ============================================
# 📦 ANÁLISE POR FAIXAS ETÁRIAS — NOVOS COMEÇOS
# (colado ao final do arquivo, sem alterar o anterior)
# ============================================

st.markdown("---")
st.header("👥 Análise de Novos Começos por Faixa Etária")

# Cópia e preparação
df_nc = df.copy()
df_nc["Idade"] = pd.to_numeric(df_nc["Idade"], errors="coerce")
df_nc = df_nc.dropna(subset=["Idade", "Quando"])

# Garantir datetime e coluna AnoMes
df_nc["Quando"] = pd.to_datetime(df_nc["Quando"], dayfirst=True, errors="coerce")
df_nc = df_nc.dropna(subset=["Quando"])
df_nc["AnoMes"] = df_nc["Quando"].dt.to_period("M").astype(str)

# ===== FAIXAS AJUSTADAS =====
bins = [0, 8, 12, 17, 26, 39, 49, 59, 100]
labels = [
    "Kids (0–8)",
    "Connect (9–12)",
    "Nexteen (13–17)",
    "Next (18–26)",
    "Next 27+ (27–39)",
    "40+ (40–49)",
    "50+ (50–59)",
    "60+ (60–100)"
]
df_nc["Faixa Etária"] = pd.cut(
    df_nc["Idade"], bins=bins, labels=labels, right=True, include_lowest=True
)

# Remover idades fora das faixas (NaN após o cut)
df_nc = df_nc.dropna(subset=["Faixa Etária"])

# ================================
# 1) Distribuição pelo total (faixa)
# ================================
st.subheader("🎂 Distribuição por Faixa Etária (Total de Novos Começos)")

# Contagens base (garante todas as faixas)
counts = df_nc["Faixa Etária"].value_counts()
dist_faixa = pd.DataFrame({"Faixa Etária": labels})
dist_faixa["Quantidade"] = dist_faixa["Faixa Etária"].map(counts).fillna(0)
dist_faixa["Quantidade"] = pd.to_numeric(dist_faixa["Quantidade"], errors="coerce").fillna(0).astype(int)

total_nc = int(dist_faixa["Quantidade"].sum())
if total_nc == 0:
    dist_faixa["Percentual"] = 0.0
else:
    dist_faixa["Percentual"] = (dist_faixa["Quantidade"].astype(float) / float(total_nc) * 100).round(1)

# 👉 Ordenar da maior para a menor (esquerda -> direita)
dist_faixa_ord_qtd = dist_faixa.sort_values("Quantidade", ascending=False).reset_index(drop=True)
ordem_categorias_qtd = dist_faixa_ord_qtd["Faixa Etária"].tolist()

colA, colB = st.columns([3, 2], gap="large")
with colA:
    fig_faixa_total = px.bar(
        dist_faixa_ord_qtd,
        x="Faixa Etária",
        y="Quantidade",
        text="Quantidade",
        title="🏷️ Novos Começos por Faixa Etária (Quantidade)",
        category_orders={"Faixa Etária": ordem_categorias_qtd},
        color_discrete_sequence=["#2297EF"]
    )
    # Texto DENTRO; adiciona anotação externa para barras pequenas
    fig_faixa_total.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)
    fig_faixa_total.update_layout(
        xaxis_tickangle=-15,
        yaxis_title="Quantidade",
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )
    limiar_qtd = 15
    for _, row in dist_faixa_ord_qtd.iterrows():
        if row["Quantidade"] < limiar_qtd and row["Quantidade"] > 0:
            fig_faixa_total.add_annotation(
                x=row["Faixa Etária"],
                y=row["Quantidade"] + max(1, int(limiar_qtd * 0.15)),
                text=str(row["Quantidade"]),
                showarrow=False,
                xanchor="center",
                yanchor="bottom",
                font=dict(size=11)
            )
    st.plotly_chart(fig_faixa_total, use_container_width=True)

# 👉 Participação por faixa (%) — barras HORIZONTAIS com lógica híbrida (texto dentro p/ grandes, fora p/ pequenas)
with colB:
    dist_faixa_ord_pct = dist_faixa.sort_values("Percentual", ascending=False).reset_index(drop=True)

    # Texto interno só para barras >= limiar; pequenas ficam vazias e recebem anotação externa
    limiar_pct = 4.0  # ajuste fino do que é “pequeno” para seu layout
    dist_faixa_ord_pct["TextoPercentual"] = dist_faixa_ord_pct["Percentual"].apply(
        lambda v: f"{v:.1f}%" if v >= limiar_pct else ""
    )

    fig_faixa_pct = px.bar(
        dist_faixa_ord_pct,
        x="Percentual",
        y="Faixa Etária",
        orientation="h",
        text="TextoPercentual",
        title="📊 Participação por Faixa (%)",
        color_discrete_sequence=["#2297EF"]
    )
    fig_faixa_pct.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)

    max_pct = float(dist_faixa_ord_pct["Percentual"].max() if not dist_faixa_ord_pct.empty else 0)
    # range maior para caber as anotações externas
    fig_faixa_pct.update_layout(
        xaxis=dict(title="Percentual (%)", ticksuffix="%", range=[0, max(10, max_pct + 6)]),
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=110, r=10, t=60, b=40),
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )

    # Anotações externas para barras pequenas
    offset = max(0.6, max_pct * 0.02)
    for _, row in dist_faixa_ord_pct.iterrows():
        if 0 < row["Percentual"] < limiar_pct:
            fig_faixa_pct.add_annotation(
                x=row["Percentual"] + offset,
                y=row["Faixa Etária"],
                text=f"{row['Percentual']:.1f}%",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=11)
            )

    st.plotly_chart(fig_faixa_pct, use_container_width=True)

# =========================================
# 2) Distribuição por bairros (Top 10 bairros)
# =========================================
st.subheader("🏙️ Distribuição por Bairros (Top 10) — Por Faixa Etária")

# Normalizar bairro (já normalizado globalmente acima; mantém fallback para valores vazios)
df_nc["Bairro"] = df_nc["Bairro"].replace(r'^\s*$|--', 'Não informado', regex=True).fillna("Não informado")

# Top 10 bairros por total de novos começos
top_bairros_nc = (
    df_nc[df_nc["Bairro"] != "Não informado"]
    .groupby("Bairro")
    .size()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
    .head(10)
)

# 🔎 Seletor de faixas para reduzir legenda (padrão: Top 5 por quantidade)
faixas_por_qtd = dist_faixa.sort_values("Quantidade", ascending=False)["Faixa Etária"].tolist()
default_faixas = faixas_por_qtd[:5] if len(faixas_por_qtd) >= 5 else faixas_por_qtd
faixas_escolhidas = st.multiselect(
    "Filtrar faixas exibidas (bairros)", options=labels, default=default_faixas
)

bairro_faixa = (
    df_nc[(df_nc["Bairro"].isin(top_bairros_nc["Bairro"])) & (df_nc["Faixa Etária"].isin(faixas_escolhidas))]
    .groupby(["Bairro", "Faixa Etária"])
    .size()
    .reset_index(name="Quantidade")
)

# Ordenar bairros pelo total
bairro_order = top_bairros_nc.sort_values("Total", ascending=False)["Bairro"].tolist()

fig_bairro_stack = px.bar(
    bairro_faixa,
    x="Bairro",
    y="Quantidade",
    color="Faixa Etária",
    category_orders={"Bairro": bairro_order, "Faixa Etária": faixas_escolhidas},
    barmode="stack",
    text="Quantidade",
    title="📍 Top 10 Bairros — Novos Começos Por Faixa Etária"
)

# rótulos mais curtos só para a LEGENDA (sem mexer nos dados)
legend_name_map = {
    "Next 27+ (27–39)": "Next 27+",
    "Next (18–26)": "Next 18–26",
    "Nexteen (13–17)": "Nexteen",
    "Connect (9–12)": "Connect",
    "Kids (0–8)": "Kids",
    "40+ (40–49)": "40+",
    "50+ (50–59)": "50+",
    "60+ (60–100)": "60+",
}
fig_bairro_stack.for_each_trace(
    lambda t: t.update(
        name=legend_name_map.get(t.name, t.name),
        legendgroup=legend_name_map.get(t.name, t.name)
    )
)

fig_bairro_stack.update_traces(textposition="inside", cliponaxis=False)

# legenda otimizada para mobile: horizontal, multi-linha, abaixo do gráfico
fig_bairro_stack.update_layout(
    xaxis_tickangle=-30,
    yaxis_title="Quantidade",
    legend=dict(
        orientation="h",
        title_text="Faixa",
        yanchor="top", y=-0.22,   # abaixo do chart
        xanchor="left", x=0,
        font=dict(size=11),
        itemsizing="trace",
        itemwidth=70,             # ajuda a quebrar em mais linhas em telas estreitas
        tracegroupgap=8
    ),
    margin=dict(t=90, b=110)      # espaço para a legenda embaixo
)
st.plotly_chart(fig_bairro_stack, use_container_width=True)


# =========================================
# 3) Evolução mensal por faixa (linhas)
# =========================================
st.subheader("📈 Evolução Mensal de Novos Começos — Por Faixa Etária")

evolucao_faixa_mensal = (
    df_nc.groupby(["AnoMes", "Faixa Etária"])
    .size()
    .reset_index(name="Quantidade")
)

# 🔎 Seletor de faixas para a evolução (padrão: Top 5 por quantidade total no período)
faixas_total_periodo = (
    evolucao_faixa_mensal.groupby("Faixa Etária")["Quantidade"].sum().sort_values(ascending=False).index.tolist()
)
default_faixas_evo = faixas_total_periodo[:5] if len(faixas_total_periodo) >= 5 else faixas_total_periodo
faixas_evo_escolhidas = st.multiselect(
    "Filtrar faixas exibidas (evolução mensal)", options=labels, default=default_faixas_evo
)

evo_filtrado = evolucao_faixa_mensal[evolucao_faixa_mensal["Faixa Etária"].isin(faixas_evo_escolhidas)]

# Ordem cronológica do eixo X
meses_ordem = sorted(evo_filtrado["AnoMes"].unique().tolist())

fig_evo_linhas = px.line(
    evo_filtrado,
    x="AnoMes",
    y="Quantidade",
    color="Faixa Etária",
    category_orders={"Faixa Etária": faixas_evo_escolhidas, "AnoMes": meses_ordem},
    markers=True,
    title="⏱️ Novos Começos por Mês e por Faixa Etária"
)

# rótulos mais curtos para a legenda
legend_name_map = {
    "Next 27+ (27–39)": "Next 27+",
    "Next (18–26)": "Next 18–26",
    "Nexteen (13–17)": "Nexteen",
    "Connect (9–12)": "Connect",
    "Kids (0–8)": "Kids",
    "40+ (40–49)": "40+",
    "50+ (50–59)": "50+",
    "60+ (60–100)": "60+",
}
fig_evo_linhas.for_each_trace(
    lambda t: t.update(
        name=legend_name_map.get(t.name, t.name),
        legendgroup=legend_name_map.get(t.name, t.name)
    )
)

fig_evo_linhas.update_traces(mode="lines+markers", line=dict(width=2))
fig_evo_linhas.update_layout(
    xaxis=dict(
        tickangle=-45,
        tickmode="array",
        tickvals=meses_ordem,
        ticktext=meses_ordem
    ),
    yaxis_title="Quantidade",
    legend=dict(
        orientation="h",
        title_text="Faixa",
        yanchor="top", y=-0.25,   # posiciona abaixo
        xanchor="left", x=0,
        font=dict(size=11),
        itemsizing="trace",
        itemwidth=70,             # ajuda a quebrar linhas
        tracegroupgap=8
    ),
    margin=dict(t=90, b=120),     # espaço extra para legenda embaixo
    hovermode="x unified"
)
st.plotly_chart(fig_evo_linhas, use_container_width=True)


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
