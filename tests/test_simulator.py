#!/usr/bin/env python3
"""
Unit tests for the simulator module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import numpy as np
from src.pcb import PCB, ProcessState
from src.event import Event, EventQueue, EventType
from src.simulator import CPUSimulator
from src.schedulers.fcfs import FCFSScheduler
from src.workload_generator import WorkloadGenerator, WorkloadConfig

class TestEventQueue(unittest.TestCase):
    """Test EventQueue functionality"""
    
    def setUp(self):
        self.event_queue = EventQueue()
    
    def test_push_pop(self):
        """Test basic push and pop operations"""
        event1 = Event(100, EventType.PROCESS_ARRIVAL, 1)
        event2 = Event(50, EventType.PROCESS_ARRIVAL, 2)
        
        self.event_queue.push(event1)
        self.event_queue.push(event2)
        
        # Should pop event with earliest timestamp first
        self.assertEqual(self.event_queue.pop().timestamp, 50)
        self.assertEqual(self.event_queue.pop().timestamp, 100)
    
    def test_is_empty(self):
        """Test is_empty method"""
        self.assertTrue(self.event_queue.is_empty())
        
        event = Event(100, EventType.PROCESS_ARRIVAL, 1)
        self.event_queue.push(event)
        
        self.assertFalse(self.event_queue.is_empty())
        
        self.event_queue.pop()
        self.assertTrue(self.event_queue.is_empty())
    
    def test_schedule_methods(self):
        """Test schedule helper methods"""
        self.event_queue.schedule_arrival(1, 100)
        self.event_queue.schedule_cpu_completion(2, 200)
        self.event_queue.schedule_io_completion(3, 300)
        self.event_queue.schedule_timeout(4, 400)
        
        self.assertEqual(self.event_queue.size(), 4)
        
        # Check event types
        events = []
        while not self.event_queue.is_empty():
            events.append(self.event_queue.pop())
        
        event_types = [e.type for e in events]
        self.assertEqual(event_types, [
            EventType.PROCESS_ARRIVAL,
            EventType.CPU_BURST_COMPLETE,
            EventType.IO_BURST_COMPLETE,
            EventType.TIME_QUANTUM_EXPIRED
        ])

class TestPCB(unittest.TestCase):
    """Test PCB functionality"""
    
    def test_creation(self):
        """Test PCB creation"""
        pcb = PCB(
            process_id=1,
            arrival_time=0,
            total_cpu_time=100,
            remaining_cpu_time=100,
            io_burst_time=50,
            priority=1
        )
        
        self.assertEqual(pcb.process_id, 1)
        self.assertEqual(pcb.arrival_time, 0)
        self.assertEqual(pcb.total_cpu_time, 100)
        self.assertEqual(pcb.remaining_cpu_time, 100)
        self.assertEqual(pcb.io_burst_time, 50)
        self.assertEqual(pcb.priority, 1)
        self.assertEqual(pcb.state, ProcessState.NEW)
    
    def test_execute(self):
        """Test process execution"""
        pcb = PCB(
            process_id=1,
            arrival_time=0,
            total_cpu_time=100,
            remaining_cpu_time=100,
            io_burst_time=50,
            priority=1
        )
        
        # Execute without time slice (until completion)
        time_used, completed, remaining = pcb.execute()
        self.assertEqual(time_used, 100)
        self.assertTrue(completed)
        self.assertEqual(remaining, 0)
        self.assertEqual(pcb.remaining_cpu_time, 0)
    
    def test_execute_with_time_slice(self):
        """Test process execution with time slice"""
        pcb = PCB(
            process_id=1,
            arrival_time=0,
            total_cpu_time=100,
            remaining_cpu_time=100,
            io_burst_time=50,
            priority=1
        )
        
        # Execute with time slice
        time_used, completed, remaining = pcb.execute(time_slice=30)
        self.assertEqual(time_used, 30)
        self.assertFalse(completed)
        self.assertEqual(remaining, 70)
        self.assertEqual(pcb.remaining_cpu_time, 70)
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        pcb = PCB(
            process_id=1,
            arrival_time=0,
            total_cpu_time=100,
            remaining_cpu_time=0,
            io_burst_time=50,
            priority=1
        )
        
        pcb.start_time = 10
        pcb.first_run_time = 10
        pcb.completion_time = 150
        pcb.total_waiting_time = 40
        
        pcb.calculate_metrics()
        
        self.assertEqual(pcb.turnaround_time, 150)
        self.assertEqual(pcb.waiting_time, 40)
        self.assertEqual(pcb.response_time, 10)
    
    def test_age_priority(self):
        """Test priority aging"""
        pcb = PCB(
            process_id=1,
            arrival_time=0,
            total_cpu_time=100,
            remaining_cpu_time=100,
            io_burst_time=50,
            priority=5
        )
        
        # Test aging when enough time has passed
        aged = pcb.age_priority(current_time=1500, aging_interval=1000)
        self.assertTrue(aged)
        self.assertEqual(pcb.priority, 4)
        
        # Test aging when not enough time has passed
        aged = pcb.age_priority(current_time=2000, aging_interval=1000)
        self.assertFalse(aged)
        self.assertEqual(pcb.priority, 4)
        
        # Test aging when priority is already 1
        pcb.priority = 1
        aged = pcb.age_priority(current_time=3000, aging_interval=1000)
        self.assertFalse(aged)
        self.assertEqual(pcb.priority, 1)

class TestSimulator(unittest.TestCase):
    """Test CPUSimulator functionality"""
    
    def setUp(self):
        self.scheduler = FCFSScheduler()
        self.simulator = CPUSimulator(self.scheduler, context_switch_time=2)
    
    def test_initialize_simulation(self):
        """Test simulation initialization"""
        # Create test processes
        processes = [
            PCB(1, 0, 50, 50, 20, 1),
            PCB(2, 10, 30, 30, 15, 2),
            PCB(3, 20, 40, 40, 25, 3)
        ]
        
        self.simulator.initialize_simulation(processes)
        
        # Check that processes are stored
        self.assertEqual(len(self.simulator.processes), 3)
        self.assertIn(1, self.simulator.processes)
        self.assertIn(2, self.simulator.processes)
        self.assertIn(3, self.simulator.processes)
        
        # Check that arrival events are scheduled
        self.assertEqual(self.simulator.event_queue.size(), 3)
    
    def test_simple_simulation(self):
        """Test a simple simulation with one process"""
        processes = [
            PCB(1, 0, 50, 50, 20, 1)
        ]
        
        self.simulator.initialize_simulation(processes)
        result = self.simulator.run(max_time=100)
        
        # Check that process completed
        self.assertEqual(len(self.simulator.completed_processes), 1)
        
        # Check metrics
        self.assertGreater(result.metrics['cpu_utilization'], 0)
        self.assertEqual(result.metrics['total_processes'], 1)
    
    def test_preemption_handling(self):
        """Test preemption handling"""
        # Use a preemptive scheduler
        from src.schedulers.priority import PriorityScheduler
        scheduler = PriorityScheduler(preemptive=True)
        simulator = CPUSimulator(scheduler, context_switch_time=2)
        
        # Create processes with different priorities
        processes = [
            PCB(1, 0, 100, 100, 20, 2),  # Lower priority (higher number)
            PCB(2, 10, 50, 50, 15, 1)    # Higher priority (lower number)
        ]
        
        simulator.initialize_simulation(processes)
        result = simulator.run(max_time=200)
        
        # Higher priority process should preempt lower priority one
        self.assertEqual(len(simulator.completed_processes), 2)
        self.assertGreater(result.metrics['preemptions'], 0)

class TestWorkloadGenerator(unittest.TestCase):
    """Test WorkloadGenerator functionality"""
    
    def setUp(self):
        self.config = WorkloadConfig(num_processes=10)
        self.generator = WorkloadGenerator(self.config)
    
    def test_synthetic_workload_generation(self):
        """Test synthetic workload generation"""
        processes = self.generator.generate_synthetic_workload()
        
        # Check number of processes
        self.assertEqual(len(processes), self.config.num_processes)
        
        # Check process attributes
        for process in processes:
            self.assertIsInstance(process, PCB)
            self.assertGreaterEqual(process.arrival_time, 0)
            self.assertGreater(process.total_cpu_time, 0)
            self.assertGreaterEqual(process.io_burst_time, self.config.io_burst_min)
            self.assertLessEqual(process.io_burst_time, self.config.io_burst_max)
            self.assertGreaterEqual(process.priority, self.config.priority_min)
            self.assertLessEqual(process.priority, self.config.priority_max)
    
    def test_trace_generation(self):
        """Test trace file generation"""
        traces = self.generator.create_sample_traces()
        
        # Check that all workload types are generated
        self.assertIn('cpu_intensive', traces)
        self.assertIn('io_intensive', traces)
        self.assertIn('mixed', traces)
        
        # Check trace content
        for workload_type, trace_lines in traces.items():
            self.assertGreater(len(trace_lines), 0)
            
            # Check first few lines have correct format
            for i, line in enumerate(trace_lines[:5]):
                parts = line.split(',')
                self.assertEqual(len(parts), 5)  # 5 fields per process
                
                # All parts should be integers
                for part in parts:
                    try:
                        int(part)
                    except ValueError:
                        self.fail(f"Non-integer value in trace: {part}")

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEventQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestPCB))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkloadGenerator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)