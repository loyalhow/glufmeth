import os
import glob
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

# 1. PASTE YOUR EXACT FOLDER PATH HERE
target_folder = r"." 

search_pattern = os.path.join(target_folder, "*.fa.gz")
mag_files = glob.glob(search_pattern)
total_files = len(mag_files)

print(f"Found {total_files} MAGs. Engaging 16-core parallel processing...\n")

# 2. Define the exact job for a single file
def process_mag(fasta_path):
    base_name = os.path.basename(fasta_path).replace(".fa.gz", "")
    out_faa = os.path.join(target_folder, f"{base_name}.faa")
    
    if os.path.exists(out_faa):
        return
        
    # Notice: NO -j flag here! Each file gets exactly 1 core.
    cmd = f'pyrodigal -i "{fasta_path}" -a "{out_faa}" -p meta'
    
    try:
        subprocess.run(cmd, shell=True, check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"ERROR: Failed on {base_name}.fa.gz")

start_time = time.time()

# 3. The Ryzen Engine: Run 16 files at the exact same time
# max_workers=16 tells Python to keep 16 files processing constantly
with ThreadPoolExecutor(max_workers=16) as executor:
    # Map the files to the workers. Python handles the queue automatically.
    executor.map(process_mag, mag_files)

elapsed = time.time() - start_time
print(f"\nPipeline Complete! Processed {total_files} MAGs in {elapsed/60:.2f} minutes.")