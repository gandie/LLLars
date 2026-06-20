#!/usr/bin/env python3
"""Prime Number Generator - Generates primes until time limit expires."""
import sys
import time
import json

def is_prime(n):
    """Check if a number is prime in O(sqrt(n)) time."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def main():
    """Generate primes continuously until time limit expires."""
    if len(sys.argv) < 2:
        print("Usage: prime_generator.py <time_limit_in_seconds>", file=sys.stderr)
        sys.exit(1)
    
    try:
        time_limit = int(float(sys.argv[1]))
    except ValueError:
        print(f"Invalid time limit: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)
    
    start_time = time.time()
    primes = []
    n = 2
    
    while time.time() - start_time < time_limit:
        if is_prime(n):
            primes.append(n)
        n += 1
    
    print(json.dumps(primes))

if __name__ == "__main__":
    main()
