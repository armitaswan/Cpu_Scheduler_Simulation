#!/usr/bin/env python3
"""
Workload-specific performance experiment
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import SimulationController
from src.visualizer import Visualizer

def run_workload_experiment():
    """Run workload-specific performance experiment"""
    controller = SimulationController()
    
    print("\n" + "="*80)
    print("EXPERIMENT 3: WORKLOAD-SPECIFIC PERFORMANCE")
    print("="*80)
    print("Objective: Analyze algorithm performance with different workload types")
    print("Workload Types: CPU-intensive, I/O-intensive, Mixed")
    print("Algorithms: FCFS, SJF, RR (q=20), Priority (preemptive)")
    print("="*80)
    
    workload_types = ['cpu_intensive', 'io_intensive', 'mixed']
    algorithms = ['FCFS', 'SJF', 'RR', 'PRIORITY']
    
    all_results = {}
    
    for workload in workload_types:
        print(f"\n{'='*60}")
        print(f"WORKLOAD: {workload.upper().replace('_', ' ')}")
        print('='*60)
        
        workload_results = {}
        
        for algo in algorithms:
            print(f"\nTesting {algo}...")
            
            # Create scheduler
            if algo == 'RR':
                scheduler = controller.create_scheduler(algo, time_quantum=20)
            else:
                scheduler = controller.create_scheduler(algo)
            
            # Generate workload
            from src.workload_generator import WorkloadGenerator, WorkloadConfig
            workload_config = WorkloadConfig(
                num_processes=200,
                workload_type=workload
            )
            generator = WorkloadGenerator(workload_config)
            processes = generator.generate_synthetic_workload()
            
            # Run simulation
            from src.simulator import CPUSimulator
            simulator = CPUSimulator(scheduler, context_switch_time=2)
            simulator.initialize_simulation(processes)
            result = simulator.run(max_time=150000)
            
            workload_results[algo] = result.metrics
            
            # Print quick summary
            metrics = result.metrics
            print(f"  Turnaround: {metrics.get('avg_turnaround_time', 0):.1f} ms | "
                  f"Waiting: {metrics.get('avg_waiting_time', 0):.1f} ms | "
                  f"CPU Util: {metrics.get('cpu_utilization', 0):.1f}%")
        
        all_results[workload] = workload_results
    
    # Create comprehensive visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    metrics_to_plot = [
        'avg_turnaround_time',
        'avg_waiting_time', 
        'avg_response_time',
        'cpu_utilization',
        'throughput',
        'fairness_index'
    ]
    
    metric_names = [
        'Avg Turnaround Time (ms)',
        'Avg Waiting Time (ms)',
        'Avg Response Time (ms)',
        'CPU Utilization (%)',
        'Throughput (proc/sec)',
        'Fairness Index'
    ]
    
    colors = plt.cm.Set2(np.arange(len(algorithms)))
    
    for idx, (metric, metric_name) in enumerate(zip(metrics_to_plot, metric_names)):
        ax = axes[idx]
        
        x = np.arange(len(workload_types))
        width = 0.8 / len(algorithms)
        
        for i, algo in enumerate(algorithms):
            values = []
            for workload in workload_types:
                if algo in all_results[workload] and metric in all_results[workload][algo]:
                    values.append(all_results[workload][algo][metric])
                else:
                    values.append(0)
            
            offset = (i - len(algorithms)/2) * width + width/2
            bars = ax.bar(x + offset, values, width, label=algo, color=colors[i])
            
            # Add value labels
            for bar, value in zip(bars, values):
                height = bar.get_height()
                if metric == 'fairness_index':
                    label = f'{value:.3f}'
                elif 'utilization' in metric:
                    label = f'{value:.1f}%'
                elif 'throughput' in metric:
                    label = f'{value:.1f}'
                else:
                    label = f'{value:.0f}'
                
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       label, ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('Workload Type')
        ax.set_ylabel(metric_name)
        ax.set_title(metric_name.split(' (')[0])
        ax.set_xticks(x)
        ax.set_xticklabels([wt.replace('_', '\n').title() for wt in workload_types])
        
        if idx == 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        ax.grid(True, axis='y', alpha=0.3)
        
        # Set appropriate y-limits
        if 'utilization' in metric:
            ax.set_ylim([0, 100])
        elif 'fairness' in metric:
            ax.set_ylim([0, 1.1])
    
    plt.suptitle('Algorithm Performance Across Different Workload Types', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/results/graphs/workload_performance.png', dpi=300)
    plt.show()
    
    # Create summary table
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY BY WORKLOAD TYPE")
    print("="*80)
    
    for workload in workload_types:
        print(f"\n{workload.upper().replace('_', ' ')} WORKLOAD:")
        print("-"*60)
        
        # Create DataFrame for this workload
        data = {}
        for algo in algorithms:
            if algo in all_results[workload]:
                data[algo] = all_results[workload][algo]
        
        df = pd.DataFrame(data).T
        
        # Select and rename key metrics
        display_metrics = {
            'avg_turnaround_time': 'Turnaround (ms)',
            'avg_waiting_time': 'Waiting (ms)',
            'avg_response_time': 'Response (ms)',
            'cpu_utilization': 'CPU Util (%)',
            'throughput': 'Throughput',
            'fairness_index': 'Fairness'
        }
        
        available_metrics = [m for m in display_metrics.keys() if m in df.columns]
        df_display = df[available_metrics].copy()
        df_display = df_display.rename(columns=display_metrics)
        
        # Round values
        for col in df_display.columns:
            if 'Fairness' in col:
                df_display[col] = df_display[col].round(3)
            elif 'Util' in col or 'Throughput' in col:
                df_display[col] = df_display[col].round(1)
            else:
                df_display[col] = df_display[col].round(0)
        
        print(df_display.to_string())
    
    # Determine best algorithm for each workload type
    print("\n" + "="*80)
    print("BEST ALGORITHM RECOMMENDATIONS")
    print("="*80)
    
    for workload in workload_types:
        print(f"\nFor {workload.replace('_', ' ').title()} Workload:")
        print("-"*40)
        
        # Find best for each metric
        metrics_to_check = ['avg_turnaround_time', 'avg_waiting_time', 
                          'cpu_utilization', 'fairness_index']
        
        for metric in metrics_to_check:
            best_algo = None
            best_value = None
            
            for algo in algorithms:
                if (algo in all_results[workload] and 
                    metric in all_results[workload][algo]):
                    value = all_results[workload][algo][metric]
                    
                    if best_algo is None:
                        best_algo = algo
                        best_value = value
                    else:
                        if 'turnaround' in metric or 'waiting' in metric:
                            # Lower is better
                            if value < best_value:
                                best_algo = algo
                                best_value = value
                        else:
                            # Higher is better
                            if value > best_value:
                                best_algo = algo
                                best_value = value
            
            if best_algo:
                metric_name = metric.replace('avg_', '').replace('_', ' ').title()
                if 'utilization' in metric:
                    print(f"  {metric_name:20} {best_algo:10} ({best_value:.1f}%)")
                elif 'fairness' in metric:
                    print(f"  {metric_name:20} {best_algo:10} ({best_value:.3f})")
                else:
                    print(f"  {metric_name:20} {best_algo:10} ({best_value:.0f} ms)")
    
    print("\n" + "="*80)
    print("EXPERIMENT 3 COMPLETE")
    print("="*80)

if __name__ == "__main__":
    run_workload_experiment()