import pandas as pd
from Bio import Entrez
import time
import xml.etree.ElementTree as ET
import re

# --- CONFIGURATION ---
Entrez.email = "haoliu_@fudan.edu.cn"  # Must be filled in!
input_file = "Agricultural_Soil_all_MAGs.metainfo.txt"
output_file = "Agricultural_Soil_MAGs_with_GIS.csv"
# ---------------------

def parse_lat_lon(geo_string):
    """Parses various NCBI lat_lon formats into decimal degrees."""
    if not geo_string or str(geo_string).lower() in ['na', 'nan', 'none', '']:
        return None, None

    clean_str = str(geo_string).replace(',', ' ').upper().strip()
    numbers = re.findall(r'-?\d+\.?\d*', clean_str)
    
    if len(numbers) < 2:
        return None, None
        
    try:
        lat = float(numbers[0])
        lon = float(numbers[1])
        
        if 'S' in clean_str and lat > 0: lat = -lat
        if 'W' in clean_str and lon > 0: lon = -lon
            
        return lat, lon
    except ValueError:
        return None, None

def fetch_biosample_locations(biosample_ids):
    results = {}
    batch_size = 40  # Lowered slightly to prevent URL length limits
    
    clean_ids = [str(x).strip() for x in biosample_ids if 'SAM' in str(x).upper()]
    total = len(clean_ids)
    
    print(f"Fetching metadata for {total} valid samples...")

    for i in range(0, total, batch_size):
        batch = clean_ids[i:i+batch_size]
        try:
            # STEP 1: Translate Accessions (SAMN...) to internal UIDs using esearch
            # We build a query like "SAMN01[Accession] OR SAMN02[Accession]"
            search_term = " OR ".join([f"{acc}[Accession]" for acc in batch])
            search_handle = Entrez.esearch(db="biosample", term=search_term, retmax=batch_size)
            search_record = Entrez.read(search_handle, validate=False)
            uids = search_record.get("IdList", [])
            
            if not uids:
                print(f"Warning: No UIDs found for batch {i}. Skipping.")
                continue

            # STEP 2: Fetch the actual data using the numeric UIDs
            # We add validate=False to prevent Biopython from crashing on NCBI errors
            summary_handle = Entrez.esummary(db="biosample", id=",".join(uids))
            summaries = Entrez.read(summary_handle, validate=False) 
            
            for record in summaries['DocumentSummarySet']['DocumentSummary']:
                acc = record['Accession']
                sample_xml = record['SampleData']
                
                lat_lon_raw = "NA"
                country = "NA"
                
                try:
                    root = ET.fromstring(f"<root>{sample_xml}</root>")
                    for attr in root.findall(".//Attribute"):
                        name = attr.get('attribute_name')
                        if name == 'lat_lon':
                            lat_lon_raw = attr.text
                        elif name == 'geo_loc_name':
                            country = attr.text
                except:
                    pass
                
                results[acc] = {'lat_lon_raw': lat_lon_raw, 'country': country}
                
        except Exception as e:
            print(f"Error in batch {i}: {e}")
        
        time.sleep(1) # Crucial: Be polite to the server to avoid getting temporarily blocked
        print(f"Processed {min(i+batch_size, total)}/{total}")

    return results

# --- MAIN EXECUTION ---
print("1. Loading input file...")
df = pd.read_csv(input_file, sep="\t")

unique_ids = df['Biosample'].dropna().unique().tolist()

print("2. Retrieving data from NCBI...")
loc_data = fetch_biosample_locations(unique_ids)

if not loc_data:
    print("CRITICAL: No data retrieved. Please check your internet connection or Entrez email.")
    exit()

print("3. Parsing coordinates...")
loc_df = pd.DataFrame.from_dict(loc_data, orient='index').reset_index()
loc_df.columns = ['Biosample', 'Lat_Lon_Raw', 'Country']

coords = loc_df['Lat_Lon_Raw'].apply(parse_lat_lon)
loc_df[['Latitude', 'Longitude']] = pd.DataFrame(coords.tolist(), index=loc_df.index)

final_df = pd.merge(df, loc_df, on='Biosample', how='left')

final_df.to_csv(output_file, index=False)
print(f"Done! Clean data saved to {output_file}")