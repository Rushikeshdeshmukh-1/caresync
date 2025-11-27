
import csv
import os
import shutil

def normalize_namaste():
    old_csv_path = 'data/namaste.csv'
    new_csv_path = 'data/NATIONAL AYURVEDA MORBIDITY CODES.csv'
    output_csv_path = 'data/namaste_new.csv'

    # 1. Load existing mappings (Term -> ICD Code)
    existing_mappings = {}
    if os.path.exists(old_csv_path):
        with open(old_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                display = row.get('display', '').strip()
                icd_code = row.get('icd11_tm2_code', '').strip()
                if display and icd_code:
                    existing_mappings[display.lower()] = icd_code
        print(f"Loaded {len(existing_mappings)} existing mappings.")

    # 2. Process new dataset
    new_rows = []
    if os.path.exists(new_csv_path):
        with open(new_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Columns: Sr No.,NAMC_ID,NAMC_CODE,NAMC_term,NAMC_term_diacritical,NAMC_term_DEVANAGARI,Short_definition,Long_definition,Ontology_branches
            
            for row in reader:
                code = row.get('NAMC_CODE', '').strip()
                term = row.get('NAMC_term', '').strip()
                
                # Definition: Prefer Long, fallback to Short
                definition = row.get('Long_definition', '').strip()
                if not definition:
                    definition = row.get('Short_definition', '').strip()
                
                # Clean up definition (remove quotes if double wrapped)
                definition = definition.replace('"', '')

                # Look up ICD code
                icd_code = existing_mappings.get(term.lower(), '')
                
                # Create new row
                new_row = {
                    'code': code,
                    'display': term,
                    'definition': definition,
                    'system_description': 'National Ayurveda Morbidity Codes',
                    'system': 'NAMASTE',
                    'who_term': '', # We don't have this in new data
                    'icd11_tm2_code': icd_code
                }
                new_rows.append(new_row)
        
        print(f"Processed {len(new_rows)} rows from new dataset.")
    else:
        print(f"Error: New dataset not found at {new_csv_path}")
        return

    # 3. Write new CSV
    fieldnames = ['code', 'display', 'definition', 'system_description', 'system', 'who_term', 'icd11_tm2_code']
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)
    
    print(f"Written normalized data to {output_csv_path}")

if __name__ == "__main__":
    normalize_namaste()
