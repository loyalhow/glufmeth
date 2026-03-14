import pandas as pd
from Bio import SeqIO
import os

# 1. Load the Diamond results and isolate the 134 high-confidence IDs
columns = ['qseqid', 'sseqid', 'pident', 'length', 'evalue', 'bitscore']
df = pd.read_csv('gcMeta_Wheat_PCycDB_Results.tsv', sep='\t', header=None, names=columns)

df_phn = df[
    (df['sseqid'].str.contains('phn:', case=False)) & 
    (~df['sseqid'].str.contains('sphn:', case=False))
]
df_high_conf = df_phn[(df_phn['evalue'] < 1e-5) & (df_phn['pident'] > 50.0) & (df_phn['length'] > 50)]

# Extract the list of target sequence IDs
target_ids = set(df_high_conf['qseqid'].tolist())
print(f"Looking for {len(target_ids)} target sequences in the master catalog...")

# 2. Parse the Master Catalog and extract the context
master_faa = "Master_Catalog_Wheat_Rhizo.faa"
output_faa = "phn_Targets_Context_Wheat_Rhizo.faa"
extracted_count = 0

# We need to grab the target AND the genes immediately surrounding it on the contig
# (e.g., if target is Gene_005, we also want Gene_004 and Gene_006)

with open(output_faa, "w") as out_handle:
    # A simple buffer to hold the previous sequence
    prev_seq_record = None
    
    # We use SeqIO.parse for robust Fasta handling
    for record in SeqIO.parse(master_faa, "fasta"):
        
        # If the CURRENT sequence is a target...
        if record.id in target_ids:
            # Write the previous gene (if one exists)
            if prev_seq_record:
                 SeqIO.write(prev_seq_record, out_handle, "fasta")
            
            # Write the target gene
            SeqIO.write(record, out_handle, "fasta")
            extracted_count += 1
            
            # Since we hit a target, we want to grab the NEXT gene too.
            # We flag this so the next iteration knows to save it.
            record.is_target_neighbor = True 
            
        # If the PREVIOUS sequence was a target, this is the neighbor after it.
        elif getattr(prev_seq_record, "is_target_neighbor", False):
             SeqIO.write(record, out_handle, "fasta")
             # Reset the flag
             record.is_target_neighbor = False
             
        # Update the buffer
        prev_seq_record = record

print(f"Success! Extracted {extracted_count} target zones into {output_faa}.")