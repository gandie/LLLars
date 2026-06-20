#!/usr/bin/env python3
"""
Optimized Prime Generator Evaluator - JSON Output Only
Tests prime generation speed and efficiency with various time limits
"""

import subprocess
import json
import time
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def is_prime(n: int) -> bool:
    """
    Verify a single number is prime using trial division.
    This is a primitive check for validation purposes.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    sqrt_n = int(n ** 0.5) + 1
    for i in range(3, sqrt_n, 2):
        if n % i == 0:
            return False
    return True


def is_prime_list_valid(primes: list) -> dict:
    """
    Verify all numbers in a list are actually prime.
    Returns validation statistics.
    """
    if not primes:
        return {'valid': False, 'error': 'Empty list'}
    
    verified_count = 0
    failed_indices = []
    
    for i, prime in enumerate(primes):
        if is_prime(prime):
            verified_count += 1
        else:
            failed_indices.append((i, prime))
    
    # Check for proper ordering (primes should be increasing)
    ordering_ok = True
    for i in range(1, len(primes)):
        if primes[i] <= primes[i-1]:
            ordering_ok = False
            break
    
    return {
        'valid': len(failed_indices) == 0 and ordering_ok,
        'verified_count': verified_count,
        'total_count': len(primes),
        'failed_indices': failed_indices,
        'ordering_correct': ordering_ok
    }


def verify_first_n_primes(known_primes: list, generated: list) -> dict:
    """
    Verify generated primes match expected first n primes.
    Returns validation results against sample results with n=5.
    """
    # For n=5 test, we expect: 2, 3, 5, 7, 11 (first 5 primes)
    n = len(known_primes)
    
    if len(generated) < n:
        return {
            'matched': False,
            'error': f'Generated fewer primes than required ({len(generated)} < {n})',
            'matched_count': min(len(generated), n),
            'expected': known_primes[:len(generated)],
            'actual': generated[:len(generated)]
        }
    
    # Check each of first n primes match
    mismatches = []
    for i in range(n):
        if generated[i] != known_primes[i]:
            mismatches.append((i, known_primes[i], generated[i]))
    
    return {
        'matched': len(mismatches) == 0,
        'n': n,
        'mismatches': mismatches,
        'expected_first_n': known_primes,
        'actual_first_n': generated[:n]
    }


def run_prime_generator(time_limit: float) -> dict:
    """Run the prime generator and capture results"""
    try:
        result = subprocess.run(
            [sys.executable, 'prime_generator.py', str(time_limit)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=int(time_limit) + 10
        )
        
        if result.returncode != 0:
            return {'error': result.stderr}
        
        output = result.stdout.strip()
        
        # Parse JSON from output (compact format)
        try:
            detailed_results = json.loads(output)
            # Normalize field names for consistent access
            detailed_results['primes_count'] = detailed_results.get('count', 0)
            detailed_results['time_used'] = detailed_results.get('time_used', 0)
            detailed_results['time_limit'] = detailed_results.get('time_limit', time_limit)
            detailed_results['primes'] = {
                'first': detailed_results.get('primes', {}).get('first_10', []),
                'last': detailed_results.get('primes', {}).get('last_10', []),
                'max': detailed_results.get('primes', {}).get('max', 0)
            }
            
            # Add verification checks
            primes_list = detailed_results['primes']['first']
            
            # Verify the list (if not empty)
            verification_stats = None
            if primes_list:
                verification_stats = is_prime_list_valid(primes_list)
            
            # Add n=5 sample verification
            known_first_5 = [2, 3, 5, 7, 11]
            n5_verification = None
            if primes_list and len(primes_list) >= 5:
                n5_verification = verify_first_n_primes(known_first_5, primes_list)
            
            detailed_results['primes']['verification'] = verification_stats
            detailed_results['primes']['n5_sample_verification'] = n5_verification
            detailed_results['verification_passed'] = verification_stats['valid'] if verification_stats else True
            
            return detailed_results
        except json.JSONDecodeError:
            return {'error': 'Could not parse JSON output'}
        
    except subprocess.TimeoutExpired:
        return {'error': 'Generation timed out', 'timeout': time_limit}
    except Exception as e:
        return {'error': str(e)}


def evaluate_performance():
    """Main evaluation function - outputs only JSON"""
    time_limits = [0.5, 1.0, 2.0]  # Use shorter times for quicker testing
    
    all_results = {}
    
    for time_limit in time_limits:
        result = run_prime_generator(time_limit)
        
        if 'error' not in result:
            all_results[time_limit] = result
    
    # Summary structure
    summary = {
        'evaluation_metadata': {
            'description': 'Prime Generator Performance Evaluation',
            'version': '1.0',
            'timestamp': time.time()
        },
        'results': {},
        'summary_stats': {}
    }
    
    # Populate results
    for time_limit, result in sorted(all_results.items()):
        if 'error' not in result:
            summary['results'][time_limit] = {
                'primes_count': result.get('primes_count', 0),
                'time_used': result.get('time_used', 0),
                'time_limit': time_limit,
                'efficiency': result.get('primes_count', 0) / result.get('time_used', 1) if result.get('time_used', 0) > 0 else 0
            }
            
            # Add verification info to each result
            summary['results'][time_limit]['verification_passed'] = result.get('verification_passed', True)
            summary['results'][time_limit]['verification_stats'] = result.get('primes', {}).get('verification')
            summary['results'][time_limit]['n5_verification'] = result.get('primes', {}).get('n5_sample_verification')
    
    # Calculate summary stats
    if summary['results']:
        times = sorted([k for k in summary['results'].keys()])
        if len(times) >= 2:
            start = summary['results'][times[0]]
            end = summary['results'][times[-1]]
            
            summary['summary_stats'] = {
                'times_range': f"{times[0]}s -> {times[-1]}s",
                'primes_growth': end.get('primes_count', 0) / start.get('primes_count', 1) if start.get('primes_count') else 0,
                'time_efficiency': end.get('time_used', 0) / start.get('time_used', 1) if start.get('time_used') else 0,
                'all_verifications_passed': all(summary['results'][t].get('verification_passed', False) for t in times if 'error' not in summary['results'][t])
            }
    
    return summary


if __name__ == '__main__':
    # Command line argument support
    if len(sys.argv) > 1:
        try:
            time_limit = float(sys.argv[1])
            result = run_prime_generator(time_limit)
            # Output ONLY JSON
            print(json.dumps(result, indent=2, default=str))
        except Exception as e:
            print(json.dumps({'error': str(e)}), file=sys.stderr)
    else:
        # Run full evaluation - output ONLY JSON
        summary = evaluate_performance()
        print(json.dumps(summary, indent=2, default=str))
