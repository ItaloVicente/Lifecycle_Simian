import pandas as pd
import os
import glob

# Diretório onde o script anterior salvou os resultados
# (mesmo valor de OUT_DIR do seu script)
OUT_DIR = "results_clones_classifieds"

# Nome do arquivo de saída para o resumo
SUMMARY_FILE = os.path.join(OUT_DIR, "summary_pr_by_category.csv")

print(f"🔎 Procurando arquivos em: {OUT_DIR}")

# 1. Encontrar e carregar todos os arquivos de classificação
all_csv_files = glob.glob(os.path.join(OUT_DIR, "*_clone_classified.csv"))

if not all_csv_files:
    print(f"⚠️ Nenhum arquivo '*_clone_classified.csv' encontrado em '{OUT_DIR}'.")
    print("Certifique-se de que o primeiro script foi executado com sucesso.")
    exit()

print(f"📚 Encontrados {len(all_csv_files)} arquivos para processar.")

all_data = []
for f in all_csv_files:
    try:
        df = pd.read_csv(f)
        if not df.empty:
            # Precisamos apenas destas colunas para a análise
            required_cols = {'project', 'pr', 'categoria'}
            if required_cols.issubset(df.columns):
                all_data.append(df[list(required_cols)])
            else:
                print(f"⚠️ Arquivo {f} pulado: colunas {required_cols} não encontradas.")
    except pd.errors.EmptyDataError:
        print(f"ℹ️ Arquivo {f} está vazio e será ignorado.")
    except Exception as e:
        print(f"🚨 Erro ao ler {f}: {e}")

if not all_data:
    print("🚨 Nenhum dado válido foi carregado. Saindo.")
    exit()

# Combinar todos os dados em um único DataFrame
print("Concatenando todos os dados...")
combined_df = pd.concat(all_data, ignore_index=True)

print(f"Total de {len(combined_df)} clones lidos.")

# 2. Identificar pares únicos de (PR, Categoria)
# Um PR é identificado por ('project', 'pr')
# drop_duplicates() garante que cada PR seja contado apenas UMA VEZ por categoria,
# mesmo se tiver vários clones daquela categoria.
print("Identificando pares únicos de (PR, Categoria)...")
unique_pr_categories = combined_df[['project', 'pr', 'categoria']].drop_duplicates()

# 3. Contar quantos PRs únicos existem para cada categoria
print("Contando PRs únicos por categoria...")
pr_counts_by_category = unique_pr_categories['categoria'].value_counts()

# 4. Formatar e salvar o resultado
print("Formatando o resultado...")
# Converte a Series (onde o índice é a 'categoria' e o valor é a contagem)
# para um DataFrame com os nomes de coluna solicitados.
summary_df = pr_counts_by_category.reset_index()
summary_df.columns = ['tipo', 'quantidade']

# Ordenar por quantidade para facilitar a leitura (opcional)
summary_df = summary_df.sort_values(by='quantidade', ascending=False)

# 5. Salvar o CSV final
summary_df.to_csv(SUMMARY_FILE, index=False)

print("\n🎉 Resumo da classificação de PRs concluído!")
print(summary_df)
print(f"\n✅ Resultado salvo em: {SUMMARY_FILE}")