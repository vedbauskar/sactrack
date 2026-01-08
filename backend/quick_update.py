# quick_update.py
"""
Quick update script for testing - updates current term only
"""
import subprocess
import sys

if __name__ == "__main__":
    print("🔄 Running quick update (current term only)...\n")
    subprocess.run([sys.executable, "orchestrator.py"])

