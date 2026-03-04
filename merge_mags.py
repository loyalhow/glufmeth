import os
import gzip

output_file = "gcMeta_Master_DNA.fna"
directory = "." # Looks in the current folder

print("Merging MAGs... this might take a minute.")
with open(output_file, 'wb') as outfile:
    for filename in os.listdir(directory):
        if filename.endswith(".fa.gz"):
            with gzip.open(os.path.join(directory, filename), 'rb') as infile:
                # Add a newline between files just to be safe
                outfile.write(infile.read() + b"\n")

print(f"Success! All MAGs combined into {output_file}")