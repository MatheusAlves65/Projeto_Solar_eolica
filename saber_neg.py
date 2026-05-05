import pandas as pd

# Carregue seu arquivo de dados (ajuste o nome do arquivo)
df = pd.read_csv('base_temperatura_unificada_A304_SBNT_2024-06_a_2025-05.csv', parse_dates=['data'])
print(df.head())

# Agrupa por mês e conta entradas negativas na coluna 'glo_avg'
df['mes'] = df['data'].dt.to_period('M')
negativos_por_mes = df[df['glo_avg'] < 0].groupby('mes').size()

print("Quantidade de valores negativos por mês:")
print(negativos_por_mes)