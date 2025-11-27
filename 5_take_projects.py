import os
from paths import metadata_path

projects = []
for file in os.listdir(metadata_path):
    if file.endswith(".csv") or file.endswith(".xlsx"):
        project_name = os.path.splitext(file)[0]
        projects.append(project_name)

projects = sorted(set(projects))

print("\nFound projects:")
for p in projects:
    print(p)

print("\nLine to paste into settings.ini:")
print("projects = " + ", ".join(projects))
print(len(projects))
