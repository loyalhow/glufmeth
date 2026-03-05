import pandas as pd

# 1. Define your input file
file_path = "gcMeta_Agri_Soil_PCycDB_Results_FixedORF2Pgene.txt"

# 2. Load the data (no headers in the original file, so we assign them)
print(f"Loading data from {file_path}...")
df = pd.read_csv(file_path, sep='\t', header=None, names=['ORF_ID', 'PCyc_Gene'])

# 3. Calculate absolute counts for each gene
gene_counts = df['PCyc_Gene'].value_counts().reset_index()
gene_counts.columns = ['PCyc_Gene', 'Count']

# 4. Calculate relative abundance (Percentage of total P-cycling ORFs)
total_genes = len(df)
gene_counts['Relative_Abundance_(%)'] = (gene_counts['Count'] / total_genes * 100).round(2)

# 5. Display the top 15 most abundant genes in the terminal
print("\n" + "="*50)
print(f"TOTAL P-CYCLING ORFs IDENTIFIED: {total_genes}")
print("="*50)
print("TOP 15 MOST ABUNDANT GENES:")
print("-" * 50)
print(gene_counts.head(15).to_string(index=False))
print("="*50 + "\n")

# 6. Save the full statistics to a new TSV file for your records
output_file = "PCyc_Gene_Summary_Stats.tsv"
gene_counts.to_csv(output_file, sep='\t', index=False)
print(f"Full summary successfully saved to: {output_file}")