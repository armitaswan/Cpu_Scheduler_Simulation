import time
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass
from .pcb import PCB, ProcessState
from .event import Event, EventQueue, EventType
from .schedulers.base_scheduler import BaseScheduler
from .statistics import StatisticsCollector

@dataclass
class SimulationResult:
    """Container for simulation results"""
    algorithm_name: str
    metrics: Dict[str, float]
    process_stats: List[Dict[str, Any]]
    gantt_chart: List[Tuple[int, int, int]]  # (start, end, pid)
    cpu_utilization: float

class CPUSimulator:
    """Discrete-event CPU scheduler simulator"""
    
    def __init__(self, scheduler: BaseScheduler, context_switch_time: int = 2):
        self.scheduler = scheduler
        self.context_switch_time = context_switch_time
        self.event_queue = EventQueue()
        self.processes = {}  # pid -> PCB
        self.running_process = None
        self.current_time = 0
        self.idle_time = 0
        self.last_update_time = 0
        
        # Statistics
        self.stats_collector = StatisticsCollector()
        self.gantt_chart = []  # For visualization
        
        # State tracking
        self.is_context_switching = False
        self.context_switch_end_time = 0
        self.completed_processes = []
    
    def initialize_simulation(self, processes: List[PCB]):
        """Initialize simulation with processes"""
        self.processes = {p.process_id: p for p in processes}
        
        # Schedule all arrival events
        for process in processes:
            self.event_queue.schedule_arrival(process.process_id, process.arrival_time)
        
        # Sort processes by arrival time for statistics
        processes.sort(key=lambda p: p.arrival_time)
    
    def run(self, max_time: int = 100000) -> SimulationResult:
        """Run the simulation until completion or max_time"""
        print(f"\n=== Starting {self.scheduler.name} Simulation ===")
        
        while (self.current_time <= max_time and 
               not (self.event_queue.is_empty() and 
                    self.scheduler.is_empty() and 
                    self.running_process is None)):
            
            self._update_waiting_times()
            
            # Check for context switch completion
            if self.is_context_switching and self.current_time >= self.context_switch_end_time:
                self.is_context_switching = False
                self.stats_collector.context_switches += 1
            
            # Process all events at current time
            while not self.event_queue.is_empty() and self.event_queue.peek().timestamp <= self.current_time:
                event = self.event_queue.pop()
                self._handle_event(event)
            
            # If CPU is idle and not context switching, schedule a process
            if (not self.is_context_switching and 
                self.running_process is None and 
                not self.scheduler.is_empty()):
                self._schedule_next_process()
            
            # If still idle, increment idle time
            if self.running_process is None and not self.is_context_switching:
                self.idle_time += 1
            
            self.current_time += 1
        
        # Complete any running process
        if self.running_process:
            self._complete_current_process()
        
        # Calculate final statistics
        return self._collect_results()
    
    def _handle_event(self, event: Event):
        """Handle different types of events"""
        if event.type == EventType.PROCESS_ARRIVAL:
            self._handle_arrival(event)
        elif event.type == EventType.CPU_BURST_COMPLETE:
            self._handle_cpu_completion(event)
        elif event.type == EventType.IO_BURST_COMPLETE:
            self._handle_io_completion(event)
        elif event.type == EventType.TIME_QUANTUM_EXPIRED:
            self._handle_timeout(event)
    
    def _handle_arrival(self, event: Event):
        """Handle process arrival"""
        pid = event.process_id
        if pid in self.processes:
            process = self.processes[pid]
            process.state = ProcessState.READY
            self.scheduler.add_process(process)
            
            # Check for preemption
            if (self.running_process and 
                self.scheduler.should_preempt(self.running_process, process)):
                self._preempt_current_process(process)
    
    def _handle_cpu_completion(self, event: Event):
        """Handle CPU burst completion"""
        if self.running_process and self.running_process.process_id == event.process_id:
            process = self.running_process
            
            # Update Gantt chart
            if self.gantt_chart and self.gantt_chart[-1][2] == process.process_id:
                start, _, _ = self.gantt_chart[-1]
                self.gantt_chart[-1] = (start, self.current_time, process.process_id)
            
            # Check if process completed all CPU time
            if process.remaining_cpu_time == 0:
                self._complete_current_process()
            else:
                # Start I/O burst
                process.state = ProcessState.WAITING
                process.total_io_time += process.io_burst_time
                io_completion = self.current_time + process.io_burst_time
                self.event_queue.schedule_io_completion(process.process_id, io_completion)
                self.running_process = None
    
    def _handle_io_completion(self, event: Event):
        """Handle I/O completion"""
        pid = event.process_id
        if pid in self.processes:
            process = self.processes[pid]
            process.state = ProcessState.READY
            self.scheduler.add_process(process)
            
            # Check for preemption
            if (self.running_process and 
                self.scheduler.should_preempt(self.running_process, process)):
                self._preempt_current_process(process)
    
    def _handle_timeout(self, event: Event):
        """Handle time quantum expiration"""
        if self.running_process and self.running_process.process_id == event.process_id:
            process = self.running_process
            self.scheduler.on_time_quantum_expired(process)
            self._preempt_current_process(None, quantum_expired=True)
    
    def _schedule_next_process(self):
        """Schedule the next process from the scheduler"""
        next_process = self.scheduler.get_next_process()
        if next_process:
            # Start context switch if needed
            if self.context_switch_time > 0:
                self.is_context_switching = True
                self.context_switch_end_time = self.current_time + self.context_switch_time
                return
            
            # Start executing the process
            self._start_execution(next_process)
    
    def _start_execution(self, process: PCB):
        """Start executing a process"""
        self.running_process = process
        process.state = ProcessState.RUNNING
        
        # Record first run time for response time
        if process.first_run_time is None:
            process.first_run_time = self.current_time
        
        # Calculate execution time
        if isinstance(self.scheduler, MLFQScheduler):
            time_quantum = self.scheduler.get_time_quantum_for_process(process)
        elif hasattr(self.scheduler, 'get_time_quantum'):
            time_quantum = self.scheduler.get_time_quantum()
        else:
            time_quantum = None  # Execute until completion
        
        # Execute the process
        if time_quantum:
            execution_time = min(process.remaining_cpu_time, time_quantum)
            # Schedule timeout for Round Robin and MLFQ
            if isinstance(self.scheduler, (RoundRobinScheduler, MLFQScheduler)):
                timeout_time = self.current_time + execution_time
                self.event_queue.schedule_timeout(process.process_id, timeout_time)
        else:
            execution_time = process.remaining_cpu_time
        
        # Schedule CPU completion
        completion_time = self.current_time + execution_time
        self.event_queue.schedule_cpu_completion(process.process_id, completion_time)
        
        # Update Gantt chart
        self.gantt_chart.append((self.current_time, completion_time, process.process_id))
    
    def _preempt_current_process(self, new_process: PCB = None, quantum_expired: bool = False):
        """Preempt the currently running process"""
        if self.running_process:
            process = self.running_process
            process.state = ProcessState.READY
            process.preempted = True
            process.context_switches += 1
            
            # Update remaining time (already accounted for in execution)
            # Add back to scheduler
            self.scheduler.add_process(process)
            
            # Update Gantt chart end time
            if self.gantt_chart and self.gantt_chart[-1][2] == process.process_id:
                start, _, _ = self.gantt_chart[-1]
                self.gantt_chart[-1] = (start, self.current_time, process.process_id)
            
            self.running_process = None
            self.stats_collector.preemptions += 1
            
            # Start context switch for new process
            if new_process:
                self.scheduler.add_process(new_process)
    
    def _complete_current_process(self):
        """Complete the current running process"""
        if self.running_process:
            process = self.running_process
            process.state = ProcessState.TERMINATED
            process.completion_time = self.current_time
            process.calculate_metrics()
            
            # Record statistics
            self.stats_collector.record_process_completion(process)
            self.completed_processes.append(process)
            
            # Update Gantt chart
            if self.gantt_chart and self.gantt_chart[-1][2] == process.process_id:
                start, _, _ = self.gantt_chart[-1]
                self.gantt_chart[-1] = (start, self.current_time, process.process_id)
            
            self.running_process = None
    
    def _update_waiting_times(self):
        """Update waiting times for all ready processes"""
        time_diff = self.current_time - self.last_update_time
        self.scheduler.update_waiting_times(self.current_time, self.last_update_time)
        self.last_update_time = self.current_time
    
    def _collect_results(self) -> SimulationResult:
        """Collect and return simulation results"""
        # Calculate system-wide metrics
        total_time = self.current_time
        cpu_time = total_time - self.idle_time
        cpu_utilization = (cpu_time / total_time) * 100 if total_time > 0 else 0
        
        # Get metrics from statistics collector
        metrics = self.stats_collector.calculate_metrics(self.completed_processes)
        metrics["cpu_utilization"] = cpu_utilization
        metrics["throughput"] = len(self.completed_processes) / (total_time / 1000)  # processes per second
        
        # Calculate fairness index (Jain's fairness)
        turnaround_times = [p.turnaround_time for p in self.completed_processes]
        if turnaround_times:
            sum_times = sum(turnaround_times)
            sum_squares = sum(t * t for t in turnaround_times)
            fairness = (sum_times ** 2) / (len(turnaround_times) * sum_squares) if sum_squares > 0 else 1
            metrics["fairness_index"] = fairness
        
        # Collect process statistics
        process_stats = []
        for process in self.completed_processes:
            process_stats.append({
                "pid": process.process_id,
                "arrival": process.arrival_time,
                "completion": process.completion_time,
                "turnaround": process.turnaround_time,
                "waiting": process.waiting_time,
                "response": process.response_time,
                "priority": process.priority
            })
        
        return SimulationResult(
            algorithm_name=self.scheduler.name,
            metrics=metrics,
            process_stats=process_stats,
            gantt_chart=self.gantt_chart,
            cpu_utilization=cpu_utilization
        )