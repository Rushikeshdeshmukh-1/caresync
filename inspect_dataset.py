import pandas as pd
import json

file_path = r"C:\Users\RUSHIKESH\Desktop\my all projects\2\data\AyurGenixAI_Dataset.xlsx"
output_path = r"C:\Users\RUSHIKESH\Desktop\my all projects\2\dataset_info.txt"

try:
    df = pd.read_excel(file_path)
    info = {
        "columns": df.columns.tolist(),
        "first_row": df.iloc[0].to_dict()
    }
    with open(output_path, "w") as f:
        json.dump(info, f, indent=2, default=str)
    print(f"Info written to {output_path}")
except Exception as e:
    print(f"Error reading Excel: {e}")
