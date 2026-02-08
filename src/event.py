from enum import Enum
from dataclasses import dataclass
import heapq
from typing import List, Optional, Any

class EventType(Enum):
    """Types of events in the discrete-event simulation"""
    PROCESS_ARRIVAL = "PROCESS_ARRIVAL"
    CPU_BURST_COMPLETE = "CPU_BURST_COMPLETE"
    IO_BURST_COMPLETE = "IO_BURST_COMPLETE"
    TIME_QUANTUM_EXPIRED = "TIME_QUANTUM_EXPIRED"
    PREEMPTION = "PREEMPTION"
    CONTEXT_SWITCH = "CONTEXT_SWITCH"

@dataclass(order=True)
class Event:
    """Event for discrete-event simulation"""
    timestamp: int
    type: EventType = field(compare=False)
    process_id: int = field(compare=False)
    data: Any = field(compare=False, default=None)
    
    def __str__(self):
        return f"Event[{self.timestamp}: {self.type.name} for P{self.process_id}]"

class EventQueue:
    """Priority queue for events sorted by timestamp"""
    
    def __init__(self):
        self.queue = []
        self.event_count = 0
    
    def push(self, event: Event):
        """Add an event to the queue"""
        heapq.heappush(self.queue, event)
        self.event_count += 1
    
    def pop(self) -> Optional[Event]:
        """Remove and return the next event"""
        if self.queue:
            self.event_count -= 1
            return heapq.heappop(self.queue)
        return None
    
    def peek(self) -> Optional[Event]:
        """View the next event without removing it"""
        return self.queue[0] if self.queue else None
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def size(self) -> int:
        return len(self.queue)
    
    def clear(self):
        self.queue.clear()
        self.event_count = 0
    
    def schedule_arrival(self, process_id: int, arrival_time: int):
        """Schedule a process arrival event"""
        self.push(Event(arrival_time, EventType.PROCESS_ARRIVAL, process_id))
    
    def schedule_cpu_completion(self, process_id: int, completion_time: int, data=None):
        """Schedule CPU burst completion event"""
        self.push(Event(completion_time, EventType.CPU_BURST_COMPLETE, process_id, data))
    
    def schedule_io_completion(self, process_id: int, completion_time: int):
        """Schedule I/O burst completion event"""
        self.push(Event(completion_time, EventType.IO_BURST_COMPLETE, process_id))
    
    def schedule_timeout(self, process_id: int, timeout_time: int):
        """Schedule time quantum expiration event"""
        self.push(Event(timeout_time, EventType.TIME_QUANTUM_EXPIRED, process_id))