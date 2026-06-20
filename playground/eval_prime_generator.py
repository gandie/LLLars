#!/usr/bin/env python3
"""Evaluation script for Prime Generator - Tests for 1 second and counts primes."""
import subprocess
import sys
import json
import time

def count_primes():
    """Call prime generator for 1 second and count primes returned."""
    time_limit = 1.0  # seconds
    
    # Start timer and process prime generator
    start_time = time.time()
    
    # Run prime generator with 1 second time limit
    result = subprocess.run(
        ["python", "prime_generator.py", str(time_limit)],
        capture_output=True,
        text=True,
        timeout=time_limit + 1  # Extra buffer for safety
    )
    
    # Wait for subprocess if it completes faster
    remaining = max(0, time_limit - (time.time() - start_time))
    time.sleep(remaining)
    
    # Parse JSON output and count primes
    try:
        prime_count = len(json.loads(result.stdout))
        return result.returncode == 0, prime_count
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        return False, 0

if __name__ == "__main__":
    success, prime_count = count_primes()
    print(json.dumps({"success": success, "prime_count": prime_count}))
    sys.exit(0 if success else 1)
