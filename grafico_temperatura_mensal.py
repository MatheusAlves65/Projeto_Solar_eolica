"""
Temperatura — Médias Mensais (°C)
Estação NAT | Rede SONDA | jun/2024 – mai/2025

Gera o gráfico e injeta no index.html do portal.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH   = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP    = ";"
COLUNA     = "temp_resultante_repetida_c"
INDEX_HTML = "index.html"
MARCADOR   = "<!-- GRAFICO_TEMP_MENSAL -->"

LABELS_MESES = {
    "2024-06": "Jun/24", "2024-07": "Jul/24", "2024-08": "Ago/24",
    "2024-09": "Set/24", "2024-10": "Out/24", "2024-11": "Nov/24",
    "2024-12": "Dez/24", "2025-01": "Jan/25", "2025-02": "Fev/25",
    "2025-03": "Mar/25", "2025-04": "Abr/25", "2025-05": "Mai/25",
}

# ── Gradiente laranja-vermelho ───────────────────────────────────────────────

def gerar_gradiente(n: int) -> list[str]:
    cor_a = np.array([180, 40,  20])
    cor_b = np.array([255, 200, 100])
    cores = []
    for i in range(n):
        t = i / max(n - 1, 1)
        rgb = (1 - t) * cor_a + t * cor_b
        cores.append(f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})")
    return cores

# ── Pipeline de dados ────────────────────────────────────────────────────────

def carregar_dados(path: str, sep: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, low_memory=False)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df[COLUNA] = pd.to_numeric(df[COLUNA], errors="coerce")
    return df


def preparar_medias_mensais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Igual ao mensal de radiação:
    1. Média diária de temp_avg (°C) por dia
    2. Média mensal dessas médias diárias
    """
    df = df[df[COLUNA] >= 0].copy()
    df["mes"] = df["timestamp_utc"].dt.to_period("M").astype(str)
    df["dia"] = df["timestamp_utc"].dt.date

    media_diaria = (
        df.groupby(["mes", "dia"])[COLUNA]
        .mean()
        .reset_index()
    )
    media_diaria.columns = ["mes", "dia", "media_dia"]

    medias_mensais = (
        media_diaria.groupby("mes")["media_dia"]
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
    cores  = gerar_gradiente(len(meses))
    vals   = [medias.loc[medias["mes"] == m, "media"].values[0] for m in meses]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=vals,
        marker_color=cores,
        name="Média mensal",
        hovertemplate="<b>%{x}</b><br>Temp: %{y:.1f} °C<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=labels,
        y=vals,
        mode="lines+markers",
        line=dict(color="rgba(255,255,255,0.5)", dash="dot", width=1.5),
        marker=dict(color="white", size=6),
        name="Tendência",
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(
            text=(
                "Médias Mensais de Temperatura"
                "<br><span style=\'font-size:14px;font-weight:normal;color:gray\'>"
                "Estação NAT | jun/2024 – mai/2025 | temp_avg ≥ 0 °C</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(title="Mês", gridcolor="#262523", color="#797876"),
        yaxis=dict(title="Temperatura (°C)", gridcolor="#262523", color="#797876"),
        font=dict(family="sans-serif", color="#cdccca"),
        margin=dict(t=130, b=60, l=60, r=20),
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        bargap=0.25,
        showlegend=False,
    )

    return fig

# ── Injetar no index.html ────────────────────────────────────────────────────

def injetar_no_portal(fig: go.Figure, html_path: str, marcador: str) -> None:
    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False)

    with open(html_path, "r", encoding="utf-8") as f:
        portal = f.read()

    if marcador not in portal:
        print(f"[AVISO] Marcador \'{marcador}\' não encontrado em {html_path}.")
        return

    portal = portal.replace(marcador, grafico_html)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(portal)

    print(f"Gráfico injetado com sucesso em: {html_path}")


def gerar_grafico(path: str = CSV_PATH) -> go.Figure:
    df     = carregar_dados(path, CSV_SEP)
    medias = preparar_medias_mensais(df)

    print("\nMédias mensais de temperatura:")
    for _, row in medias.iterrows():
        label = LABELS_MESES.get(row["mes"], row["mes"])
        print(f"  {label:<10} {row['media']:>6.2f} °C")

    return criar_figura(medias)

# ── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fig = gerar_grafico(path=CSV_PATH)

    fig.show()

    resposta = input("\nGráfico OK? Injetar no index.html? [s/N]: ").strip().lower()
    if resposta == "s":
        injetar_no_portal(fig, html_path=INDEX_HTML, marcador=MARCADOR)
    else:
        print("Injeção cancelada. Nenhum arquivo foi alterado.")
