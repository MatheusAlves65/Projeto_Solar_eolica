"""
Radiação Global — Média Horária Mensal
Estação NAT | Rede SONDA | jun/2024 – mai/2025
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

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

# Azul intenso → azul claro (12 passos)
def gerar_gradiente_azul(n: int) -> list[str]:
    """Retorna n cores em gradiente do azul intenso ao azul claro."""
    azul_intenso = np.array([0, 56, 176])    # RGB azul escuro
    azul_claro   = np.array([173, 216, 255]) # RGB azul claro
    cores = []
    for i in range(n):
        t = i / max(n - 1, 1)
        rgb = (1 - t) * azul_intenso + t * azul_claro
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        cores.append(f"rgb({r},{g},{b})")
    return cores

# ── Funções ──────────────────────────────────────────────────────────────────

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


def criar_traces(medias: pd.DataFrame, meses: list[str]) -> list[go.Scatter]:
    cores = gerar_gradiente_azul(len(meses))
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
                f"{COLUNA}: %{{y:.0f}} W/m²<extra></extra>"
            ),
        ))
    return traces


def criar_botoes(meses: list[str]) -> list[dict]:
    n = len(meses)

    def visibilidade(indices_ativos: list[int]) -> list[bool]:
        return [j in indices_ativos for j in range(n)]

    botoes = [
        dict(label="Todos",  method="update", args=[{"visible": [True]  * n}]),
        dict(label="Nenhum", method="update", args=[{"visible": [False] * n}]),
    ]
    for i, mes in enumerate(meses):
        botoes.append(dict(
            label=LABELS_MESES.get(mes, mes),
            method="update",
            args=[{"visible": visibilidade([i])}],
        ))
    return botoes


def montar_layout(botoes: list[dict]) -> go.Layout:
    return go.Layout(
        title=dict(
            text=(
                "Média Horária de Radiação Global por Mês"
                "<br><span style='font-size:14px;font-weight:normal;color:gray'>"
                "Estação NAT | jun/2024 – mai/2025 | glo_avg ≥ 0 W/m²</span>"
            ),
            x=0.5,
            xanchor="center",
        ),
        updatemenus=[dict(
            type="buttons",
            direction="right",
            showactive=True,
            x=0.5, xanchor="center",
            y=1.18, yanchor="top",
            buttons=botoes,
            bgcolor="#1c1b19",
            bordercolor="#393836",
            font=dict(color="#cdccca", size=12),
            pad=dict(l=4, r=4, t=4, b=4),
        )],
        xaxis=dict(
            title="Hora (UTC)",
            range=[0, 23],          # eixo x fixo de 0 a 23
            dtick=1,
            tickmode="linear",
            tickvals=list(range(24)),
            ticktext=[f"{h:02d}:00" for h in range(24)],
            gridcolor="#262523",
            color="#797876",
        ),
        yaxis=dict(
            title="glo_avg (W/m²)",
            gridcolor="#262523",
            color="#797876",
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


def gerar_grafico(path: str = CSV_PATH, salvar_html: str | None = None) -> go.Figure:
    df     = carregar_dados(path, CSV_SEP)
    medias = preparar_medias(df)
    meses  = sorted(medias["mes"].unique())

    traces = criar_traces(medias, meses)
    botoes = criar_botoes(meses)
    layout = montar_layout(botoes)

    fig = go.Figure(data=traces, layout=layout)

    if salvar_html:
        fig.write_html(salvar_html)
        print(f"Salvo em: {salvar_html}")

    print(f"Meses carregados : {len(meses)}")
    print(f"Registros válidos: {len(df[df[COLUNA] >= 0]):,}")

    return fig


# ── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fig = gerar_grafico(
        path=CSV_PATH,
        salvar_html=None,   # ex: "radiacao_global_mensal.html"
    )
    fig.show()
