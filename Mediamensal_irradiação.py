import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Configurações ────────────────────────────────────────────────────────────

CSV_PATH   = "base_sonda_com_temperaturas_A304_SBNT_2024-06_a_2025-05.csv"
CSV_SEP    = ";"
COLUNA     = "glo_avg"
INDEX_HTML = "index.html"
MARCADOR   = "Médias horárias mensais — Radiação Global"

LABELS_MESES = {
    "2024-06": "Jun/24", "2024-07": "Jul/24", "2024-08": "Ago/24",
    "2024-09": "Set/24", "2024-10": "Out/24", "2024-11": "Nov/24",
    "2024-12": "Dez/24", "2025-01": "Jan/25", "2025-02": "Fev/25",
    "2025-03": "Mar/25", "2025-04": "Abr/25", "2025-05": "Mai/25",
}

# ── Funções de Apoio ─────────────────────────────────────────────────────────

def gerar_gradiente_azul(n: int) -> list[str]:
    azul_intenso = np.array([0, 56, 176])
    azul_claro   = np.array([173, 216, 255])
    cores = []
    for i in range(n):
        t   = i / max(n - 1, 1)
        rgb = (1 - t) * azul_intenso + t * azul_claro
        cores.append(f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})")
    return cores

def carregar_dados(path: str, sep: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, low_memory=False)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df[COLUNA] = pd.to_numeric(df[COLUNA], errors="coerce")
    return df

# ── Pipeline de Cálculo (Exigência do Professor) ─────────────────────────────

def preparar_dados_irradiacao(df: pd.DataFrame):
    df = df[df[COLUNA] >= 0].copy()
    
    # Extrai mês, dia e hora para os agrupamentos
    df["mes"] = df["timestamp_utc"].dt.to_period("M").astype(str)
    df["dia"] = df["timestamp_utc"].dt.date
    df["hora"] = df["timestamp_utc"].dt.hour

    # PASSO 1: Calcular a Irradiação Horária de cada dia específico (Wh/m²)
    # Soma a irradiância dos 60 minutos de cada hora e divide por 60.
    irradiacao_diaria_por_hora = (
        df.groupby(["mes", "dia", "hora"])[COLUNA]
        .sum()
        .div(60)
        .reset_index()
    )
    irradiacao_diaria_por_hora.rename(columns={COLUNA: "energia_da_hora"}, inplace=True)

    # PASSO 2: Calcular a Média Horária Mensal
    # Tira a média da mesma hora considerando todos os dias do mês
    media_horaria_mensal = (
        irradiacao_diaria_por_hora.groupby(["mes", "hora"])["energia_da_hora"]
        .mean()
        .reset_index()
    )

    # PASSO 3: Calcular a Média Mensal de Irradiação Diária
    # Soma as 24 médias horárias de cada mês
    media_mensal = (
        media_horaria_mensal.groupby("mes")["energia_da_hora"]
        .sum()
        .round(2)
        .reset_index()
    )
    media_mensal.columns = ["mes", "media"]
    
    # Para salvar o passo 2 em CSV se quiser comprovar o cálculo para o professor
    # media_horaria_mensal.to_csv("medias_horarias_mensais.csv", index=False)
    
    return media_mensal

# ── Plotly ───────────────────────────────────────────────────────────────────

def criar_figura(medias: pd.DataFrame) -> go.Figure:
    meses  = sorted(medias["mes"].unique())
    labels = [LABELS_MESES.get(m, m) for m in meses]
    
    # Valores em Wh/m²/dia (se quiser em kWh, divida por 1000 aqui)
    valores = [medias.loc[medias["mes"] == m, "media"].values[0] for m in meses]
    cores  = gerar_gradiente_azul(len(meses))

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=valores,
        marker_color=cores,
        hovertemplate="<b>%{x}</b><br>Irradiação Média: %{y:,.0f} Wh/m²/dia<extra></extra>",
        name="Média mensal",
    ))

    # Linha de tendência para visualização
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
                "Média Mensal — Irradiação Global Horizontal"
                "<br><span style='font-size:14px;font-weight:normal;color:gray'>"
                "Soma das médias horárias mensais (Wh/m²/dia) | Estação NAT</span>"
            ),
            x=0.5, xanchor="center",
        ),
        xaxis=dict(title="Mês", gridcolor="#262523", color="#797876"),
        yaxis=dict(title="Irradiação Diária Média (Wh/m²/dia)", gridcolor="#262523", color="#797876"),
        plot_bgcolor="#1c1b19",
        paper_bgcolor="#171614",
        font=dict(family="sans-serif", color="#cdccca"),
        margin=dict(t=130, b=60, l=60, r=20),
        bargap=0.25,
        showlegend=False
    )

    return fig

# ── Injeção HTML ─────────────────────────────────────────────────────────────

def injetar_no_portal(fig: go.Figure, html_path: str, marcador: str) -> None:
    grafico_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    with open(html_path, "r", encoding="utf-8") as f:
        portal = f.read()
    
    if marcador not in portal:
        print(f"[AVISO] Marcador '{marcador}' não encontrado.")
        return

    portal = portal.replace(marcador, grafico_html)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(portal)
    print(f"Gráfico injetado com sucesso em: {html_path}")

# ── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Processando dados e calculando médias horárias...")
    df = carregar_dados(CSV_PATH, CSV_SEP)
    medias_mensais = preparar_dados_irradiacao(df)
    
    fig = criar_figura(medias_mensais)
    fig.show()

    resposta = input("\nGráfico OK? Injetar no index.html? [s/N]: ").strip().lower()
    if resposta == "s":
        injetar_no_portal(fig, INDEX_HTML, MARCADOR)
    else:
        print("Injeção cancelada.")