"""
Radiação Global — Médias Mensais
Estação NAT | Rede SONDA | jun/2024 – mai/2025

Gera o gráfico de médias mensais e injeta no index.html do portal.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH   = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP    = ";"
COLUNA     = "glo_avg"
INDEX_HTML = "index.html"
MARCADOR   = "Médias mensais — Radiação Global"

LABELS_MESES = {
    "2024-06": "Jun/24", "2024-07": "Jul/24", "2024-08": "Ago/24",
    "2024-09": "Set/24", "2024-10": "Out/24", "2024-11": "Nov/24",
    "2024-12": "Dez/24", "2025-01": "Jan/25", "2025-02": "Fev/25",
    "2025-03": "Mar/25", "2025-04": "Abr/25", "2025-05": "Mai/25",
}

# ── Gradiente azul ───────────────────────────────────────────────────────────

def gerar_gradiente_azul(n: int) -> list[str]:
    azul_intenso = np.array([0, 56, 176])
    azul_claro   = np.array([173, 216, 255])
    cores = []
    for i in range(n):
        t   = i / max(n - 1, 1)
        rgb = (1 - t) * azul_intenso + t * azul_claro
        cores.append(f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})")
    return cores

# ── Pipeline de dados ────────────────────────────────────────────────────────

def carregar_dados(path: str, sep: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, low_memory=False)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df[COLUNA] = pd.to_numeric(df[COLUNA], errors="coerce")
    return df


def preparar_medias_mensais(df: pd.DataFrame) -> pd.DataFrame:
    """Média diária de cada mês: soma a energia do dia (Wh/m²) e tira a média mensal."""
    df = df[df[COLUNA] >= 0].copy()
    df["mes"] = df["timestamp_utc"].dt.to_period("M").astype(str)
    df["dia"] = df["timestamp_utc"].dt.date

    # Média horária por dia (minutos → horas)
    media_horaria = (
        df.groupby(["mes", "dia"])[COLUNA]
        .mean()
        .reset_index()
    )

    # Média mensal das médias diárias
    medias_mensais = (
        media_horaria.groupby("mes")[COLUNA]
        .mean()
        .round(2)
        .reset_index()
    )
    medias_mensais.columns = ["mes", "media"]
    return medias_mensais

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_figura(medias: pd.DataFrame) -> go.Figure:
    meses  = sorted(medias["mes"].unique())
    labels = [LABELS_MESES.get(m, m) for m in meses]
    valores = [medias.loc[medias["mes"] == m, "media"].values[0] for m in meses]
    cores  = gerar_gradiente_azul(len(meses))

    fig = go.Figure()

    # Barras coloridas por mês
    fig.add_trace(go.Bar(
        x=labels,
        y=valores,
        marker_color=cores,
        hovertemplate="<b>%{x}</b><br>Média: %{y:.1f} W/m²<extra></extra>",
        name="Média mensal",
    ))

    # Linha de tendência por cima
    fig.add_trace(go.Scatter(
        x=labels,
        y=valores,
        mode="lines+markers",
        line=dict(color="rgba(255,255,255,0.5)", width=1.5, dash="dot"),
        marker=dict(size=6, color="white"),
        hoverinfo="skip",
        name="Tendência",
        showlegend=False,
    ))

    fig.update_layout(
        title=dict(
            text=(
                "Médias Mensais de Radiação Global Horizontal"
                "<br><span style='font-size:14px;font-weight:normal;color:gray'>"
                "Estação NAT | jun/2024 – mai/2025 | glo_avg ≥ 0 W/m²</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title="Mês",
            gridcolor="#262523",
            color="#797876",
        ),
        yaxis=dict(
            title="glo_avg médio (W/m²)",
            gridcolor="#262523",
            color="#797876",
        ),
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        font=dict(family="sans-serif", color="#cdccca"),
        bargap=0.25,
        showlegend=False,
        margin=dict(t=130, b=60, l=60, r=20),
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
    df      = carregar_dados(path, CSV_SEP)
    medias  = preparar_medias_mensais(df)
    fig     = criar_figura(medias)

    print(f"Meses calculados : {len(medias)}")
    print(f"Registros válidos: {len(df[df[COLUNA] >= 0]):,}")
    return fig


if __name__ == "__main__":
    fig = gerar_grafico(path=CSV_PATH)
    injetar_no_portal(fig, html_path=INDEX_HTML, marcador=MARCADOR)
