from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import List, Optional, Deque
from collections import deque
import heapq

class MLFQScheduler(BaseScheduler):
    """Multilevel Feedback Queue Scheduler (Bonus)"""
    
    def __init__(self, num_queues: int = 3, time_quanta: List[int] = None):
        super().__init__("MLFQ")
        
        self.num_queues = num_queues
        self.time_quanta = time_quanta or [10, 20, 40]
        self.queues = [deque() for _ in range(num_queues)]
        self.preemptive = True
        
        # Boost parameters
        self.boost_interval = 5000  # Boost all processes every 5s
        self.last_boost_time = 0
        self.promotion_threshold = 2  # Run twice in same queue before promotion
        self.process_counts = {}
    
    def add_process(self, process: PCB):
        """Add new process to highest priority queue (queue 0)"""
        process.current_queue_level = 0
        self.queues[0].append(process)
        self.process_counts[process.process_id] = 0
    
    def get_next_process(self) -> Optional[PCB]:
        """Get process from highest priority non-empty queue"""
        for i in range(self.num_queues):
            if self.queues[i]:
                process = self.queues[i].popleft()
                
                # Track how many times process has run at this level
                self.process_counts[process.process_id] = self.process_counts.get(process.process_id, 0) + 1
                
                return process
        return None
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """Preempt if new process is in a higher priority queue"""
        if not current_process:
            return False
        return new_process.current_queue_level < current_process.current_queue_level
    
    def on_time_quantum_expired(self, process: PCB):
        """Handle process when its time quantum expires"""
        if process.remaining_cpu_time > 0:
            # Check if process should be demoted
            current_level = process.current_queue_level
            run_count = self.process_counts.get(process.process_id, 0)
            
            if run_count >= self.promotion_threshold and current_level < self.num_queues - 1:
                # Demote to lower priority queue
                process.current_queue_level = current_level + 1
                self.process_counts[process.process_id] = 0
            
            # Add to appropriate queue
            new_level = process.current_queue_level
            self.queues[new_level].append(process)
    
    def apply_priority_boost(self, current_time: int):
        """Boost all processes to highest priority queue periodically"""
        if current_time - self.last_boost_time >= self.boost_interval:
            self.last_boost_time = current_time
            
            # Move all processes to queue 0
            for i in range(1, self.num_queues):
                while self.queues[i]:
                    process = self.queues[i].popleft()
                    process.current_queue_level = 0
                    self.queues[0].append(process)
                    self.process_counts[process.process_id] = 0
    
    def get_time_quantum_for_process(self, process: PCB) -> int:
        """Get time quantum based on queue level"""
        level = process.current_queue_level
        if level < len(self.time_quanta):
            return self.time_quanta[level]
        return self.time_quanta[-1]  # Use last quantum for lowest queues
    
    @property
    def ready_queue(self):
        """Get all processes across all queues"""
        all_processes = []
        for q in self.queues:
            all_processes.extend(list(q))
        return all_processes