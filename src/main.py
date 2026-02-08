#!/usr/bin/env python3
"""
Main controller for CPU Scheduler Simulation Project
"""

import sys
import os
import yaml
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pcb import PCB
from src.simulator import CPUSimulator, SimulationResult
from src.workload_generator import WorkloadGenerator, WorkloadConfig
from src.visualizer import Visualizer
from src.statistics import StatisticsCollector

# Import all schedulers
from src.schedulers.fcfs import FCFSScheduler
from src.schedulers.sjf import SJFScheduler
from src.schedulers.srtf import SRTFScheduler
from src.schedulers.round_robin import RoundRobinScheduler
from src.schedulers.priority import PriorityScheduler
from src.schedulers.mlfq import MLFQScheduler

@dataclass
class SimulationConfig:
    """Configuration for a simulation run"""
    algorithm: str
    time_quantum: Optional[int] = None
    preemptive: bool = True
    num_processes: int = 100
    workload_type: str = "mixed"
    max_time: int = 100000
    context_switch: int = 2

class SimulationController:
    """Main controller for running simulations"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.workload_generator = WorkloadGenerator()
        self.visualizer = Visualizer()
        self.results = {}
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            'simulation': {
                'max_processes': 1000,
                'context_switch_time': 2,
                'log_level': 'INFO'
            },
            'workload': {
                'generation_method': 'synthetic',
                'num_processes': 500,
                'workload_type': 'mixed'
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                return {**default_config, **config}
        
        return default_config
    
    def create_scheduler(self, algorithm: str, **kwargs) -> Any:
        """Factory method to create scheduler instances"""
        schedulers = {
            'FCFS': lambda: FCFSScheduler(),
            'SJF': lambda: SJFScheduler(),
            'SRTF': lambda: SRTFScheduler(),
            'RR': lambda: RoundRobinScheduler(
                time_quantum=kwargs.get('time_quantum', 20)
            ),
            'PRIORITY': lambda: PriorityScheduler(
                preemptive=kwargs.get('preemptive', True),
                aging_interval=kwargs.get('aging_interval', 1000)
            ),
            'PRIORITY_NP': lambda: PriorityScheduler(
                preemptive=False,
                aging_interval=kwargs.get('aging_interval', 1000)
            ),
            'MLFQ': lambda: MLFQScheduler(
                num_queues=kwargs.get('num_queues', 3),
                time_quanta=kwargs.get('time_quanta', [10, 20, 40])
            )
        }
        
        if algorithm in schedulers:
            return schedulers[algorithm]()
        else:
            raise ValueError(f"Unknown scheduler: {algorithm}")
    
    def generate_workload(self, config: SimulationConfig) -> List[PCB]:
        """Generate workload based on configuration"""
        workload_config = WorkloadConfig(
            num_processes=config.num_processes,
            workload_type=config.workload_type
        )
        
        self.workload_generator.config = workload_config
        return self.workload_generator.generate_synthetic_workload()
    
    def run_simulation(self, sim_config: SimulationConfig) -> SimulationResult:
        """Run a single simulation with given configuration"""
        print(f"\n{'='*60}")
        print(f"Running {sim_config.algorithm} simulation")
        print(f"Processes: {sim_config.num_processes}, Type: {sim_config.workload_type}")
        print(f"{'='*60}")
        
        # Create scheduler
        scheduler_kwargs = {}
        if sim_config.algorithm == 'RR':
            scheduler_kwargs['time_quantum'] = sim_config.time_quantum or 20
        
        scheduler = self.create_scheduler(sim_config.algorithm, **scheduler_kwargs)
        
        # Generate workload
        processes = self.generate_workload(sim_config)
        
        # Create and run simulator
        simulator = CPUSimulator(
            scheduler=scheduler,
            context_switch_time=sim_config.context_switch
        )
        
        simulator.initialize_simulation(processes)
        result = simulator.run(max_time=sim_config.max_time)
        
        # Store results
        self.results[sim_config.algorithm] = result
        
        # Print summary
        self._print_simulation_summary(result)
        
        return result
    
    def _print_simulation_summary(self, result: SimulationResult):
        """Print summary of simulation results"""
        print(f"\n{'='*60}")
        print(f"SIMULATION RESULTS: {result.algorithm_name}")
        print(f"{'='*60}")
        
        metrics = result.metrics
        
        print(f"Completed Processes: {metrics.get('total_processes', 0)}")
        print(f"Average Turnaround Time: {metrics.get('avg_turnaround_time', 0):.2f} ms")
        print(f"Average Waiting Time: {metrics.get('avg_waiting_time', 0):.2f} ms")
        print(f"Average Response Time: {metrics.get('avg_response_time', 0):.2f} ms")
        print(f"CPU Utilization: {metrics.get('cpu_utilization', 0):.2f}%")
        print(f"Throughput: {metrics.get('throughput', 0):.2f} processes/sec")
        print(f"Fairness Index: {metrics.get('fairness_index', 0):.3f}")
        print(f"Context Switches: {metrics.get('context_switches', 0)}")
        print(f"Preemptions: {metrics.get('preemptions', 0)}")
        
        if 'std_turnaround' in metrics:
            print(f"Turnaround Time STD: {metrics['std_turnaround']:.2f} ms")
        
        print(f"{'='*60}")
    
    def run_baseline_comparison(self):
        """Run baseline comparison of all algorithms"""
        print("\n" + "="*70)
        print("BASELINE COMPARISON: All Algorithms with Identical Workload")
        print("="*70)
        
        # Configuration for baseline
        baseline_config = SimulationConfig(
            algorithm="FCFS",  # Will be overridden
            num_processes=500,
            workload_type="mixed",
            max_time=200000
        )
        
        # Algorithms to test
        algorithms = ['FCFS', 'SJF', 'SRTF', 'RR', 'PRIORITY', 'PRIORITY_NP']
        
        # Generate workload once for fair comparison
        workload = self.generate_workload(baseline_config)
        
        results = {}
        all_process_stats = {}
        
        for algo in algorithms:
            print(f"\nRunning {algo}...")
            
            # Create scheduler
            scheduler_kwargs = {}
            if algo == 'RR':
                scheduler_kwargs['time_quantum'] = 20
            
            scheduler = self.create_scheduler(algo, **scheduler_kwargs)
            
            # Create and run simulator
            simulator = CPUSimulator(
                scheduler=scheduler,
                context_switch_time=baseline_config.context_switch
            )
            
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
            result = simulator.run(max_time=baseline_config.max_time)
            
            results[algo] = result.metrics
            all_process_stats[algo] = result.process_stats
            
            # Store for visualization
            self.results[algo] = result
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        # Metrics comparison bar chart
        self.visualizer.create_metrics_comparison(
            results,
            title="Baseline Comparison: All Scheduling Algorithms"
        )
        
        # Box plots for waiting time distribution
        self.visualizer.create_box_plots(
            all_process_stats,
            metric='waiting_time',
            title="Waiting Time Distribution Across Algorithms"
        )
        
        # Create summary table
        styled_df = self.visualizer.create_summary_table(results)
        print("\nSummary Results Table:")
        print(styled_df.to_string())
        
        # Create Gantt charts for first 2 algorithms
        for i, algo in enumerate(['FCFS', 'RR'][:2]):
            if algo in self.results:
                self.visualizer.create_gantt_chart(
                    self.results[algo].gantt_chart[:20],
                    title=f"Gantt Chart - {algo}",
                    filename=f"gantt_{algo.lower()}.png"
                )
        
        return results
    
    def run_sensitivity_analysis(self):
        """Run sensitivity analysis for Round Robin"""
        print("\n" + "="*70)
        print("SENSITIVITY ANALYSIS: Round Robin with Different Time Quanta")
        print("="*70)
        
        # Different time quantum values
        time_quanta = [5, 10, 20, 50, 100]
        results = {}
        
        for quantum in time_quanta:
            print(f"\nRunning RR with quantum = {quantum}ms")
            
            config = SimulationConfig(
                algorithm="RR",
                time_quantum=quantum,
                num_processes=300,
                workload_type="mixed"
            )
            
            scheduler = self.create_scheduler("RR", time_quantum=quantum)
            processes = self.generate_workload(config)
            
            simulator = CPUSimulator(
                scheduler=scheduler,
                context_switch_time=config.context_switch
            )
            
            simulator.initialize_simulation(processes)
            result = simulator.run(max_time=config.max_time)
            
            algo_name = f"RR(q={quantum})"
            results[algo_name] = result.metrics
        
        # Plot sensitivity analysis
        self.visualizer.create_line_plots(
            {algo: {metric: [results[algo][metric]] for metric in results[algo]} 
             for algo in results},
            param_name="Time Quantum (ms)",
            title="Round Robin Sensitivity to Time Quantum"
        )
        
        return results
    
    def run_workload_specific_tests(self):
        """Test algorithms with different workload types"""
        print("\n" + "="*70)
        print("WORKLOAD-SPECIFIC PERFORMANCE ANALYSIS")
        print("="*70)
        
        workload_types = ['cpu_intensive', 'io_intensive', 'mixed']
        algorithms = ['FCFS', 'SJF', 'RR', 'PRIORITY']
        
        all_results = {}
        
        for workload_type in workload_types:
            print(f"\n{'='*40}")
            print(f"Testing with {workload_type.upper()} workload")
            print('='*40)
            
            workload_results = {}
            
            for algo in algorithms:
                print(f"  Running {algo}...")
                
                config = SimulationConfig(
                    algorithm=algo,
                    num_processes=200,
                    workload_type=workload_type
                )
                
                if algo == 'RR':
                    scheduler = self.create_scheduler(algo, time_quantum=20)
                else:
                    scheduler = self.create_scheduler(algo)
                
                processes = self.generate_workload(config)
                
                simulator = CPUSimulator(
                    scheduler=scheduler,
                    context_switch_time=config.context_switch
                )
                
                simulator.initialize_simulation(processes)
                result = simulator.run(max_time=config.max_time)
                
                workload_results[algo] = result.metrics
            
            all_results[workload_type] = workload_results
        
        # Create comparison plots for each metric across workloads
        self._plot_workload_comparison(all_results)
        
        return all_results
    
    def _plot_workload_comparison(self, all_results: Dict[str, Dict[str, Dict]]):
        """Plot comparison across different workloads"""
        metrics = ['avg_turnaround_time', 'avg_waiting_time', 'cpu_utilization']
        workload_types = list(all_results.keys())
        algorithms = list(next(iter(all_results.values())).keys())
        
        fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 15))
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            
            # Prepare data for grouped bar chart
            x = np.arange(len(workload_types))
            width = 0.8 / len(algorithms)
            
            for i, algo in enumerate(algorithms):
                values = [all_results[wt][algo].get(metric, 0) for wt in workload_types]
                offset = (i - len(algorithms)/2) * width + width/2
                bars = ax.bar(x + offset, values, width, label=algo)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                           f'{value:.1f}', ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel('Workload Type')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f'{metric.replace("_", " ").title()} by Workload Type')
            ax.set_xticks(x)
            ax.set_xticklabels([wt.replace('_', ' ').title() for wt in workload_types])
            ax.legend()
            ax.grid(True, axis='y', alpha=0.3)
        
        plt.suptitle("Algorithm Performance Across Different Workloads", 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(self.visualizer.output_dir, 'workload_comparison.png'), 
                   dpi=300)
        plt.show()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CPU Scheduler Simulation')
    parser.add_argument('--config', type=str, default='config/simulation_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--experiment', type=str, default='baseline',
                       choices=['baseline', 'sensitivity', 'workload', 'scalability', 'all'],
                       help='Experiment to run')
    parser.add_argument('--processes', type=int, default=500,
                       help='Number of processes')
    parser.add_argument('--algorithm', type=str, default='FCFS',
                       help='Specific algorithm to test')
    parser.add_argument('--quantum', type=int, default=20,
                       help='Time quantum for RR')
    
    args = parser.parse_args()
    
    # Create controller
    controller = SimulationController(args.config)
    
    # Run selected experiment
    if args.experiment == 'baseline' or args.experiment == 'all':
        controller.run_baseline_comparison()
    
    if args.experiment == 'sensitivity' or args.experiment == 'all':
        controller.run_sensitivity_analysis()
    
    if args.experiment == 'workload' or args.experiment == 'all':
        controller.run_workload_specific_tests()
    
    if args.experiment == 'scalability':
        # You can implement scalability test similarly
        print("Scalability test - Implement as needed")
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print(f"Results saved to: {controller.visualizer.output_dir}")
    print("="*70)

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    main()