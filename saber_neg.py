import pandas as pd
import plotly.graph_objects as go

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP  = ";"
COLUNA   = "glo_avg"

LABELS_MESES = {
    "2024-06": "Jun/24", "2024-07": "Jul/24", "2024-08": "Ago/24",
    "2024-09": "Set/24", "2024-10": "Out/24", "2024-11": "Nov/24",
    "2024-12": "Dez/24", "2025-01": "Jan/25", "2025-02": "Fev/25",
    "2025-03": "Mar/25", "2025-04": "Abr/25", "2025-05": "Mai/25",
}

# ── Pipeline de Dados ────────────────────────────────────────────────────────

def carregar_dados(path: str, sep: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, low_memory=False)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df[COLUNA] = pd.to_numeric(df[COLUNA], errors="coerce")
    
    # Extrai as informações de tempo
    df["mes"]  = df["timestamp_utc"].dt.to_period("M").astype(str)
    df["dia"]  = df["timestamp_utc"].dt.date
    df["hora"] = df["timestamp_utc"].dt.hour
    
    return df

def exibir_contagem_negativos(df: pd.DataFrame):
    """Calcula e imprime a quantidade de valores negativos por mês no terminal."""
    print("\n=== QUANTIDADE DE VALORES NEGATIVOS POR MÊS ===")
    
    # Conta totais por mês
    total_por_mes = df.groupby("mes").size().reset_index(name="total_registros")
    
    # Filtra e conta negativos por mês
    df_negativos = df[df[COLUNA] < 0]
    negativos_por_mes = df_negativos.groupby("mes").size().reset_index(name="qtd_negativos")
    
    # Mescla as duas tabelas para exibir lado a lado
    resumo = pd.merge(total_por_mes, negativos_por_mes, on="mes", how="left").fillna(0)
    resumo["qtd_negativos"] = resumo["qtd_negativos"].astype(int)
    
    # Calcula a porcentagem
    resumo["%_negativos"] = ((resumo["qtd_negativos"] / resumo["total_registros"]) * 100).round(1)
    
    print(resumo.to_string(index=False))
    print("===============================================\n")

def calcular_irradiacao(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a Irradiação Diária Média (Wh/m²/dia) de um DataFrame."""
    # 1. Energia da hora
    irr_hora = df.groupby(["mes", "dia", "hora"])[COLUNA].sum().div(60).reset_index()
    irr_hora.rename(columns={COLUNA: "energia"}, inplace=True)
    
    # 2. Média horária do mês
    med_hora = irr_hora.groupby(["mes", "hora"])["energia"].mean().reset_index()
    
    # 3. Soma do dia típico
    med_mensal = med_hora.groupby("mes")["energia"].sum().round(2).reset_index()
    return med_mensal

def gerar_comparativo(df: pd.DataFrame) -> pd.DataFrame:
    # Cenário A: Com dados negativos (Bruto)
    df_bruto = df.copy()
    medias_brutas = calcular_irradiacao(df_bruto)
    
    # Cenário B: Sem dados negativos (Limpo - >= 0)
    df_limpo = df[df[COLUNA] >= 0].copy()
    medias_limpas = calcular_irradiacao(df_limpo)
    
    # Mescla os dois resultados
    comparativo = pd.merge(medias_brutas, medias_limpas, on="mes", suffixes=("_bruto", "_limpo"))
    
    # Calcula o impacto da filtragem
    comparativo["perda_wh"] = comparativo["energia_limpo"] - comparativo["energia_bruto"]
    comparativo["impacto_percentual"] = (comparativo["perda_wh"] / comparativo["energia_limpo"]) * 100
    
    return comparativo

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_grafico_comparativo(df_comp: pd.DataFrame) -> go.Figure:
    meses  = sorted(df_comp["mes"].unique())
    labels = [LABELS_MESES.get(m, m) for m in meses]
    
    y_bruto = df_comp["energia_bruto"].tolist()
    y_limpo = df_comp["energia_limpo"].tolist()

    fig = go.Figure()

    # Barras dos dados BRUTOS (Com negativos)
    fig.add_trace(go.Bar(
        x=labels,
        y=y_bruto,
        name="Com Negativos (Dados Brutos)",
        marker_color="#b5b3ae",
        hovertemplate="<b>%{x}</b><br>Bruto: %{y:,.0f} Wh/m²/dia<extra></extra>"
    ))

    # Barras dos dados LIMPOS (Sem negativos)
    fig.add_trace(go.Bar(
        x=labels,
        y=y_limpo,
        name="Sem Negativos (Filtrado)",
        marker_color="#01696f",
        hovertemplate="<b>%{x}</b><br>Limpo: %{y:,.0f} Wh/m²/dia<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text=(
                "Impacto dos Valores Negativos na Irradiação Global"
                "<br><span style='font-size:14px;font-weight:normal;color:gray'>"
                "Comparação da Média Diária (Wh/m²/dia) filtrando ou não leituras noturnas</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(title="Mês", gridcolor="#262523", color="#797876"),
        yaxis=dict(title="Irradiação Média (Wh/m²/dia)", gridcolor="#262523", color="#797876"),
        barmode="group",
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        font=dict(family="sans-serif", color="#cdccca"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2),
        margin=dict(t=100, b=80, l=60, r=20),
    )

    return fig

# ── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Carregando base de dados...\n")
    df = carregar_dados(CSV_PATH, CSV_SEP)
    
    # NOVO: Exibe a quantidade de valores negativos antes dos cálculos
    exibir_contagem_negativos(df)
    
    print("Calculando cenários de irradiação...")
    df_comparativo = gerar_comparativo(df)
    
    print("\n=== RELATÓRIO DE IMPACTO DOS DADOS NEGATIVOS NA ENERGIA ===")
    print(df_comparativo[["mes", "energia_bruto", "energia_limpo", "perda_wh", "impacto_percentual"]].to_string(index=False))
    
    media_impacto = df_comparativo["impacto_percentual"].mean()
    print(f"\nResumo: Os valores negativos reduzem o total de energia calculada em cerca de {media_impacto:.2f}% ao longo do ano.")
    
    # Exibe o gráfico interativo
    fig = criar_grafico_comparativo(df_comparativo)
    fig.show()