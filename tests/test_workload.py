#!/usr/bin/env python3
"""
Unit tests for workload generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from src.workload_generator import WorkloadGenerator, WorkloadConfig
from src.pcb import PCB

class TestWorkloadConfig(unittest.TestCase):
    """Test WorkloadConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = WorkloadConfig()
        
        self.assertEqual(config.num_processes, 100)
        self.assertEqual(config.arrival_lambda, 0.01)
        self.assertEqual(config.cpu_burst_mean, 50.0)
        self.assertEqual(config.cpu_burst_std, 20.0)
        self.assertEqual(config.io_burst_min, 10)
        self.assertEqual(config.io_burst_max, 100)
        self.assertEqual(config.priority_min, 1)
        self.assertEqual(config.priority_max, 10)
        self.assertEqual(config.workload_type, "mixed")
        self.assertEqual(config.cpu_io_ratio, 0.7)
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = WorkloadConfig(
            num_processes=500,
            arrival_lambda=0.02,
            cpu_burst_mean=75.0,
            cpu_burst_std=25.0,
            io_burst_min=5,
            io_burst_max=50,
            priority_min=1,
            priority_max=5,
            workload_type="cpu_intensive",
            cpu_io_ratio=0.9
        )
        
        self.assertEqual(config.num_processes, 500)
        self.assertEqual(config.arrival_lambda, 0.02)
        self.assertEqual(config.cpu_burst_mean, 75.0)
        self.assertEqual(config.cpu_burst_std, 25.0)
        self.assertEqual(config.io_burst_min, 5)
        self.assertEqual(config.io_burst_max, 50)
        self.assertEqual(config.priority_min, 1)
        self.assertEqual(config.priority_max, 5)
        self.assertEqual(config.workload_type, "cpu_intensive")
        self.assertEqual(config.cpu_io_ratio, 0.9)

