import os
import pandas as pd
import xml.etree.ElementTree as ET
import configparser
from tqdm import tqdm

# === Read configuration ===
config = configparser.ConfigParser()
config.read("./metadata/dados/settings.ini")

projects = [p.strip() for p in config.get("DETAILS", "projects").split(",")]
path_to_repo = config.get("DETAILS", "path_to_repo", fallback=".")
search_results_dir = os.path.join(path_to_repo, "search_results")
metadata_dir = os.path.join(path_to_repo, "metadata")

os.makedirs(search_results_dir, exist_ok=True)

def extract_fingerprints(xml_path):
    if not os.path.exists(xml_path):
        return set()

    try:
        # Read the entire file as text
        with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Find where the XML starts (first "<")
        idx = content.find("<")
        if idx > 0:
            content = content[idx:]  # remove header

        # Now parse as real XML
        root = ET.fromstring(content)

        fingerprints = set()

        # Find <set> nodes with fingerprint
        for s in root.findall(".//set"):
            fp = s.attrib.get("fingerprint")
            if not fp:
                continue

            blocks = s.findall("block")
            files = [b.attrib.get("sourceFile", "").lower() for b in blocks]

            # Ignore if ALL blocks are tests
            if all(("test" in f or "tests" in f or "spec" in f) for f in files):
                continue

            fingerprints.add(fp)

        return fingerprints

    except Exception as e:
        print(f"⚠️ Error reading XML {xml_path}: {e}")
        return set()

# === Loop per project ===
for project in projects:
    csv_path = os.path.join(metadata_dir, f"{project}.csv")
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV not found: {csv_path}")
        continue

    df = pd.read_csv(csv_path)

    if df.empty:
        print(f"⚠️ Empty CSV: {csv_path}")
        continue

    print(f"\n📌 Processing project: {project}")

    results = []

    # Group by PR
    for pr_id, pr_group in tqdm(df.groupby("number_pr"), desc=f"PRs - {project}"):
        pr_group = pr_group.sort_values("number_commit")
        total_commits = pr_group.shape[0]

        active_clones = {}  # fingerprint -> start_commit

        for _, row in pr_group.iterrows():
            number_commit = row["number_commit"]

            xml_parent = os.path.join(
                search_results_dir,
                f"simian-result-{project}-{pr_id}-{number_commit}-parent.xml"
            )
            xml_child = os.path.join(
                search_results_dir,
                f"simian-result-{project}-{pr_id}-{number_commit}-child.xml"
            )

            parent_clones = extract_fingerprints(xml_parent)
            child_clones = extract_fingerprints(xml_child)

            # New clones introduced in this commit
            new_clones = child_clones - parent_clones
            # Clones that disappeared
            disappeared = set(active_clones.keys()) - child_clones

            # Record disappeared clones
            for fp in disappeared:
                results.append({
                    "project": project,
                    "pr": pr_id,
                    "clone_fingerprint": fp,
                    "start_commit": active_clones[fp],
                    "end_commit": number_commit - 1,
                    "total_commits_in_pr": total_commits
                })
                del active_clones[fp]

            # Record new active clones
            for fp in new_clones:
                active_clones[fp] = number_commit

        # Finalize clones that lasted until the last commit
        for fp, start_commit in active_clones.items():
            results.append({
                "project": project,
                "pr": pr_id,
                "clone_fingerprint": fp,
                "start_commit": start_commit,
                "end_commit": pr_group["number_commit"].max(),
                "total_commits_in_pr": total_commits
            })

    # === Save project result ===
    output_csv = os.path.join(metadata_dir, f"{project}_clone_lifetimes.csv")
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"✅ CSV saved: {output_csv}")
