import csv
import os

def prepare_data():
    base_path = "c:\\work\\seed_core"
    specs_path = os.path.join(base_path, "references", "Variety Specifications.csv")
    names_path = os.path.join(base_path, "references", "Commercial Names.csv")
    output_path = os.path.join(base_path, "seed_core", "fixtures", "seed_variety_import_full.csv")

    # Read Commercial Names into a dict keyed by Variety Code
    # Format: Country, Variety Code, Type, Comm. Name, Registration
    commercial_names = {}
    with open(names_path, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("Variety Code", "").strip()
            if not code:
                continue
            if code not in commercial_names:
                commercial_names[code] = []
            commercial_names[code].append({
                "country": row.get("Country", "").strip(),
                "commercial_name": row.get("Comm. Name", "").strip(),
                "registration_status": "Registered" if "Registered" in row.get("Registration", "") else "In Progress"
            })

    # Read Specs and write combined CSV
    # Specs: CROPS,CODE,PLANT,FRUIT,RESISTANCE,CULTIVATION
    with open(specs_path, 'r', encoding='latin-1') as f_in, \
         open(output_path, 'w', newline='', encoding='utf-8') as f_out:
        
        reader = csv.DictReader(f_in)
        
        # Define output columns
        fieldnames = [
            "variety_name", "crop", "segment", 
            "plant_characteristics", "fruit_characteristics", 
            "resistance_codes", "cultivation_environment",
            "description",
            "variety_names.country", "variety_names.commercial_name", "variety_names.registration_status"
        ]
        
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            code = row.get("CODE", "").strip()
            if not code:
                continue

            # Basic mapping
            # Note: Segment is missing in specs, limiting to known data
            # Description combining Plant, Fruit, Cultivation
            description = f"Plant: {row['PLANT']}\nFruit: {row['FRUIT']}\nCultivation: {row['CULTIVATION']}"
            
            main_row = {
                "variety_name": code,
                "crop": row.get("CROPS", "").strip(), # Need to ensure this matches Seed Crop names?
                "segment": "", # Unknown
                "plant_characteristics": row.get("PLANT", ""),
                "fruit_characteristics": row.get("FRUIT", ""),
                "resistance_codes": row.get("RESISTANCE", ""),
                "cultivation_environment": row.get("CULTIVATION", ""),
                "description": description
            }

            # Add child rows if any match
            names = commercial_names.get(code, [])
            
            if not names:
                # Write single row
                writer.writerow(main_row)
            else:
                # Write first row with main data + first child
                first_name = names[0]
                full_row = main_row.copy()
                full_row.update({
                    "variety_names.country": first_name["country"],
                    "variety_names.commercial_name": first_name["commercial_name"],
                    "variety_names.registration_status": first_name["registration_status"]
                })
                writer.writerow(full_row)

                # Write subsequent child rows (main fields empty)
                for name in names[1:]:
                    child_row = {k: "" for k in fieldnames} # Empty row
                    # Key ID 'variety_name' usually needed for update/upsert, 
                    # but for fresh import typically we leave main blank OR fill it. 
                    # Frappe Data Import usually prefers main ID filled for all rows OR just first.
                    # Safest is filling main ID (variety_name) for all rows to group them.
                    child_row["variety_name"] = code
                    child_row.update({
                        "variety_names.country": name["country"],
                        "variety_names.commercial_name": name["commercial_name"],
                        "variety_names.registration_status": name["registration_status"]
                    })
                    writer.writerow(child_row)

    print(f"Generated import file at {output_path}")

if __name__ == "__main__":
    prepare_data()
