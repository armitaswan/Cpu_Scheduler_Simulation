#!/usr/bin/env python3
"""
Baseline comparison experiment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import SimulationController

def run_baseline_experiment():
    """Run baseline comparison experiment"""
    controller = SimulationController()
    
    print("\n" + "="*80)
    print("EXPERIMENT 1: BASELINE COMPARISON")
    print("="*80)
    print("Objective: Compare all scheduling algorithms with identical workload")
    print("Workload: 500 processes, mixed CPU/I/O characteristics")
    print("Algorithms: FCFS, SJF, SRTF, RR (q=20), Priority (preemptive & non-preemptive)")
    print("="*80)
    
    results = controller.run_baseline_comparison()
    
    print("\n" + "="*80)
    print("EXPERIMENT 1 COMPLETE")
    print("="*80)
    
    # Print best algorithm for each metric
    print("\nBEST PERFORMERS BY METRIC:")
    print("-"*40)
    
    metrics_of_interest = ['avg_turnaround_time', 'avg_waiting_time', 
                          'avg_response_time', 'cpu_utilization', 
                          'throughput', 'fairness_index']
    
    for metric in metrics_of_interest:
        if any(metric in r for r in results.values()):
            # For turnaround, waiting, response: lower is better
            # For CPU util, throughput, fairness: higher is better
            
            if 'turnaround' in metric or 'waiting' in metric or 'response' in metric:
                best_algo = min(results.items(), key=lambda x: x[1].get(metric, float('inf')))
                value = best_algo[1].get(metric, 0)
                print(f"{metric.replace('_', ' ').title():25} {best_algo[0]:15} {value:.2f} ms")
            else:
                best_algo = max(results.items(), key=lambda x: x[1].get(metric, 0))
                value = best_algo[1].get(metric, 0)
                if 'utilization' in metric:
                    print(f"{metric.replace('_', ' ').title():25} {best_algo[0]:15} {value:.2f}%")
                else:
                    print(f"{metric.replace('_', ' ').title():25} {best_algo[0]:15} {value:.3f}")

if __name__ == "__main__":
    run_baseline_experiment()