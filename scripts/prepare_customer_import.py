import csv
import os
import re

def prepare_customer_data():
    base_path = "c:\\work\\seed_core"
    source_path = os.path.join(base_path, "references", "Distributors & Subsidiaries Yuksel Seeds 2025.csv")
    
    # Target paths
    cg_path = os.path.join(base_path, "seed_core", "fixtures", "Customer Group.csv")
    cust_path = os.path.join(base_path, "seed_core", "fixtures", "Customer.csv")
    addr_path = os.path.join(base_path, "seed_core", "fixtures", "Address.csv")

    # Data structures to hold unique groups and customers
    continents = set()
    countries = set() # (country_name, continent_name)
    customers = []
    addresses = []

    # Country mapping (Reuse from seed variety if needed, but file seems to have full names)
    # The file has "Country" column. We'll use it directly, assuming it matches ERPNext or close enough.
    
    with open(source_path, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            distributor = row.get("Distributor or Subsidiary", "").strip()
            if not distributor:
                continue

            continent = row.get("Continent", "").strip()
            country = row.get("Country", "").strip()
            
            if continent:
                continents.add(continent)
            if country and continent:
                countries.add((country, continent))

            # Customer Data
            customers.append({
                "customer_name": distributor,
                "customer_group": country if country else "All Customer Groups",
                "territory": country if country else "All Territories",
                "website": row.get("Web", "").strip(),
                "email": row.get("Mail", "").strip(),
                "mobile": row.get("Mobile", "").strip(),
                "image": "" # Could map logo if available
            })

            # Address Data
            lat = ""
            lng = ""
            location = row.get("Location", "").strip()
            if location:
                # Expecting "lat, long"
                parts = location.split(',')
                if len(parts) == 2:
                    lat = parts[0].strip()
                    lng = parts[1].strip()

            addresses.append({
                "address_title": distributor,
                "address_line1": row.get("Address", "").strip(),
                "city": "", # Not strictly in CSV, implied in address
                "country": country,
                "phone": row.get("Telephone", "").strip(),
                "email_id": row.get("Mail", "").strip(),
                "link_doctype": "Customer",
                "link_name": distributor,
                "latitude": lat,
                "longitude": lng
            })

    # 1. Write Customer Group CSV
    # Headers: Customer Group Name, Parent Customer Group, Is Group
    with open(cg_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Customer Group Name", "Parent Customer Group", "Is Group"])
        
        # Continents (Parent = All Customer Groups)
        for cont in sorted(list(continents)):
            writer.writerow([cont, "All Customer Groups", 1])
        
        # Countries (Parent = Continent)
        for country, parent in sorted(list(countries)):
            writer.writerow([country, parent, 0])

    print(f"Generated {cg_path}")

    # 2. Write Customer CSV
    # Headers based on reference: ID, Customer Name, Customer Type, Customer Group, Territory, Website, Email Id, Mobile No, Is Internal Customer
    with open(cust_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["ID", "Customer Name", "Customer Type", "Customer Group", "Territory", "Website", "Email Id", "Mobile No", "Is Internal Customer"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for cust in customers:
            writer.writerow({
                "ID": cust["customer_name"], # Use Name as ID for proper linking
                "Customer Name": cust["customer_name"],
                "Customer Type": "Company",
                "Customer Group": cust["customer_group"],
                "Territory": cust["territory"], # Assumes Territory named 'Country' exists or auto-created is fine
                "Website": cust["website"],
                "Email Id": cust["email"],
                "Mobile No": cust["mobile"],
                "Is Internal Customer": 0
            })
            
    print(f"Generated {cust_path}")

    # 3. Write Address CSV
    # Headers: Address Title, Address Line 1, Country, phone, Email Address, Link Document Type (Links), Link Name (Links), Latitude, Longitude
    with open(addr_path, 'w', newline='', encoding='utf-8') as f:
        # Note: mapping 'Phone' in CSV to 'phone' fieldname. 'Email Address' matches.
        fieldnames = ["Address Title", "Address Line 1", "Country", "Phone", "Email Address", "Link Document Type (Links)", "Link Name (Links)", "Latitude", "Longitude"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for addr in addresses:
            writer.writerow({
                "Address Title": addr["address_title"],
                "Address Line 1": addr["address_line1"],
                "Country": addr["country"],
                "Phone": addr["phone"],
                "Email Address": addr["email_id"],
                "Link Document Type (Links)": "Customer",
                "Link Name (Links)": addr["link_name"],
                "Latitude": addr["latitude"],
                "Longitude": addr["longitude"]
            })

    print(f"Generated {addr_path}")

    # 4. Write Territory CSV
    # Headers: Territory Name, Parent Territory, Is Group, Territory Manager
    terr_path = os.path.join(base_path, "seed_core", "fixtures", "Territory.csv")
    with open(terr_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Territory Name", "Parent Territory", "Is Group"])
        
        # Continents
        for cont in sorted(list(continents)):
            writer.writerow([cont, "All Territories", 1])
        
        # Countries
        for country, parent in sorted(list(countries)):
            writer.writerow([country, parent, 0])

    print(f"Generated {terr_path}")

if __name__ == "__main__":
    prepare_customer_data()
