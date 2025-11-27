import os
import pandas as pd
import configparser
from tqdm import tqdm

# === Ler configurações ===
config = configparser.ConfigParser()
config.read("./metadata/dados/settings.ini")

projects = [p.strip() for p in config.get("DETAILS", "projects").split(",")]
metadata_dir = config.get("DETAILS", "path_to_repo", fallback=".") + "/metadata"

OUT_DIR = "results_clones_classifieds"
os.makedirs(OUT_DIR, exist_ok=True)

def classify_clone(start, end, total):
    # start, end, total são inteiros aqui

    # 1. Primeiro, verificar o caso de "span completo"
    #    Isso captura (1, 1, 1) E (1, 5, 5) corretamente.
    if start == 1 and end == total:
        return "ini_mei_final"

    # 2. Se não for span completo, verificar os casos "únicos" (start == end)
    elif start == end:
        if start == 1:
            # Já sabemos que end != total, senão teria caído no 'if' acima
            return "unique_ini"
        elif start == total:
            # Já sabemos que start != 1
            return "unique_final"
        else:
            # Nem start=1 nem end=total
            return "unique_mei"

    # 3. Se não for "span completo" nem "único", é um "span parcial"
    else: # start != end
        if start == 1 and end < total:
            return "ini_mei"
        elif 1 < start and end < total:
            return "mei"
        elif start > 1 and end == total:
            return "mei_final"
        else:
            # Caso de segurança, não deve ser atingido
            return "unknown"

for project in projects:
    input_csv = os.path.join(metadata_dir, f"{project}_clone_lifetimes.csv")
    if not os.path.exists(input_csv):
        print(f"⚠️ Arquivo não encontrado: {input_csv}")
        continue

    try:
        df = pd.read_csv(input_csv)
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver 100% vazio (0 bytes), o pandas dá este erro
        print(f"⚠️ CSV vazio (EmptyDataError): {input_csv}")
        continue  # <-- ESTA É A CORREÇÃO CRÍTICA
    except Exception as e:
        # Captura outros erros de leitura
        print(f"🚨 Erro ao ler o CSV {input_csv}: {e}")
        continue  # <-- Também pular em outros erros

    if df.empty:
        # Se o arquivo tem cabeçalhos mas não tem linhas de dados
        print(f"⚠️ CSV vazio (sem linhas de dados): {input_csv}")
        continue

    # Verifica colunas mínimas
    required_cols = {"pr", "clone_fingerprint", "start_commit", "end_commit", "total_commits_in_pr"}
    if not required_cols.issubset(set(df.columns)):
        print(f"⚠️ Colunas faltando em {input_csv}. Esperado: {required_cols}. Encontrado: {set(df.columns)}")
        continue

    print(f"\n📌 Classificando CLONES do projeto: {project}")

    # Normalizar/forçar tipos e remover linhas inválidas
    # Coerce -> transforma valores não-numéricos em NaN
    df["start_commit"] = pd.to_numeric(df["start_commit"], errors="coerce")
    df["end_commit"] = pd.to_numeric(df["end_commit"], errors="coerce")
    df["total_commits_in_pr"] = pd.to_numeric(df["total_commits_in_pr"], errors="coerce")

    # Remover linhas com NaN ou total_commits_in_pr <= 0
    invalid_mask = df["start_commit"].isna() | df["end_commit"].isna() | df["total_commits_in_pr"].isna() | (df["total_commits_in_pr"] <= 0)
    if invalid_mask.any():
        n_invalid = invalid_mask.sum()
        print(f"⚠️ {n_invalid} linhas inválidas/removidas em {input_csv} (NaN ou total <= 0).")
        df = df[~invalid_mask]

    if df.empty:
        print(f"⚠️ Depois da limpeza, CSV vazio: {input_csv}")
        continue

    # Forçar inteiros (os commits são índices inteiros)
    df["start_commit"] = df["start_commit"].astype(int)
    df["end_commit"] = df["end_commit"].astype(int)
    df["total_commits_in_pr"] = df["total_commits_in_pr"].astype(int)

    clone_rows = []

    # itertuples é mais rápido e seguro quanto a índices
    for row in tqdm(df.itertuples(index=False), total=len(df), desc=f"Clones {project}"):
        # Assumindo ordem dos campos conforme CSV:
        # row.pr, row.clone_fingerprint, row.start_commit, row.end_commit, row.total_commits_in_pr
        # Como usamos index=False, os nomes virão de acordo com as colunas do CSV (pandas converte pontos por _)
        pr = getattr(row, "pr")
        fp = getattr(row, "clone_fingerprint")
        start = int(getattr(row, "start_commit"))
        end = int(getattr(row, "end_commit"))
        total = int(getattr(row, "total_commits_in_pr"))

        # Classificação
        categoria = classify_clone(start, end, total)

        # distância
        if total <= 1:
            distancia = 0.0
        else:
            distancia = 0.0 if start == 1 else (start / total)

        # duração (proteção contra div por zero já feita)
        duracao = (end - start + 1) / total if total > 0 else 0.0

        clone_rows.append({
            "project": project,
            "pr": pr,
            "clone_fingerprint": fp,
            "start_commit": start,
            "end_commit": end,
            "total_commits": total,
            "categoria": categoria,
            "distancia": round(distancia, 4),
            "duracao": round(duracao, 4)
        })

    out_csv = os.path.join(OUT_DIR, f"{project}_clone_classified.csv")
    pd.DataFrame(clone_rows).to_csv(out_csv, index=False)
    print(f"✅ Resultado salvo em: {out_csv}")
