#!/usr/bin/env python3
"""
Scalability test experiment
"""

import sys
import os
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import SimulationController
from src.visualizer import Visualizer
from src.workload_generator import WorkloadGenerator, WorkloadConfig

def run_scalability_experiment():
    """Run scalability experiment"""
    controller = SimulationController()
    visualizer = Visualizer()
    
    print("\n" + "="*80)
    print("EXPERIMENT 4: SCALABILITY TEST")
    print("="*80)
    print("Objective: Analyze algorithm performance with increasing system load")
    print("Process Counts: 100, 250, 500, 750, 1000")
    print("Algorithms: FCFS, SJF, RR (q=20), Priority (preemptive)")
    print("="*80)
    
    process_counts = [100, 250, 500, 750, 1000]
    algorithms = ['FCFS', 'SJF', 'RR', 'PRIORITY']
    
    # Store results
    results = {algo: {} for algo in algorithms}
    execution_times = {algo: [] for algo in algorithms}
    
    for count in process_counts:
        print(f"\n{'='*60}")
        print(f"TESTING WITH {count} PROCESSES")
        print('='*60)
        
        # Generate workload once for fair comparison
        workload_config = WorkloadConfig(
            num_processes=count,
            workload_type="mixed"
        )
        generator = WorkloadGenerator(workload_config)
        workload = generator.generate_synthetic_workload()
        
        for algo in algorithms:
            print(f"  Running {algo}...", end=' ', flush=True)
            start_time = time.time()
            
            # Create scheduler
            if algo == 'RR':
                scheduler = controller.create_scheduler(algo, time_quantum=20)
            else:
                scheduler = controller.create_scheduler(algo)
            
            # Create simulator
            from src.simulator import CPUSimulator
            simulator = CPUSimulator(scheduler, context_switch_time=2)
            
            # Use the same workload
            simulator.processes = {p.process_id: p for p in workload}
            for process in workload:
                # Reset process state
                process.remaining_cpu_time = process.total_cpu_time
                process.state = PCB.NEW
                process.start_time = None
                process.completion_time = None
                process.first_run_time = None
                process.total_waiting_time = 0
                process.total_io_time = 0
                process.preempted = False
                process.context_switches = 0
                process.turnaround_time = None
                process.waiting_time = None
                process.response_time = None
            
            simulator.initialize_simulation(workload.copy())
            
            # Adjust max time based on process count
            max_time = min(500000, count * 1000)
            result = simulator.run(max_time=max_time)
            
            exec_time = time.time() - start_time
            execution_times[algo].append(exec_time)
            
            # Store key metrics
            metrics = result.metrics
            if algo not in results:
                results[algo] = {}
            
            results[algo][count] = {
                'avg_turnaround': metrics.get('avg_turnaround_time', 0),
                'avg_waiting': metrics.get('avg_waiting_time', 0),
                'avg_response': metrics.get('avg_response_time', 0),
                'cpu_utilization': metrics.get('cpu_utilization', 0),
                'throughput': metrics.get('throughput', 0),
                'fairness': metrics.get('fairness_index', 0),
                'execution_time': exec_time
            }
            
            print(f"✓ ({exec_time:.1f}s)")
    
    # Create scalability plots
    create_scalability_plots(results, process_counts, execution_times)
    
    # Print summary table
    print_summary_table(results, process_counts)
    
    print("\n" + "="*80)
    print("EXPERIMENT 4 COMPLETE")
    print("="*80)
    
    return results

