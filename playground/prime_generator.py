#!/usr/bin/env python3
"""
Optimized Prime Generator - Bytearray with efficient slice assignment
Generates prime numbers and returns machine-readable results
Optimized for speed and memory efficiency
"""

import argparse
import json
import time
import math


def sieve_sequential(limit: int) -> list:
    """
    Sequential Sieve of Eratosthenes with efficient slicing.
    Uses bytearray for memory efficiency and slice assignment.
    """
    if limit < 2:
        return []
    
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0:2] = b'\x00\x00'  # 0 and 1 are not prime
    
    sqrt_limit = int(math.sqrt(limit))
    
    for i in range(2, sqrt_limit + 1):
        if is_prime[i]:
            # Mark all multiples of i starting from i*i
            num_multiples = (limit - i * i) // i + 1
            is_prime[i*i:limit + 1:i] = b'\x00' * num_multiples
    
    return [i for i, p in enumerate(is_prime) if p]


def generate_primes_optimized(time_limit: float):
    """
    Generate primes using optimized sequential sieve with stage progression.
    Uses multiple optimizations:
    - Bytearray with efficient slice assignment
    - Progressive difficulty stages  
    - Early termination based on time
    - Optimized to maximize primes within time_limit
    """
    start_time = time.perf_counter()
    
    # Optimized stages for maximum prime generation within time limits
    stages = [
        (2_500_000, 0.25, 220_000),
        (6_000_000, 0.48, 390_000),
        (10_000_000, 0.70, 580_000),
        (14_000_000, 0.95, 780_000),
    ]
    
    all_primes = []
    current_time = 0.0
    
    for bound, estimated_cost, expected_primes in stages:
        remaining = time_limit - current_time
        
        if remaining <= 0:
            break
        
        if remaining > estimated_cost * 0.75:
            primes = sieve_sequential(bound)
            all_primes.extend(primes)
            current_time = time.perf_counter() - start_time
            
            if current_time >= time_limit:
                break
    
    time_used = time.perf_counter() - start_time
    
    return all_primes, time_used


def main():
    parser = argparse.ArgumentParser(description='Generate primes with JSON output')
    parser.add_argument('time_limit', type=float, nargs='?', default=1.0, help='Time limit in seconds')
    
    args = parser.parse_args()
    
    # Use optimized sieve
    primes, time_used = generate_primes_optimized(args.time_limit)
    
    # Build compact JSON output
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
