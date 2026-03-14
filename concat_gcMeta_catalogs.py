import pandas as pd

# Define the uploaded summary statistics files and their corresponding ecosystems
files = {
    "Agricultural Soil": "PCyc_Summary_Stats_Agri_Soil.tsv",
    "Arabidopsis Rhizosphere": "PCyc_Summary_Stats_Arab_Rhizo.tsv",
    "Bean Rhizosphere": "PCyc_Summary_Stats_Bean_Rhizo.tsv",
    "Rice Rhizosphere": "PCyc_Summary_Stats_Rice_Rhizo.tsv",
    "Wheat Rhizosphere": "PCyc_Summary_Stats_Wheat_Rhizo.tsv"
}

dfs = []
for ecosystem, file_path in files.items():
    try:
        # Read each TSV file
        df = pd.read_csv(file_path, sep='\t')
        
        # Add a column to identify the source ecosystem
        df['Ecosystem'] = ecosystem
        dfs.append(df)
    except FileNotFoundError:
        print(f"File not found: {file_path}")

if dfs:
    # Concatenate all datasets vertically
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Clean up column names just in case there are hidden spaces
    merged_df.columns = merged_df.columns.str.strip()
    
    # Pivot the data to create a clean comparison matrix
    # Rows = Specific Phosphorus Genes, Columns = Ecosystems, Values = Gene Counts
    comparison_matrix = merged_df.pivot(index='PCyc_Gene', columns='Ecosystem', values='Count').fillna(0).astype(int)
    
    # Calculate a total count across all ecosystems to sort by global abundance
    comparison_matrix['Global_Total'] = comparison_matrix.sum(axis=1)
    comparison_matrix = comparison_matrix.sort_values(by='Global_Total', ascending=False)
    
    # Export to CSV
    output_filename = "Global_PCyc_Ecosystem_Comparison.csv"
    comparison_matrix.to_csv(output_filename)
    
    print(f"Successfully combined {len(dfs)} catalogs into a single matrix!")
    print(f"Total unique phosphorus cycling genes tracked: {len(comparison_matrix)}")
    print(f"Exported to: {output_filename}\n")
    
    print("--- Top 10 Most Abundant Phosphorus Genes Across All Ecosystems ---")
    print(comparison_matrix.drop(columns=['Global_Total']).head(10).to_string())
    
    # Let's also isolate the 'phn' genes specifically to see their distribution
    phn_only = comparison_matrix[comparison_matrix.index.str.contains('phn', case=False, na=False)]
    print("\n--- Distribution of the Core C-P Lyase (phn) Subunits ---")
    print(phn_only.drop(columns=['Global_Total']).head(8).to_string())