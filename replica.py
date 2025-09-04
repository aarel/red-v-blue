import os
import shutil

# This function demonstrates a self-replicating script for educational purposes.
# It copies the current script into a 'replicas' directory as 'worm_copy.py' to illustrate replication behavior.

def replicate():
    src = __file__                      # current script
    dst = os.path.join("replicas", "worm_copy.py")
    os.makedirs("replicas", exist_ok=True)
    shutil.copy(src, dst)
    print(f"[+] Worm copied itself to {dst}")

if __name__ == "__main__":
    replicate()