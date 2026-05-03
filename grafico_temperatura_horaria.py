"""
Temperatura — Média Horária Mensal
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
MARCADOR   = "<!-- GRAFICO_TEMP_HORARIA -->"

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


def preparar_medias(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df[COLUNA] >= 0].copy()
    df["hora"] = df["timestamp_utc"].dt.hour
    df["mes"]  = df["timestamp_utc"].dt.to_period("M").astype(str)
    medias = (
        df.groupby(["mes", "hora"])[COLUNA]
        .mean()
        .round(2)
        .reset_index()
    )
    medias.columns = ["mes", "hora", "media"]
    return medias

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_traces(medias: pd.DataFrame, meses: list[str]) -> list[go.Scatter]:
    cores = gerar_gradiente(len(meses))
    traces = []
    for i, mes in enumerate(meses):
        dados = medias[medias["mes"] == mes].sort_values("hora")
        label = LABELS_MESES.get(mes, mes)
        traces.append(go.Scatter(
            x=dados["hora"],
            y=dados["media"],
            mode="lines",
            name=label,
            line=dict(color=cores[i], width=2.5),
            hovertemplate=(
                f"{label}<br>Hora: %{{x}}:00 UTC<br>"
                f"Temp: %{{y:.1f}} °C<extra></extra>"
            ),
        ))
    return traces


def criar_botoes(meses: list[str]) -> list[dict]:
    n = len(meses)

    def vis(idx_ativos):
        return [j in idx_ativos for j in range(n)]

    botoes = [
        dict(label="Todos",  method="update", args=[{"visible": [True]  * n}]),
        dict(label="Nenhum", method="update", args=[{"visible": [False] * n}]),
    ]
    for i, mes in enumerate(meses):
        botoes.append(dict(
            label=LABELS_MESES.get(mes, mes),
            method="update",
            args=[{"visible": vis([i])}],
        ))
    return botoes


def montar_layout(botoes: list[dict]) -> go.Layout:
    return go.Layout(
        title=dict(
            text=(
                "Média Horária de Temperatura por Mês"
                "<br><span style=\'font-size:14px;font-weight:normal;color:gray\'>"
                "Estação NAT | jun/2024 – mai/2025 | temp_avg ≥ 0 °C</span>"
            ),
            x=0.5, xanchor="center",
        ),
        updatemenus=[dict(
            type="buttons", direction="right", showactive=True,
            x=0.5, xanchor="center", y=1.18, yanchor="top",
            buttons=botoes,
            bgcolor="#1c1b19", bordercolor="#393836",
            font=dict(color="#cdccca", size=12),
            pad=dict(l=4, r=4, t=4, b=4),
        )],
        xaxis=dict(
            title="Hora (UTC)",
            range=[0, 23], dtick=1, tickmode="linear",
            tickvals=list(range(24)),
            ticktext=[f"{h:02d}:00" for h in range(24)],
            gridcolor="#262523", color="#797876",
        ),
        yaxis=dict(
            title="Temperatura (°C)",
            gridcolor="#262523", color="#797876",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5,
            font=dict(size=12),
        ),
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        font=dict(family="sans-serif", color="#cdccca"),
        hovermode="x unified",
        margin=dict(t=160, b=100, l=60, r=20),
    )


def gerar_grafico(path: str = CSV_PATH) -> go.Figure:
    df     = carregar_dados(path, CSV_SEP)
    medias = preparar_medias(df)
    meses  = sorted(medias["mes"].unique())

    fig = go.Figure(
        data=criar_traces(medias, meses),
        layout=montar_layout(criar_botoes(meses)),
    )

    print(f"Meses carregados : {len(meses)}")
    print(f"Registros válidos: {len(df[df[COLUNA] >= 0]):,}")
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

# ── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fig = gerar_grafico(path=CSV_PATH)

    fig.show()

    resposta = input("\nGráfico OK? Injetar no index.html? [s/N]: ").strip().lower()
    if resposta == "s":
        injetar_no_portal(fig, html_path=INDEX_HTML, marcador=MARCADOR)
    else:
        print("Injeção cancelada. Nenhum arquivo foi alterado.")
