#!/usr/bin/env python3
"""
Sensitivity analysis experiment
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import SimulationController
from src.visualizer import Visualizer

def run_sensitivity_experiment():
    """Run sensitivity analysis experiment"""
    controller = SimulationController()
    visualizer = Visualizer()
    
    print("\n" + "="*80)
    print("EXPERIMENT 2: SENSITIVITY ANALYSIS")
    print("="*80)
    print("Objective: Analyze sensitivity of algorithms to parameter changes")
    print("Part 1: Round Robin with different time quanta")
    print("Part 2: Varying number of processes")
    print("="*80)
    
    # Part 1: RR with different time quanta
    print("\nPART 1: ROUND ROBIN TIME QUANTUM SENSITIVITY")
    print("-"*60)
    
    time_quanta = [5, 10, 20, 50, 100]
    algorithms = ['FCFS', 'SJF', 'RR']  # Compare RR with others
    
    all_results = {}
    
    for algo in algorithms:
        print(f"\nTesting {algo}...")
        
        if algo == 'RR':
            # Test RR with different quanta
            rr_results = {}
            for quantum in time_quanta:
                print(f"  Quantum = {quantum}ms")
                
                # Create scheduler
                from src.schedulers.round_robin import RoundRobinScheduler
                scheduler = RoundRobinScheduler(time_quantum=quantum)
                
                # Generate workload
                from src.workload_generator import WorkloadGenerator, WorkloadConfig
                workload_config = WorkloadConfig(num_processes=300, workload_type='mixed')
                generator = WorkloadGenerator(workload_config)
                processes = generator.generate_synthetic_workload()
                
                # Run simulation
                from src.simulator import CPUSimulator
                simulator = CPUSimulator(scheduler, context_switch_time=2)
                simulator.initialize_simulation(processes)
                result = simulator.run(max_time=100000)
                
                rr_results[quantum] = result.metrics
            
            # Convert to format for plotting
            metrics_to_plot = ['avg_turnaround_time', 'avg_waiting_time', 
                             'avg_response_time', 'cpu_utilization']
            for metric in metrics_to_plot:
                if metric in rr_results[time_quanta[0]]:
                    all_results[f'RR_{metric}'] = {
                        quantum: rr_results[quantum][metric] for quantum in time_quanta
                    }
        
        else:
            # Run baseline for comparison
            from src.schedulers.fcfs import FCFSScheduler
            from src.schedulers.sjf import SJFScheduler
            
            if algo == 'FCFS':
                scheduler = FCFSScheduler()
            elif algo == 'SJF':
                scheduler = SJFScheduler()
            
            # Generate workload
            from src.workload_generator import WorkloadGenerator, WorkloadConfig
            workload_config = WorkloadConfig(num_processes=300, workload_type='mixed')
            generator = WorkloadGenerator(workload_config)
            processes = generator.generate_synthetic_workload()
            
            # Run simulation
            from src.simulator import CPUSimulator
            simulator = CPUSimulator(scheduler, context_switch_time=2)
            simulator.initialize_simulation(processes)
            result = simulator.run(max_time=100000)
            
            # Store constant values for each quantum
            for metric in ['avg_turnaround_time', 'avg_waiting_time', 
                          'avg_response_time', 'cpu_utilization']:
                if metric in result.metrics:
                    all_results[f'{algo}_{metric}'] = {
                        quantum: result.metrics[metric] for quantum in time_quanta
                    }
    
    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    metrics = ['avg_turnaround_time', 'avg_waiting_time', 
              'avg_response_time', 'cpu_utilization']
    titles = ['Turnaround Time', 'Waiting Time', 'Response Time', 'CPU Utilization']
    
    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx]
        
        # Plot RR results
        rr_key = f'RR_{metric}'
        if rr_key in all_results:
            quanta = list(all_results[rr_key].keys())
            values = list(all_results[rr_key].values())
            ax.plot(quanta, values, 'o-', linewidth=2, markersize=8, 
                   label='Round Robin', color='red')
        
        # Plot FCFS baseline (horizontal line)
        fcfs_key = f'FCFS_{metric}'
        if fcfs_key in all_results:
            fcfs_value = list(all_results[fcfs_key].values())[0]
            ax.axhline(y=fcfs_value, color='blue', linestyle='--', 
                      linewidth=2, label='FCFS')
        
        # Plot SJF baseline (horizontal line)
        sjf_key = f'SJF_{metric}'
        if sjf_key in all_results:
            sjf_value = list(all_results[sjf_key].values())[0]
            ax.axhline(y=sjf_value, color='green', linestyle='-.', 
                      linewidth=2, label='SJF')
        
        ax.set_xlabel('Time Quantum (ms)')
        ax.set_ylabel(title + ' (ms)' if 'utilization' not in metric else 'CPU Utilization (%)')
        ax.set_title(f'Impact of Time Quantum on {title}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        if metric == 'cpu_utilization':
            ax.set_ylim([0, 100])
    
    plt.suptitle('Sensitivity Analysis: Round Robin vs Time Quantum', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/results/graphs/rr_sensitivity.png', dpi=300)
    plt.show()
    
    # Part 2: Scalability test
    print("\n\nPART 2: SCALABILITY WITH INCREASING PROCESS COUNT")
    print("-"*60)
    
    process_counts = [100, 300, 500, 1000]
    algorithms = ['FCFS', 'SJF', 'RR']
    
    scalability_results = {algo: {metric: [] for metric in metrics} for algo in algorithms}
    
    for count in process_counts:
        print(f"\nTesting with {count} processes...")
        
        for algo in algorithms:
            print(f"  {algo}...", end=' ', flush=True)
            
            # Create scheduler
            if algo == 'FCFS':
                from src.schedulers.fcfs import FCFSScheduler
                scheduler = FCFSScheduler()
            elif algo == 'SJF':
                from src.schedulers.sjf import SJFScheduler
                scheduler = SJFScheduler()
            elif algo == 'RR':
                from src.schedulers.round_robin import RoundRobinScheduler
                scheduler = RoundRobinScheduler(time_quantum=20)
            
            # Generate workload
            from src.workload_generator import WorkloadGenerator, WorkloadConfig
            workload_config = WorkloadConfig(num_processes=count, workload_type='mixed')
            generator = WorkloadGenerator(workload_config)
            processes = generator.generate_synthetic_workload()
            
            # Run simulation
            from src.simulator import CPUSimulator
            simulator = CPUSimulator(scheduler, context_switch_time=2)
            simulator.initialize_simulation(processes)
            result = simulator.run(max_time=200000)
            
            # Store results
            for metric in metrics:
                if metric in result.metrics:
                    scalability_results[algo][metric].append(result.metrics[metric])
            
            print("✓")
    
    # Plot scalability results
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx]
        
        for algo in algorithms:
            if scalability_results[algo][metric]:
                ax.plot(process_counts, scalability_results[algo][metric], 
                       'o-', linewidth=2, markersize=8, label=algo)
        
        ax.set_xlabel('Number of Processes')
        ax.set_ylabel(title + ' (ms)' if 'utilization' not in metric else 'CPU Utilization (%)')
        ax.set_title(f'Scalability: {title} vs Process Count')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        if metric == 'cpu_utilization':
            ax.set_ylim([0, 100])
    
    plt.suptitle('Scalability Analysis: Performance with Increasing Load', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/results/graphs/scalability_analysis.png', dpi=300)
    plt.show()
    
    print("\n" + "="*80)
    print("EXPERIMENT 2 COMPLETE")
    print("="*80)

if __name__ == "__main__":
    run_sensitivity_experiment()