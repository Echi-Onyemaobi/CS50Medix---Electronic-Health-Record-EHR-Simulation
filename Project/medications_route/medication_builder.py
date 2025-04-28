# fresh_medication_dictionary_builder.py
import requests
import sqlite3
import time

# DB Connection
conn = sqlite3.connect("ehr.db")
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS MedicationDictionary (
    rxcui TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dosage_form TEXT,
    strength TEXT,
    brand_name TEXT
);
""")
conn.commit()

# Medication list
seed_meds = [
    "Acetaminophen", "Ibuprofen", "Amoxicillin", "Metformin", "Atorvastatin",
    "Simvastatin", "Omeprazole", "Levothyroxine", "Lisinopril", "Losartan",
    "Amlodipine", "Hydrochlorothiazide", "Albuterol", "Prednisone", "Ciprofloxacin",
    "Azithromycin", "Gabapentin", "Duloxetine", "Sertraline", "Fluoxetine",
    "Warfarin", "Clopidogrel", "Insulin Glargine", "Tamsulosin", "Ranitidine",
    "Pantoprazole", "Lorazepam", "Diazepam", "Nitroglycerin", "Oxycodone",
    "Morphine", "Furosemide", "Spironolactone", "Metoprolol", "Atenolol",
    "Carvedilol", "Sitagliptin", "Glipizide", "Doxycycline", "Amoxicillin-Clavulanate",
    "Naproxen", "Cetirizine", "Loratadine", "Diphenhydramine", "Montelukast",
    "Fluticasone", "Salbutamol", "Aztreonam", "Levofloxacin", "Vancomycin",
    "Hydromorphone", "Methadone", "Tramadol", "Clindamycin", "Cephalexin",
    "Linezolid", "Rosuvastatin", "Pravastatin", "Hydralazine", "Isosorbide Mononitrate",
    "Allopurinol", "Colchicine", "Methotrexate", "Sodium Bicarbonate", "Potassium Chloride",
    "Iron Supplement", "Vitamin B12", "Vitamin D3", "Folic Acid", "Calcium Carbonate",
    "Magnesium Oxide", "Enoxaparin", "Apixaban", "Rivaroxaban", "Dabigatran",
    "Insulin Aspart", "Insulin Lispro", "Insulin Detemir", "Risperidone", "Olanzapine",
    "Aripiprazole", "Quetiapine", "Haloperidol", "Alprazolam", "Clonazepam", "Propranolol",
    "Diltiazem", "Verapamil", "Digoxin", "Chlorthalidone", "Bumetanide", "Ethacrynic Acid",
    "Tadalafil", "Sildenafil", "Finasteride", "Dutasteride", "Cyclobenzaprine", "Tizanidine",
]

# Track inserted meds
inserted_meds = set()

for med in seed_meds:
    try:
        search_resp = requests.get("https://rxnav.nlm.nih.gov/REST/approximateTerm.json", params={"term": med})
        search_resp.raise_for_status()
        candidates = search_resp.json().get("approximateGroup", {}).get("candidate", [])

        for candidate in candidates:
            rxcui = candidate.get("rxcui")
            if rxcui and rxcui not in inserted_meds:
                # Now fetch properties for full details
                prop_resp = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json")
                prop_resp.raise_for_status()
                props = prop_resp.json().get("properties", {})

                if props:
                    inserted_meds.add(rxcui)
                    cur.execute("""
                        INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        props.get("rxcui"),
                        props.get("name"),
                        props.get("dosageFormName"),
                        props.get("strength"),
                        props.get("brandName")
                    ))
                    conn.commit()


                # Sleep a little to avoid hitting API rate limits
                time.sleep(0.1)

                if len(inserted_meds) >= 1000:
                    break

    except Exception as e:
        print(f"Error fetching {med}: {e}")

print(f"Done! {len(inserted_meds)} medications inserted with full details!")
conn.close()
