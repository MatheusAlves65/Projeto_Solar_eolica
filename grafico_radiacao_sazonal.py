"""
Radiação Global — Médias Sazonais (Wh/m²/dia)
Estação NAT | Rede SONDA | jun/2024 – mai/2025

Gera gráfico de médias sazonais e injeta no index.html do portal.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH   = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP    = ";"
COLUNA     = "glo_avg"
INDEX_HTML = "index.html"
MARCADOR   = "<!-- GRAFICO_RADIACAO_SAZONAL -->"

# Estações do Hemisfério Sul — datas exatas do período
# Cada tupla: (label_exibição, [meses incluídos], cor)
ESTACOES = [
    {
        "label":  "Inverno\n(jun–ago/24)",
        "meses":  ["2024-06", "2024-07", "2024-08"],
        "cor":    "rgb(70, 130, 200)",   # azul frio
    },
    {
        "label":  "Primavera\n(set–nov/24)",
        "meses":  ["2024-09", "2024-10", "2024-11"],
        "cor":    "rgb(100, 180, 100)",  # verde
    },
    {
        "label":  "Verão\n(dez/24–fev/25)",
        "meses":  ["2024-12", "2025-01", "2025-02"],
        "cor":    "rgb(230, 140, 50)",   # laranja quente
    },
    {
        "label":  "Outono\n(mar–mai/25)",
        "meses":  ["2025-03", "2025-04", "2025-05"],
        "cor":    "rgb(180, 100, 60)",   # terra
    },
]

# ── Pipeline de dados ────────────────────────────────────────────────────────

def carregar_dados(path: str, sep: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, low_memory=False)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df[COLUNA] = pd.to_numeric(df[COLUNA], errors="coerce")
    return df


def preparar_medias_sazonais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada estação:
      1. Filtra os meses da estação
      2. Calcula energia diária (Wh/m²/dia) = Σ(glo_avg) / 60
      3. Tira a média de todos os dias da estação
    """
    df = df[df[COLUNA] >= 0].copy()
    df["mes"] = df["timestamp_utc"].dt.to_period("M").astype(str)
    df["dia"] = df["timestamp_utc"].dt.date

    # Energia por dia (todos os meses)
    energia_diaria = (
        df.groupby(["mes", "dia"])[COLUNA]
        .sum()
        .div(60)
        .reset_index()
    )
    energia_diaria.columns = ["mes", "dia", "energia_wh"]

    resultados = []
    for estacao in ESTACOES:
        dias_estacao = energia_diaria[energia_diaria["mes"].isin(estacao["meses"])]
        media  = dias_estacao["energia_wh"].mean().round(2)
        desvio = dias_estacao["energia_wh"].std().round(2)
        resultados.append({
            "label":  estacao["label"],
            "media":  media,
            "desvio": desvio,
            "cor":    estacao["cor"],
            "n_dias": len(dias_estacao),
        })

    return pd.DataFrame(resultados)

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_figura(medias: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    # Barras por estação
    fig.add_trace(go.Bar(
        x=medias["label"],
        y=medias["media"],
        error_y=dict(
            type="data",
            array=medias["desvio"].tolist(),
            visible=True,
            color="rgba(255,255,255,0.4)",
            thickness=2,
            width=6,
        ),
        marker_color=medias["cor"].tolist(),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Média: %{y:.1f} Wh/m²/dia<br>"
            "Desvio padrão: %{error_y.array:.1f} Wh/m²/dia<extra></extra>"
        ),
        name="Energia sazonal",
        width=0.5,
    ))

    # Linha de média geral do período
    media_geral = medias["media"].mean()
    fig.add_hline(
        y=media_geral,
        line_dash="dot",
        line_color="rgba(255,255,255,0.4)",
        line_width=1.5,
        annotation_text=f"Média anual: {media_geral:.0f} Wh/m²/dia",
        annotation_position="top right",
        annotation_font_color="rgba(255,255,255,0.6)",
    )

    fig.update_layout(
        title=dict(
            text=(
                "Energia Solar Média por Estação do Ano"
                "<br><span style='font-size:14px;font-weight:normal;color:gray'>"
                "Estação NAT | jun/2024 – mai/2025 | Hemisfério Sul</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title="Estação",
            gridcolor="#262523",
            color="#797876",
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            title="Energia média diária (Wh/m²/dia)",
            gridcolor="#262523",
            color="#797876",
        ),
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        font=dict(family="sans-serif", color="#cdccca"),
        showlegend=False,
        margin=dict(t=130, b=80, l=70, r=20),
    )

    return fig

# ── Injetar no index.html ────────────────────────────────────────────────────

def injetar_no_portal(fig: go.Figure, html_path: str, marcador: str) -> None:
    grafico_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    with open(html_path, "r", encoding="utf-8") as f:
        portal = f.read()

    if marcador not in portal:
        print(f"[AVISO] Marcador '{marcador}' não encontrado em {html_path}.")
        print("Verifique se o comentário está no index.html e tente novamente.")
        return

    portal = portal.replace(marcador, grafico_html)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(portal)

    print(f"Gráfico injetado com sucesso em: {html_path}")

# ── Execução ─────────────────────────────────────────────────────────────────

def gerar_grafico(path: str = CSV_PATH) -> go.Figure:
    df     = carregar_dados(path, CSV_SEP)
    medias = preparar_medias_sazonais(df)

    print("\nMédias sazonais calculadas:")
    for _, row in medias.iterrows():
        print(f"  {row['label'].replace(chr(10),' '):<30} {row['media']:>8.1f} Wh/m²/dia  (±{row['desvio']:.1f}, n={row['n_dias']} dias)")

    return criar_figura(medias)


if __name__ == "__main__":
    fig = gerar_grafico(path=CSV_PATH)

    fig.show()

    resposta = input("\nGráfico OK? Injetar no index.html? [s/N]: ").strip().lower()
    if resposta == "s":
        injetar_no_portal(fig, html_path=INDEX_HTML, marcador=MARCADOR)
    else:
        print("Injeção cancelada. Nenhum arquivo foi alterado.")
