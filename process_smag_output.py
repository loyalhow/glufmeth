import re
from collections import Counter, defaultdict
from pathlib import Path

base = Path("c:/Users/loyal/Documents/trae_projects/Phosphorus-cycling-database/SMAG_output")
orf_dir = base / "ORF2gene_s70"

orf_files = sorted(orf_dir.glob("*.txt"))
merged_path = orf_dir / "merged_ORF2gene_s70.tsv"
phn_path = orf_dir / "phn_family_genes.tsv"
mag_count_path = orf_dir / "MAG_phn_genes_count.tsv"
mag_detail_path = orf_dir / "MAG_phn_genes_detailed_count.tsv"

all_rows = []
for fp in orf_files:
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            all_rows.append((parts[0], parts[1]))

with merged_path.open("w", encoding="utf-8", newline="") as f:
    for oid, gene in all_rows:
        f.write(f"{oid}\t{gene}\n")

phn_rows = [(oid, gene) for oid, gene in all_rows if "phn" in gene.lower()]
with phn_path.open("w", encoding="utf-8", newline="") as f:
    for oid, gene in phn_rows:
        f.write(f"{oid}\t{gene}\n")

mag_pat = re.compile(r"^(.*?)_k\d+_")


def extract_mag(orf_id: str) -> str:
    m = mag_pat.match(orf_id)
    if m:
        return m.group(1)
    if "_" in orf_id:
        return "_".join(orf_id.split("_")[:-1])
    return orf_id


mag_total = Counter()
mag_gene = defaultdict(Counter)
all_phn_genes = set()

for oid, gene in phn_rows:
    mag = extract_mag(oid)
    mag_total[mag] += 1
    mag_gene[mag][gene] += 1
    all_phn_genes.add(gene)

with mag_count_path.open("w", encoding="utf-8", newline="") as f:
    for mag, cnt in sorted(mag_total.items(), key=lambda x: (-x[1], x[0])):
        f.write(f"{mag}\t{cnt}\n")

genes = sorted(all_phn_genes)
with mag_detail_path.open("w", encoding="utf-8", newline="") as f:
    f.write("MAG_ID\t" + "\t".join(genes) + "\n")
    for mag in sorted(mag_gene.keys()):
        vals = [str(mag_gene[mag].get(g, 0)) for g in genes]
        f.write(mag + "\t" + "\t".join(vals) + "\n")

print(f"ORF files merged: {len(orf_files)}")
print(f"Merged rows: {len(all_rows)}")
print(f"phn rows: {len(phn_rows)}")
print(f"MAGs with phn genes: {len(mag_total)}")
print(f"Unique phn gene types: {len(genes)}")
print("Outputs:")
print(merged_path)
print(phn_path)
print(mag_count_path)
print(mag_detail_path)
