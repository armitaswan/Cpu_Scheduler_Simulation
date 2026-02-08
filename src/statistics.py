from typing import List, Dict, Any
from .pcb import PCB
import numpy as np

class StatisticsCollector:
    """Collects and calculates performance metrics"""
    
    def __init__(self):
        self.context_switches = 0
        self.preemptions = 0
        self.completed_processes = 0
        self.total_turnaround_time = 0
        self.total_waiting_time = 0
        self.total_response_time = 0
    
    def record_process_completion(self, process: PCB):
        """Record statistics for a completed process"""
        self.completed_processes += 1
        self.total_turnaround_time += process.turnaround_time or 0
        self.total_waiting_time += process.waiting_time or 0
        self.total_response_time += process.response_time or 0
    
    def calculate_metrics(self, processes: List[PCB] = None) -> Dict[str, float]:
        """Calculate all performance metrics"""
        if processes:
            # Recalculate from provided processes
            self._recalculate_from_processes(processes)
        
        metrics = {}
        
        if self.completed_processes > 0:
            metrics["avg_turnaround_time"] = self.total_turnaround_time / self.completed_processes
            metrics["avg_waiting_time"] = self.total_waiting_time / self.completed_processes
            metrics["avg_response_time"] = self.total_response_time / self.completed_processes
        else:
            metrics["avg_turnaround_time"] = 0
            metrics["avg_waiting_time"] = 0
            metrics["avg_response_time"] = 0
        
        metrics["total_processes"] = self.completed_processes
        metrics["context_switches"] = self.context_switches
        metrics["preemptions"] = self.preemptions
        
        # Calculate percentiles if processes provided
        if processes:
            turnaround_times = [p.turnaround_time or 0 for p in processes]
            waiting_times = [p.waiting_time or 0 for p in processes]
            response_times = [p.response_time or 0 for p in processes]
            
            if turnaround_times:
                metrics["std_turnaround"] = np.std(turnaround_times)
                metrics["min_turnaround"] = min(turnaround_times)
                metrics["max_turnaround"] = max(turnaround_times)
                metrics["median_turnaround"] = np.median(turnaround_times)
            
            if waiting_times:
                metrics["std_waiting"] = np.std(waiting_times)
                metrics["min_waiting"] = min(waiting_times)
                metrics["max_waiting"] = max(waiting_times)
            
            if response_times:
                metrics["std_response"] = np.std(response_times)
        
        return metrics
    
    def _recalculate_from_processes(self, processes: List[PCB]):
        """Recalculate totals from list of processes"""
        self.completed_processes = len(processes)
        self.total_turnaround_time = sum(p.turnaround_time or 0 for p in processes)
        self.total_waiting_time = sum(p.waiting_time or 0 for p in processes)
        self.total_response_time = sum(p.response_time or 0 for p in processes)
    
    def reset(self):
        """Reset all statistics"""
        self.context_switches = 0
        self.preemptions = 0
        self.completed_processes = 0
        self.total_turnaround_time = 0
        self.total_waiting_time = 0
        self.total_response_time = 0