class TestWorkloadGenerator(unittest.TestCase):
    """Test WorkloadGenerator class"""
    
    def setUp(self):
        self.config = WorkloadConfig(num_processes=10)
        self.generator = WorkloadGenerator(self.config)
    
    def test_synthetic_workload_cpu_intensive(self):
        """Test CPU-intensive workload generation"""
        config = WorkloadConfig(
            num_processes=50,
            workload_type="cpu_intensive"
        )
        generator = WorkloadGenerator(config)
        
        processes = generator.generate_synthetic_workload()
        
        self.assertEqual(len(processes), 50)
        
        # Check that processes have reasonable values
        for process in processes:
            self.assertIsInstance(process, PCB)
            self.assertGreater(process.total_cpu_time, 0)
            self.assertGreaterEqual(process.io_burst_time, config.io_burst_min)
            self.assertLessEqual(process.io_burst_time, config.io_burst_max // 2)
    
    def test_synthetic_workload_io_intensive(self):
        """Test I/O-intensive workload generation"""
        config = WorkloadConfig(
            num_processes=50,
            workload_type="io_intensive"
        )
        generator = WorkloadGenerator(config)
        
        processes = generator.generate_synthetic_workload()
        
        self.assertEqual(len(processes), 50)
        
        # Check that processes have reasonable values
        for process in processes:
            self.assertIsInstance(process, PCB)
            self.assertGreater(process.total_cpu_time, 0)
            self.assertGreaterEqual(process.io_burst_time, config.io_burst_max // 2)
            self.assertLessEqual(process.io_burst_time, config.io_burst_max)
    
    def test_synthetic_workload_mixed(self):
        """Test mixed workload generation"""
        config = WorkloadConfig(
            num_processes=100,
            workload_type="mixed"
        )
        generator = WorkloadGenerator(config)
        
        processes = generator.generate_synthetic_workload()
        
        self.assertEqual(len(processes), 100)
        
        # Count CPU vs I/O intensive processes
        cpu_intensive = 0
        io_intensive = 0
        
        for process in processes:
            if process.io_burst_time <= config.io_burst_max // 2:
                cpu_intensive += 1
            else:
                io_intensive += 1
        
        # Should have mix of both (roughly 70% CPU intensive based on default ratio)
        self.assertGreater(cpu_intensive, 0)
        self.assertGreater(io_intensive, 0)
        self.assertGreater(cpu_intensive, io_intensive)  # More CPU intensive in mixed
    
    def test_generate_from_trace(self):
        """Test trace file parsing"""
        # Create a temporary trace file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Write sample trace data
            f.write("# Test trace file\n")
            f.write("1,0,50,20,1\n")
            f.write("2,10,30,15,2\n")
            f.write("3,20,40,25,3\n")
            f.write("\n")  # Empty line
            f.write("4,30,60,30,1\n")
            temp_file = f.name
        
        try:
            # Generate from trace file
            processes = self.generator.generate_from_trace(temp_file)
            
            # Should parse 4 processes
            self.assertEqual(len(processes), 4)
            
            # Check first process
            self.assertEqual(processes[0].process_id, 1)
            self.assertEqual(processes[0].arrival_time, 0)
            self.assertEqual(processes[0].total_cpu_time, 50)
            self.assertEqual(processes[0].io_burst_time, 20)
            self.assertEqual(processes[0].priority, 1)
            
            # Check last process
            self.assertEqual(processes[3].process_id, 4)
            self.assertEqual(processes[3].arrival_time, 30)
            self.assertEqual(processes[3].total_cpu_time, 60)
            self.assertEqual(processes[3].io_burst_time, 30)
            self.assertEqual(processes[3].priority, 1)
            
            # Test with non-existent file
            processes = self.generator.generate_from_trace("non_existent.txt")
            self.assertEqual(len(processes), 0)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_generate_from_trace_invalid_format(self):
        """Test trace file parsing with invalid format"""
        # Create a temporary trace file with invalid data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("1,0,50,20,1\n")
            f.write("invalid,data,here\n")  # Invalid line
            f.write("2,10,thirty,15,2\n")   # Non-integer CPU burst
            f.write("3,20,40\n")            # Missing fields
            temp_file = f.name
        
        try:
            # Should handle invalid lines gracefully
            processes = self.generator.generate_from_trace(temp_file)
            
            # Should parse only valid lines
            self.assertEqual(len(processes), 1)
            self.assertEqual(processes[0].process_id, 1)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_create_sample_traces(self):
        """Test sample trace generation"""
        traces = self.generator.create_sample_traces()
        
        # Should generate traces for all workload types
        self.assertIn('cpu_intensive', traces)
        self.assertIn('io_intensive', traces)
        self.assertIn('mixed', traces)
        
        # Check each trace has correct number of processes
        self.assertEqual(len(traces['cpu_intensive']), 100)
        self.assertEqual(len(traces['io_intensive']), 100)
        self.assertEqual(len(traces['mixed']), 200)
        
        # Check trace format
        for workload_type, trace_lines in traces.items():
            for line in trace_lines[:10]:  # Check first 10 lines
                parts = line.split(',')
                self.assertEqual(len(parts), 5)  # 5 fields
                
                # All fields should be integers
                pid, arrival, cpu, io, priority = parts
                self.assertTrue(pid.isdigit())
                self.assertTrue(arrival.isdigit())
                self.assertTrue(cpu.isdigit())
                self.assertTrue(io.isdigit())
                self.assertTrue(priority.isdigit())
    
    def test_process_id_sequencing(self):
        """Test that process IDs are sequenced correctly"""
        # Generate first batch
        processes1 = self.generator.generate_synthetic_workload()
        
        # Generate second batch
        processes2 = self.generator.generate_synthetic_workload()
        
        # Check that process IDs continue from where left off
        max_id1 = max(p.process_id for p in processes1)
        min_id2 = min(p.process_id for p in processes2)
        
        self.assertEqual(min_id2, max_id1 + 1)
    
    def test_arrival_time_distribution(self):
        """Test that arrival times follow Poisson distribution"""
        config = WorkloadConfig(
            num_processes=1000,
            arrival_lambda=0.01  # Expect ~10ms average inter-arrival
        )
        generator = WorkloadGenerator(config)
        
        processes = generator.generate_synthetic_workload()
        
        # Calculate inter-arrival times
        arrival_times = [p.arrival_time for p in processes]
        inter_arrival_times = [arrival_times[i] - arrival_times[i-1] 
                              for i in range(1, len(arrival_times))]
        
        # Basic statistics check (not a full statistical test)
        avg_inter_arrival = sum(inter_arrival_times) / len(inter_arrival_times)
        
        # With lambda = 0.01, expected average = 100ms
        # Allow some variation due to randomness
        self.assertGreater(avg_inter_arrival, 50)  # Should be > 50ms
        self.assertLess(avg_inter_arrival, 200)    # Should be < 200ms

def run_workload_tests():
    """Run all workload tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWorkloadConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkloadGenerator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_workload_tests()
    sys.exit(0 if success else 1)