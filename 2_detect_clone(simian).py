import os
import pandas as pd
import subprocess
import configparser
from tqdm import tqdm

# === Ler configurações ===
config = configparser.ConfigParser()
config.read("./metadata/dados/settings.ini")

projects = [p.strip() for p in config.get("DETAILS", "projects").split(",")]
path_to_repo = config.get("DETAILS", "path_to_repo", fallback=".")
search_results_dir = os.path.join(path_to_repo, "search_results")
language = config.get("DETAILS", "language")


os.makedirs(search_results_dir, exist_ok=True)

# === Função para rodar o Simian ===
def run_simian(repo_path, project, number_pr, number_commit, mode):
    """
    mode = 'parent' ou 'child'
    """
    output_xml = os.path.join(
        search_results_dir,
        f"simian-result-{project}-{number_pr}-{number_commit}-{mode}.xml"
    )
    simian_jar = os.path.join(path_to_repo, "simian-4.0.0", "simian-4.0.0.jar")
    options = "-formatter=xml -threshold=6"
    simian_command = f'java -jar "{simian_jar}" {options} -includes="{repo_path}/**/*.{language}" > "{output_xml}"'
    os.system(simian_command)
    print(f"✅ Simian salvo em {output_xml}")

# === Loop pelos projetos ===
for project in projects:
    metadata_csv = os.path.join(path_to_repo, "metadata", f"{project}.csv")
    repo_path = os.path.join(path_to_repo, "git_repos", project)

    if not os.path.exists(metadata_csv):
        print(f"⚠️ CSV não encontrado: {metadata_csv}")
        continue
    if not os.path.exists(repo_path):
        print(f"⚠️ Repositório não encontrado: {repo_path}")
        continue

    df = pd.read_csv(metadata_csv)
    if df.empty:
        print(f"⚠️ CSV vazio: {metadata_csv}")
        continue

    print(f"\n📦 Processando projeto: {project} ({len(df)} commits)")

    os.chdir(repo_path)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Commits de {project}"):

        number_pr = row["number_pr"]
        number_commit = row["number_commit"]

        parent_sha = str(row["parent"]).strip()
        child_sha = str(row["child"]).strip()

        # --- Rodar simian no parent ---
        if parent_sha and parent_sha != "None" and len(parent_sha) > 5:
            try:
                subprocess.run(["git", "reset", "--hard", parent_sha],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                run_simian(repo_path, project, number_pr, number_commit, "parent")
            except subprocess.CalledProcessError:
                print(f"⚠️ Falha no checkout do parent {parent_sha} ({project} PR {number_pr})")

        # --- Rodar simian no child ---
        if child_sha and len(child_sha) > 5:
            try:
                subprocess.run(["git", "reset", "--hard", child_sha],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                run_simian(repo_path, project, number_pr, number_commit, "child")
            except subprocess.CalledProcessError:
                print(f"⚠️ Falha no checkout do child {child_sha} ({project} PR {number_pr})")

print("\n✅ Execução concluída com sucesso!")
