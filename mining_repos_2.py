import os
import pandas as pd
from tqdm import tqdm
import subprocess
import requests
import configparser

# === Ler settings.ini ===
config = configparser.ConfigParser()
config.read("metadata/dados/settings.ini")
LANGUAGE = config["DETAILS"]["language"]
print(f" Linguagem selecionada: {LANGUAGE}")

# === Ler token do arquivo .ini ===
config = configparser.ConfigParser()
config.read("metadata/dados/token.ini")
GITHUB_TOKEN = config.get("github", "token")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# === Caminhos ===
csv_path = f"metadata/dados/{LANGUAGE.lower()}_pr_commits_without_parents.csv"
output_dir = "git_repos"

# === Criar pasta de saída ===
os.makedirs(output_dir, exist_ok=True)

# === Ler CSV ===
if not os.path.exists(csv_path):
    raise FileNotFoundError(f" Arquivo CSV não encontrado: {csv_path}")

df = pd.read_csv(csv_path)

# === Pegar repositórios únicos ===
repos = df["repo_url"].dropna().unique()
print(f" {len(repos)} repositórios únicos encontrados para {LANGUAGE}.")

def get_clone_url(api_url: str) -> str | None:
    """
    Dado o link da API do repositório (ex: https://api.github.com/repos/domaframework/doma),
    retorna o campo 'clone_url' do JSON.
    """
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("clone_url", None)
        else:
            print(f" Falha ao obter clone_url ({r.status_code}) para {api_url}")
            return None
    except Exception as e:
        print(f" Erro ao buscar clone_url para {api_url}: {e}")
        return None


# === Clonar repositórios ===
for api_url in tqdm(repos, desc=f"Clonando repositórios ({LANGUAGE})"):
    clone_url = get_clone_url(api_url)
    if not clone_url:
        print(f" Não foi possível obter clone_url para {api_url}")
        continue

    repo_name = clone_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(output_dir, repo_name)

    if os.path.exists(repo_path):
        print(f" Repositório '{repo_name}' já existe, pulando.")
        continue

    try:
        subprocess.run(["git", "clone", clone_url, repo_path], check=True)
        print(f" Clonado: {repo_name}")
    except subprocess.CalledProcessError as e:
        print(f" Erro ao clonar {repo_name}: {e}")
    except Exception as e:
        print(f" Erro inesperado com {repo_name}: {e}")

print(f"\n Clonagem concluída para projetos {LANGUAGE}!")