def create_scalability_plots(results, process_counts, execution_times):
    """Create scalability visualization plots"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    # Plot 1: Average Turnaround Time
    ax = axes[0]
    for algo in results.keys():
        turnaround_times = [results[algo][count]['avg_turnaround'] for count in process_counts]
        ax.plot(process_counts, turnaround_times, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Average Turnaround Time (ms)')
    ax.set_title('Scalability: Turnaround Time')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Plot 2: Average Waiting Time
    ax = axes[1]
    for algo in results.keys():
        waiting_times = [results[algo][count]['avg_waiting'] for count in process_counts]
        ax.plot(process_counts, waiting_times, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Average Waiting Time (ms)')
    ax.set_title('Scalability: Waiting Time')
    ax.grid(True, alpha=0.3)
    
    # Plot 3: CPU Utilization
    ax = axes[2]
    for algo in results.keys():
        cpu_utils = [results[algo][count]['cpu_utilization'] for count in process_counts]
        ax.plot(process_counts, cpu_utils, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('CPU Utilization (%)')
    ax.set_title('Scalability: CPU Utilization')
    ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Throughput
    ax = axes[3]
    for algo in results.keys():
        throughputs = [results[algo][count]['throughput'] for count in process_counts]
        ax.plot(process_counts, throughputs, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Throughput (processes/sec)')
    ax.set_title('Scalability: Throughput')
    ax.grid(True, alpha=0.3)
    
    # Plot 5: Fairness Index
    ax = axes[4]
    for algo in results.keys():
        fairness = [results[algo][count]['fairness'] for count in process_counts]
        ax.plot(process_counts, fairness, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Fairness Index')
    ax.set_title('Scalability: Fairness')
    ax.set_ylim([0, 1.1])
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Execution Time (Simulation Performance)
    ax = axes[5]
    for algo in results.keys():
        if algo in execution_times:
            ax.plot(process_counts, execution_times[algo], 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Execution Time (seconds)')
    ax.set_title('Simulation Performance')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.suptitle('Scalability Analysis: Algorithm Performance with Increasing Load', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/results/graphs/scalability_analysis.png', dpi=300)
    plt.show()
    
    # Create overhead analysis plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate overhead (waiting time / turnaround time)
    for algo in results.keys():
        overheads = []
        for count in process_counts:
            turnaround = results[algo][count]['avg_turnaround']
            waiting = results[algo][count]['avg_waiting']
            if turnaround > 0:
                overhead = (waiting / turnaround) * 100
                overheads.append(overhead)
            else:
                overheads.append(0)
        
        ax.plot(process_counts, overheads, 'o-', linewidth=2, markersize=6, label=algo)
    
    ax.set_xlabel('Number of Processes')
    ax.set_ylabel('Scheduling Overhead (%)')
    ax.set_title('Scheduling Overhead: Waiting Time as Percentage of Turnaround Time')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('data/results/graphs/scheduling_overhead.png', dpi=300)
    plt.show()

def print_summary_table(results, process_counts):
    """Print scalability summary table"""
    print("\n" + "="*80)
    print("SCALABILITY SUMMARY")
    print("="*80)
    
    # Create summary DataFrame
    summary_data = []
    
    for algo in results.keys():
        row = {'Algorithm': algo}
        
        # Calculate growth rates
        turnaround_growth = []
        waiting_growth = []
        
        for i in range(1, len(process_counts)):
            prev = results[algo][process_counts[i-1]]['avg_turnaround']
            curr = results[algo][process_counts[i]]['avg_turnaround']
            if prev > 0:
                growth = ((curr - prev) / prev) * 100
                turnaround_growth.append(growth)
            
            prev_w = results[algo][process_counts[i-1]]['avg_waiting']
            curr_w = results[algo][process_counts[i]]['avg_waiting']
            if prev_w > 0:
                growth_w = ((curr_w - prev_w) / prev_w) * 100
                waiting_growth.append(growth_w)
        
        # Add average growth rates
        if turnaround_growth:
            row['Avg Turnaround Growth %'] = np.mean(turnaround_growth)
        if waiting_growth:
            row['Avg Waiting Growth %'] = np.mean(waiting_growth)
        
        # Add final values for largest process count
        last_count = process_counts[-1]
        row[f'Turnaround @ {last_count}'] = results[algo][last_count]['avg_turnaround']
        row[f'Waiting @ {last_count}'] = results[algo][last_count]['avg_waiting']
        row[f'CPU Util @ {last_count}'] = results[algo][last_count]['cpu_utilization']
        row[f'Fairness @ {last_count}'] = results[algo][last_count]['fairness']
        
        summary_data.append(row)
    
    # Create and display DataFrame
    df = pd.DataFrame(summary_data)
    
    # Format numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if 'Growth' in col or 'Fairness' in col:
            df[col] = df[col].map(lambda x: f'{x:.2f}')
        elif 'Util' in col:
            df[col] = df[col].map(lambda x: f'{x:.1f}%')
        else:
            df[col] = df[col].map(lambda x: f'{x:.0f}')
    
    print(df.to_string(index=False))
    
    # Print scalability conclusions
    print("\n" + "="*80)
    print("SCALABILITY CONCLUSIONS")
    print("="*80)
    
    # Find best scalable algorithm for each metric
    metrics_to_check = [
        ('Avg Turnaround Growth %', 'lower', 'turnaround time growth'),
        ('Avg Waiting Growth %', 'lower', 'waiting time growth'),
        (f'CPU Util @ {process_counts[-1]}', 'higher', 'CPU utilization'),
        (f'Fairness @ {process_counts[-1]}', 'higher', 'fairness')
    ]
    
    for col, direction, description in metrics_to_check:
        if col in df.columns:
            if direction == 'lower':
                best_idx = df[col].str.replace('%', '').astype(float).idxmin()
            else:
                best_idx = df[col].str.replace('%', '').astype(float).idxmax()
            
            best_algo = df.loc[best_idx, 'Algorithm']
            best_value = df.loc[best_idx, col]
            
            print(f"Best for {description:30} {best_algo:10} ({best_value})")

if __name__ == "__main__":
    from src.pcb import PCB
    results = run_scalability_experiment()