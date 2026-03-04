import sys
from collections import defaultdict
from Bio import SeqIO

def parse_header(header):
    """
    Parses a typical Prodigal/Metagenomic header to extract contig, coordinates, and strand.
    Example: GCMeta_00120034_00413_3 # 2517 # 4325 # 1 # ...
    """
    parts = header.split("#")
    if len(parts) >= 4:
        gene_id = parts[0].strip()
        start = int(parts[1].strip())
        stop = int(parts[2].strip())
        strand = int(parts[3].strip())
        
        # Typically, the ID format is [Contig_ID]_[Gene_Number]
        # We assume the last underscore separates the contig ID from the gene number.
        id_parts = gene_id.rsplit('_', 1)
        contig_id = id_parts[0] if len(id_parts) > 1 else gene_id
        
        return contig_id, gene_id, start, stop, strand
    return None, None, None, None, None

def analyze_operons(fasta_file):
    # Dictionary to group genes by their parent contig
    contigs = defaultdict(list)
    
    print(f"Reading target sequences from: {fasta_file}...")
    
    for record in SeqIO.parse(fasta_file, "fasta"):
        contig_id, gene_id, start, stop, strand = parse_header(record.description)
        if contig_id:
            contigs[contig_id].append({
                'gene_id': gene_id,
                'start': start,
                'stop': stop,
                'strand': strand,
                'description': record.description
            })

    print(f"Found {len(contigs)} unique target contigs. Analyzing architecture...\n")
    
    operon_clusters = []
    
    for contig_id, genes in contigs.items():
        # Sort genes by their starting coordinate on the contig
        genes_sorted = sorted(genes, key=lambda x: x['start'])
        
        print(f"--- Contig: {contig_id} ---")
        
        # Simple grouping check: are these genes on the same strand and physically close?
        # A typical operon distance is < 50-100 base pairs.
        current_cluster = [genes_sorted[0]]
        
        for i in range(1, len(genes_sorted)):
            prev_gene = current_cluster[-1]
            curr_gene = genes_sorted[i]
            
            # Calculate distance (assuming start < stop)
            distance = curr_gene['start'] - prev_gene['stop']
            
            # Same strand and physically close
            if curr_gene['strand'] == prev_gene['strand'] and distance < 200:
                current_cluster.append(curr_gene)
            else:
                operon_clusters.append(current_cluster)
                current_cluster = [curr_gene]
                
        if current_cluster:
            operon_clusters.append(current_cluster)
            
        # Print out the layout for this contig
        for gene in genes_sorted:
            direction = "==>" if gene['strand'] == 1 else "<=="
            print(f"  {gene['gene_id']:<25} | {gene['start']:>8} - {gene['stop']:<8} | {direction}")
            
    print(f"\nTotal potential operon blocks identified: {len(operon_clusters)}")

if __name__ == "__main__":
    analyze_operons("phn_Targets_Context_Wheat_Rhizo.faa")