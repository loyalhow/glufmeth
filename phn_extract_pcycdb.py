input_fasta = "PCycDBv1.1.faa"

print("Scanning PCycDB and extracting sequences. Please wait...")

with open(input_fasta, "r") as infile, \
     open("PCycDB_phnJ.faa", "w") as out_j, \
     open("PCycDB_phnY.faa", "w") as out_y:
     
     write_j = False
     write_y = False
     
     for line in infile:
         if line.startswith(">"):
             # Reset writing flags for every new sequence header
             write_j = False
             write_y = False
             
             # Check if the header contains our target gene names
             if "phnJ" in line:
                 write_j = True
                 out_j.write(line)
             elif "phnY" in line:
                 write_y = True
                 out_y.write(line)
         else:
             # If the flag is True, write the amino acid sequence lines
             if write_j:
                 out_j.write(line)
             elif write_y:
                 out_y.write(line)
                 
print("Extraction complete! Your PCycDB_phnJ.faa and PCycDB_phnY.faa files are ready.")