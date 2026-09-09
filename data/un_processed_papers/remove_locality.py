from pathlib import Path
import pandas as pd

# Root folder containing all the subfolders
root = Path(r"C:/Users/Pedro Trindade/Documents/github/table_extraction_llm/data/un_processed_papers")  # <-- Change this

# Loop through every subfolder
for folder in root.iterdir():
    if folder.is_dir():
        # Find the Excel file
        xlsx_files = list(folder.glob("*.xlsx"))

        if not xlsx_files:
            print(f"No Excel file found in {folder.name}")
            continue

        file = xlsx_files[0]

        try:
            # Read Excel
            df = pd.read_excel(file)

            # Find the MeasurementType column (case-insensitive)
            cols = {c.lower(): c for c in df.columns}

            if "measurementtype" not in cols:
                print(f"'MeasurementType' column not found in {file.name}")
                continue

            col = cols["measurementtype"]

            original_rows = len(df)

            # Remove rows where MeasurementType == locality
            df = df[df[col].astype(str).str.lower() != "locality"]

            removed = original_rows - len(df)

            # Save back to the same file
            df.to_excel(file, index=False)

            print(f"{file.name}: removed {removed} rows")

        except Exception as e:
            print(f"Error processing {file.name}: {e}")

print("Done!")