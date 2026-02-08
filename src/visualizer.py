import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import os

class Visualizer:
    """Creates visualizations for simulation results"""
    
    def __init__(self, output_dir: str = "data/results/graphs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def create_gantt_chart(self, gantt_data: List[Tuple[int, int, int]], 
                          title: str = "Gantt Chart", 
                          filename: str = None):
        """Create Gantt chart for first N processes"""
        if not gantt_data:
            print("No Gantt data available")
            return
        
        fig, ax = plt.subplots(figsize=(15, 6))
        
        # Create color map for processes
        unique_pids = list(set([pid for _, _, pid in gantt_data]))
        cmap = plt.cm.get_cmap('tab20', len(unique_pids))
        color_map = {pid: cmap(i) for i, pid in enumerate(unique_pids)}
        
        # Plot each process execution
        y_ticks = []
        y_labels = []
        
        for i, (start, end, pid) in enumerate(gantt_data[:20]):  # First 20 processes
            duration = end - start
            ax.broken_barh([(start, duration)], (i, 0.8), 
                          facecolors=color_map[pid])
            
            # Add process label in the middle of the bar
            mid_x = start + duration / 2
            ax.text(mid_x, i + 0.4, f'P{pid}', 
                   ha='center', va='center', color='white', fontweight='bold')
        
        # Set up axes
        ax.set_yticks([i + 0.4 for i in range(min(20, len(gantt_data)))])
        ax.set_yticklabels([f'P{gantt_data[i][2]}' for i in range(min(20, len(gantt_data)))])
        ax.set_xlabel('Time (ms)')
        ax.set_title(f'{title} - First 20 Processes')
        ax.grid(True, axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        if filename:
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def create_metrics_comparison(self, results: Dict[str, Dict[str, float]], 
                                 metrics: List[str] = None,
                                 title: str = "Algorithm Comparison"):
        """Create bar chart comparing metrics across algorithms"""
        if metrics is None:
            metrics = ['avg_turnaround_time', 'avg_waiting_time', 'avg_response_time']
        
        algorithms = list(results.keys())
        
        # Prepare data
        data = {metric: [results[algo].get(metric, 0) for algo in algorithms] 
                for metric in metrics}
        
        # Create subplots
        fig, axes = plt.subplots(1, len(metrics), figsize=(15, 5))
        if len(metrics) == 1:
            axes = [axes]
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            x = np.arange(len(algorithms))
            bars = ax.bar(x, data[metric], color=plt.cm.Set3(np.arange(len(algorithms))))
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel('Algorithm')
            ax.set_ylabel('Time (ms)')
            ax.set_title(f'{metric.replace("_", " ").title()}')
            ax.set_xticks(x)
            ax.set_xticklabels(algorithms, rotation=45, ha='right')
            ax.grid(True, axis='y', alpha=0.3)
        
        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'metrics_comparison.png'), dpi=300)
        plt.show()
    
    def create_box_plots(self, all_process_stats: Dict[str, List[Dict[str, Any]]],
                        metric: str = 'waiting_time',
                        title: str = "Waiting Time Distribution"):
        """Create box plots showing distribution of metrics"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        data_to_plot = []
        labels = []
        
        for algo, stats in all_process_stats.items():
            if stats:
                values = [p[metric] for p in stats if metric in p]
                if values:
                    data_to_plot.append(values)
                    labels.append(algo)
        
        # Create box plot
        bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
        
        # Add colors
        colors = plt.cm.Set3(np.arange(len(data_to_plot)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_ylabel(f'{metric.replace("_", " ").title()} (ms)')
        ax.set_title(title)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'{metric}_boxplot.png'), dpi=300)
        plt.show()
    
    def create_line_plots(self, sensitivity_results: Dict[str, Dict[str, List[float]]],
                         param_name: str = "Time Quantum",
                         title: str = "Sensitivity Analysis"):
        """Create line plots for sensitivity analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        metrics = ['avg_turnaround_time', 'avg_waiting_time', 
                  'avg_response_time', 'cpu_utilization']
        metric_titles = ['Average Turnaround Time', 'Average Waiting Time',
                        'Average Response Time', 'CPU Utilization (%)']
        
        for idx, (metric, metric_title) in enumerate(zip(metrics, metric_titles)):
            ax = axes[idx]
            
            for algo, data in sensitivity_results.items():
                if metric in data:
                    x_values = list(data.keys())
                    y_values = data[metric]
                    
                    ax.plot(x_values, y_values, 'o-', linewidth=2, markersize=8, label=algo)
            
            ax.set_xlabel(param_name)
            ax.set_ylabel(metric_title)
            ax.set_title(metric_title)
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'sensitivity_analysis.png'), dpi=300)
        plt.show()
    
    def create_summary_table(self, results: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """Create a summary DataFrame of all metrics"""
        df = pd.DataFrame.from_dict(results, orient='index')
        
        # Select key metrics for display
        key_metrics = ['avg_turnaround_time', 'avg_waiting_time', 
                      'avg_response_time', 'cpu_utilization', 
                      'throughput', 'fairness_index']
        
        # Filter to available metrics
        available_metrics = [m for m in key_metrics if m in df.columns]
        df_display = df[available_metrics].round(2)
        
        # Rename columns for display
        display_names = {
            'avg_turnaround_time': 'Avg Turnaround',
            'avg_waiting_time': 'Avg Waiting',
            'avg_response_time': 'Avg Response',
            'cpu_utilization': 'CPU Util (%)',
            'throughput': 'Throughput',
            'fairness_index': 'Fairness Index'
        }
        
        df_display = df_display.rename(columns=display_names)
        
        # Highlight best values (lower is better for times, higher for others)
        def highlight_best(row):
            # For turnaround, waiting, response: lower is better
            # For CPU utilization, throughput, fairness: higher is better
            
            styles = []
            for col in df_display.columns:
                value = row[col]
                if 'Turnaround' in col or 'Waiting' in col or 'Response' in col:
                    # Lower is better
                    is_best = value == df_display[col].min()
                else:
                    # Higher is better
                    is_best = value == df_display[col].max()
                
                if is_best:
                    styles.append('background-color: lightgreen')
                else:
                    styles.append('')
            return styles
        
        styled_df = df_display.style.apply(highlight_best, axis=1)
        
        # Save to CSV and Excel
        df_display.to_csv(os.path.join(self.output_dir, 'summary_results.csv'))
        df_display.to_excel(os.path.join(self.output_dir, 'summary_results.xlsx'))
        
        return styled_df