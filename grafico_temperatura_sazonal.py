"""
Temperatura — Médias Sazonais (°C)
Estação NAT | Rede SONDA | jun/2024 – mai/2025

Gera o gráfico e injeta no index.html do portal.
"""

import pandas as pd
import plotly.graph_objects as go

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH   = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP    = ";"
COLUNA     = "temp_resultante_repetida_c"
INDEX_HTML = "index.html"
MARCADOR   = "!-- Gráfico 6: Sazonal Temperatura --"

ESTACOES = [
    {
        "label": "Inverno\n(jun–ago/24)",
        "meses": ["2024-06", "2024-07", "2024-08"],
        "cor":   "rgb(70, 130, 200)",
    },
    {
        "label": "Primavera\n(set–nov/24)",
        "meses": ["2024-09", "2024-10", "2024-11"],
        "cor":   "rgb(100, 180, 100)",
    },
    {
        "label": "Verão\n(dez/24–fev/25)",
        "meses": ["2024-12", "2025-01", "2025-02"],
        "cor":   "rgb(230, 140, 50)",
    },
    {
        "label": "Outono\n(mar–mai/25)",
        "meses": ["2025-03", "2025-04", "2025-05"],
        "cor":   "rgb(180, 100, 60)",
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
    Igual ao mensal: média diária de temp_avg (°C) → média dos dias da estação.
    Ignora valores negativos.
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

    resultados = []
    for estacao in ESTACOES:
        dias = media_diaria[media_diaria["mes"].isin(estacao["meses"])]
        media = dias["media_dia"].mean().round(2)
        resultados.append({
            "label":  estacao["label"],
            "media":  media,
            "cor":    estacao["cor"],
            "n_dias": len(dias),
        })

    return pd.DataFrame(resultados)

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_figura(medias: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=medias["label"],
        y=medias["media"],
        marker_color=medias["cor"].tolist(),
        hovertemplate="<b>%{x}</b><br>Temp: %{y:.1f} °C<extra></extra>",
        name="Temperatura sazonal",
        width=0.5,
    ))

    media_geral = medias["media"].mean()
    fig.add_hline(
        y=media_geral,
        line_dash="dot",
        line_color="rgba(255,255,255,0.4)",
        line_width=1.5,
        annotation_text=f"Média anual: {media_geral:.1f} °C",
        annotation_position="top right",
        annotation_font_color="rgba(255,255,255,0.6)",
    )

    fig.update_layout(
        title=dict(
            text=(
                "Temperatura Média por Estação do Ano"
                "<br><span style=\'font-size:14px;font-weight:normal;color:gray\'>"
                "Estação NAT | jun/2024 – mai/2025 | Hemisfério Sul</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title="Estação",
            gridcolor="#262523", color="#797876",
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            title="Temperatura (°C)",
            gridcolor="#262523", color="#797876",
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
    medias = preparar_medias_sazonais(df)

    print("\nMédias sazonais de temperatura:")
    for _, row in medias.iterrows():
        print(f"  {row['label'].replace(chr(10),' '):<30} {row['media']:>6.2f} °C  (n={row['n_dias']} dias)")

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
