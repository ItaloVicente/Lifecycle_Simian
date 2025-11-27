import pandas as pd
import os
import glob

# Directory where the previous script saved the results
# (same value as OUT_DIR from your script)
OUT_DIR = "results_clones_classifieds"

# Output file name for the summary
SUMMARY_FILE = os.path.join(OUT_DIR, "summary_pr_by_category.csv")

print(f"🔎 Looking for files in: {OUT_DIR}")

# 1. Find and load all classification files
all_csv_files = glob.glob(os.path.join(OUT_DIR, "*_clone_classified.csv"))

if not all_csv_files:
    print(f"⚠️ No '*_clone_classified.csv' files found in '{OUT_DIR}'.")
    print("Make sure the first script ran successfully.")
    exit()

print(f"📚 Found {len(all_csv_files)} files to process.")

all_data = []
for f in all_csv_files:
    try:
        df = pd.read_csv(f)
        if not df.empty:
            # We only need these columns for the analysis
            required_cols = {"project", "pr", "categoria"}
            if required_cols.issubset(df.columns):
                all_data.append(df[list(required_cols)])
            else:
                print(f"⚠️ File {f} skipped: columns {required_cols} not found.")
    except pd.errors.EmptyDataError:
        print(f"ℹ️ File {f} is empty and will be ignored.")
    except Exception as e:
        print(f"🚨 Error reading {f}: {e}")

if not all_data:
    print("🚨 No valid data was loaded. Exiting.")
    exit()

# Combine all data into a single DataFrame
print("Concatenating all data...")
combined_df = pd.concat(all_data, ignore_index=True)

print(f"Total of {len(combined_df)} clones read.")

# 2. Identify unique (PR, Category) pairs
# A PR is identified by ('project', 'pr')
# drop_duplicates() ensures each PR is counted only ONCE per category,
# even if it has multiple clones in that category.
print("Identifying unique (PR, Category) pairs...")
unique_pr_categories = combined_df[["project", "pr", "categoria"]].drop_duplicates()

# 3. Count how many unique PRs exist for each category
print("Counting unique PRs by category...")
pr_counts_by_category = unique_pr_categories["categoria"].value_counts()

# 4. Format and save the result
print("Formatting the result...")
# Convert the Series (where the index is 'categoria' and the value is the count)
# into a DataFrame with the requested column names.
summary_df = pr_counts_by_category.reset_index()
summary_df.columns = ["tipo", "quantidade"]

# Sort by count for easier reading (optional)
summary_df = summary_df.sort_values(by="quantidade", ascending=False)

# 5. Save the final CSV
summary_df.to_csv(SUMMARY_FILE, index=False)

print("\n🎉 PR classification summary completed!")
print(summary_df)
print(f"\n✅ Result saved to: {SUMMARY_FILE}")
