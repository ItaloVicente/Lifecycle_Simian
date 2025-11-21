import os
import pandas as pd
import subprocess
import configparser

# === Ler configurações ===
config = configparser.ConfigParser()
config.read("metadata/dados/settings.ini")
LANGUAGE = config["DETAILS"]["language"]
print(f" Linguagem configurada: {LANGUAGE}")

# === Caminhos ===
base_dir = os.getcwd()
repos_base_dir = "git_repos"
input_csv = f"metadata/dados/{LANGUAGE.lower()}_pr_commits_without_parents.csv"
output_csv = f"metadata/dados/{LANGUAGE.lower()}_pr_commits_with_parents.csv"

# === Verifica se o CSV de entrada existe ===
if not os.path.exists(input_csv):
    raise FileNotFoundError(f" Arquivo CSV não encontrado: {input_csv}")

# === Ler CSV ===
df = pd.read_csv(input_csv)
repos_grouped = df.groupby("repo_url")

total_commits = len(df)
commit_counter = 0

# Inicializa a coluna parent (se ainda não existir)
if "parent" not in df.columns:
    df["parent"] = None

print(f" Processando {len(repos_grouped)} repositórios e {total_commits} commits para {LANGUAGE}...\n")

# === Loop pelos repositórios ===
for repo_url, group in repos_grouped:
    repo_name = repo_url.split("/")[-1].strip()
    repo_path = os.path.join(repos_base_dir, repo_name)

    if not os.path.exists(repo_path):
        print(f"[ AVISO] Repositório não encontrado localmente: {repo_path}, pulando.")
        continue

    os.chdir(repo_path)
    print(f"\n Repositório: {repo_name} ({len(group)} commits)")

    for idx, row in group.iterrows():
        commit_sha = row["sha_commit"]

        try:
            #  Buscar commit remoto (caso ainda não esteja local)
            subprocess.run(
                ["git", "fetch", "--all", "--quiet"],
                check=False
            )
            subprocess.run(
                ["git", "fetch", "origin", commit_sha],
                check=False
            )

            #  Obter parent real do commit
            result = subprocess.run(
                ["git", "rev-list", "--parents", "-n", "1", commit_sha],
                check=True,
                capture_output=True,
                text=True
            )
            output = result.stdout.strip().split()
            parent_sha = output[1] if len(output) > 1 else None

            df.loc[row.name, "parent"] = parent_sha

        except subprocess.CalledProcessError:
            print(f" Erro ao processar commit {commit_sha} em {repo_name}")
        except Exception as e:
            print(f" Erro inesperado: {e}")

        commit_counter += 1
        print(f"[{commit_counter}/{total_commits}] commits processados", end="\r")

    os.chdir(base_dir)

# === Salvar CSV atualizado ===
df.to_csv(output_csv, index=False)
print(f"\n CSV atualizado salvo em: {output_csv}")
