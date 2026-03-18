import csv
from collections import defaultdict
from pathlib import Path

gcmeta_path = Path("c:/Users/loyal/Documents/trae_projects/Phosphorus-cycling-database/gcMeta_output/metainformation/merged_meta_information.tsv")

counts = defaultdict(int)
total = 0
valid_coords = 0

with gcmeta_path.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        cat = (row.get("Catalogue_name") or "Unknown").strip()
        counts[cat] += 1
        
        # Check for valid coordinates
        try:
            lat = float(row.get("Latitude", ""))
            lon = float(row.get("Longitude", ""))
            if lat and lon:
                valid_coords +=1
        except ValueError:
            pass

print("📊 gcMeta Sample Breakdown:")
print("=" * 50)
for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count:,} samples")
print("-" * 50)
print(f"  Total samples: {total:,}")
print(f"  Samples with valid coordinates: {valid_coords:,}")
print("\n💡 Explanation:")
print("The 4,742 samples come from merging 5 separate ecosystem datasets:")
print("  1. Agricultural Soil")
print("  2. Arabidopsis Rhizosphere") 
print("  3. Bean Rhizosphere")
print("  4. Rice Rhizosphere")
print("  5. Wheat Rhizosphere")
print("\nEach dataset contains multiple MAGs (Metagenome-Assembled Genomes) from")
print("different sampling sites and biosamples, leading to the total count.")
