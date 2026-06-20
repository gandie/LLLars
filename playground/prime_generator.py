#!/usr/bin/env python3
"""
Optimized Prime Generator - JSON Output Only
Generates prime numbers and returns machine-readable results
"""

import argparse
import json
import time


def generate_primes(time_limit: float):
    """Generate prime numbers using Sieve of Eratosthenes."""
    start_time = time.perf_counter()
    
    stages = [
        (4_000_000, 0.15, 270_000),
        (8_000_000, 0.25, 500_000),
        (12_000_000, 0.38, 920_000),
        (16_000_000, 0.55, 1.25_000_000),
    ]
    
    all_primes = []
    current_time = 0.0
    
    for bound, estimated_cost, expected_primes in stages:
        remaining = time_limit - current_time
        
        if remaining <= 0:
            break
        
        if remaining > estimated_cost * 1.2:
            current_primes = sieve(bound)
            all_primes.extend(current_primes)
            current_time = time.perf_counter() - start_time
            
            if current_time >= time_limit:
                break
    
    time_used = time.perf_counter() - start_time
    
    return all_primes, time_used


def sieve(limit: int) -> list:
    """Sieve of Eratosthenes - find all primes up to limit."""
    if limit < 2:
        return []
    
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0:2] = b'\x00\x00'
    
    sqrt_limit = int(limit ** 0.5)
    for i in range(2, sqrt_limit + 1):
        if is_prime[i]:
            is_prime[i*i:limit+1:i] = b'\x00' * len(is_prime[i*i:limit+1:i])
    
    return [i for i, p in enumerate(is_prime) if p]


def main():
    parser = argparse.ArgumentParser(description='Generate primes with JSON output')
    parser.add_argument('time_limit', type=float, nargs='?', default=1.0, help='Time limit in seconds')
    
    args = parser.parse_args()
    
    primes, time_used = generate_primes(args.time_limit)
    
    # Build compact JSON output (machine-readable, no verbose text)
    result = {
        'count': len(primes),
        'time_limit': args.time_limit,
        'time_used': round(time_used, 3),
        'primes': {
            'first_10': primes[:10],
            'last_10': primes[-10:] if len(primes) >= 10 else [],
            'max': primes[-1] if primes else 0
        }
    }
    
    print(json.dumps(result, default=str))


if __name__ == '__main__':
    main()