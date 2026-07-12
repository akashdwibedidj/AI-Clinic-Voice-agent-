import subprocess
import sys

scripts = [
    'rag/1_extract_text.py',
    'rag/2_convert_to_chunks.py', 
    'rag/3_convert_to_embedings.py',
    'rag/4_store_to_vector.py',
]
print("="*50)
print("BookRDR - Add New Books Pipeline")
print("="*50)

for script in scripts:
    print(f"Running {script}...")
    result = subprocess.run([sys.executable, script])
    
    if result.returncode != 0:
        print(f"FAILED at {script} — stopping pipeline")
        break
    
    print(f"✅ {script} complete")

print("\n" + "="*50)
print("\nFull pipeline done!")
print("="* 50)
