# python -m unittest  tests/test_hod_pdf.py
import unittest
import numpy as np
import math
from numba import jit

import src.hod_pdf as pdf

class TestPoissonSample(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Set random seed for reproducible tests
        np.random.seed(42)
        
    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_poisson_sample(self):
        """Test behavior with lambda = 0"""
        np.random.seed(42)
        result = pdf.poisson_sample(0.0)
        self.assertEqual(result, 0, "Poisson(0) should return 0")
        
        """Test behavior with negative lambda"""
        np.random.seed(42)
        result = pdf.poisson_sample(-1.0)
        self.assertEqual(result, 0, "Negative lambda should return 0")
    
        """Test with small lambda values"""
        test_lambdas = [0.1, 0.5, 1.0, 2.0]  
        for lam in test_lambdas:
            with self.subTest(lambda_val=lam):
                np.random.seed(42)
                # Generate multiple samples
                samples = [pdf.poisson_sample(lam) for _ in range(1000)]
                
                # Basic checks
                self.assertTrue(all(s >= 0 for s in samples), 
                               f"All samples should be non-negative for lambda={lam}")
                self.assertTrue(all(isinstance(s, (int, np.integer)) for s in samples),
                               f"All samples should be integers for lambda={lam}")

    def test_next_integer(self):
        """Test next_integer function"""
        # Test with exact integer inputs
        test_integers = [0, 1, 2, 5, 10]
        
        for x in test_integers:
            with self.subTest(x=x, test_type="integer_input"):
                np.random.seed(42)
                samples = [pdf.next_integer(float(x)) for _ in range(100)]
                
                # All samples should equal the input integer
                self.assertTrue(all(s == x for s in samples),
                               f"next_integer({x}) should always return {x}")
        
        # Test with fractional inputs
        test_cases = [
            (1.3, [1, 2]),  # Should return 1 or 2
            (2.7, [2, 3]),  # Should return 2 or 3
            (0.1, [0, 1]),  # Should return 0 or 1
            (5.9, [5, 6]),  # Should return 5 or 6
        ]
        
        for x, expected_values in test_cases:
            with self.subTest(x=x, test_type="fractional_input"):
                np.random.seed(42)
                samples = [pdf.next_integer(x) for _ in range(1000)]
                
                # All samples should be in expected range
                self.assertTrue(all(s in expected_values for s in samples),
                               f"next_integer({x}) should return values in {expected_values}")
                
                # Should get both values with some frequency
                unique_values = set(samples)
                self.assertEqual(len(unique_values), 2,
                               f"next_integer({x}) should return both possible values")
        
        # Test statistical properties
        test_statistical_cases = [
            (1.3, 1.3),  # Expected value should equal input
            (2.7, 2.7),
            (0.1, 0.1),
            (5.5, 5.5),
        ]
        
        for x, expected_mean in test_statistical_cases:
            with self.subTest(x=x, test_type="statistical"):
                np.random.seed(42)
                samples = [pdf.next_integer(x) for _ in range(5000)]
                sample_mean = np.mean(samples)
                
                # Mean should be close to input value
                tolerance = 0.1
                self.assertAlmostEqual(sample_mean, expected_mean, delta=tolerance,
                                     msg=f"next_integer({x}) mean should be close to {expected_mean}")
        
        # Test edge cases
        np.random.seed(42)
        result = pdf.next_integer(0.0)
        self.assertEqual(result, 0, "next_integer(0.0) should return 0")
        
        # Test negative inputs (if function should handle them)
        np.random.seed(42)
        result = pdf.next_integer(-0.5)
        self.assertIn(result, [-1, 0], "next_integer(-0.5) should return -1 or 0")

    def test_neg_binomial(self):
        """Test neg_binomial_sample function"""
        # Test edge cases
        np.random.seed(42)
        result = pdf.neg_binomial_sample(0.0, 1.0)
        self.assertEqual(result, 0, "neg_binomial_sample(0, beta) should return 0")
        
        # Test with positive parameters
        test_cases = [
            (1.0, 0.5),   # mean=1.0, beta=0.5
            (2.0, 1.0),   # mean=2.0, beta=1.0
            (5.0, 0.2),   # mean=5.0, beta=0.2
        ]
        
        for mean, beta in test_cases:
            with self.subTest(mean=mean, beta=beta):
                np.random.seed(42)
                samples = [pdf.neg_binomial_sample(mean, beta) for _ in range(1000)]
                
                # Basic validity checks
                self.assertTrue(all(s >= 0 for s in samples),
                               f"All neg_binomial samples should be non-negative")
                self.assertTrue(all(isinstance(s, (int, np.integer)) for s in samples),
                               f"All neg_binomial samples should be integers")
                
                # Check reasonable range (shouldn't be extremely large)
                max_reasonable = mean + 10 * math.sqrt(mean * (1 + beta * mean))
                self.assertTrue(all(s <= max_reasonable for s in samples),
                               f"neg_binomial samples should be within reasonable range")
        
        # Test statistical properties for a specific case
        mean, beta = 3.0, 0.5
        np.random.seed(42)
        samples = [pdf.neg_binomial_sample(mean, beta) for _ in range(5000)]
        sample_mean = np.mean(samples)
        sample_var = np.var(samples)
        
        # For negative binomial: variance = mean * (1 + beta * mean)
        expected_var = mean * (1 + beta * mean)
        
        # Allow reasonable tolerance for statistical fluctuations
        mean_tolerance = 0.3
        var_tolerance = 0.5 * expected_var
        
        self.assertAlmostEqual(sample_mean, mean, delta=mean_tolerance,
                             msg=f"neg_binomial mean should be close to {mean}")
        self.assertAlmostEqual(sample_var, expected_var, delta=var_tolerance,
                             msg=f"neg_binomial variance should be close to {expected_var}")
        
        # Test that function doesn't hang with extreme parameters
        np.random.seed(42)
        result = pdf.neg_binomial_sample(0.1, 2.0)  # Small mean, large beta
        self.assertIsInstance(result, (int, np.integer), "Should return integer even with extreme params")

    def test_binomial(self):
        """Test binomial_sample function"""
        # Test edge cases
        np.random.seed(42)
        result = pdf.binomial_sample(0.0, -0.5)
        self.assertEqual(result, 0, "binomial_sample(0, beta) should return 0")
        
        # Test with various parameters
        test_cases = [
            (1.0, -0.2),   # mean=1.0, beta=-0.2
            (3.0, -0.5),   # mean=3.0, beta=-0.5
            (5.0, -0.8),   # mean=5.0, beta=-0.8
        ]
        
        for mean, beta in test_cases:
            with self.subTest(mean=mean, beta=beta):
                np.random.seed(42)
                samples = [pdf.binomial_sample(mean, beta) for _ in range(1000)]
                
                # Basic validity checks
                self.assertTrue(all(s >= 0 for s in samples),
                               f"All binomial samples should be non-negative")
                self.assertTrue(all(isinstance(s, (int, np.integer)) for s in samples),
                               f"All binomial samples should be integers")
                
                # For extended binomial, samples should be bounded
                # n_val calculation from function: max(int(mean + 1.0), int(1.0 / abs(beta)))
                a = -beta
                n_val = max(int(mean + 1.0), int(1.0 / a))
                self.assertTrue(all(s <= n_val for s in samples),
                               f"binomial samples should not exceed n_val={n_val}")
        
        # Test statistical properties for a specific case
        mean, beta = 2.0, -0.3
        np.random.seed(42)
        samples = [pdf.binomial_sample(mean, beta) for _ in range(3000)]
        sample_mean = np.mean(samples)
        
        # Mean should be reasonably close to input mean
        # (exact relationship depends on extended binomial formulation)
        mean_tolerance = 1.0  # More generous tolerance for extended binomial
        self.assertLess(abs(sample_mean - mean), mean_tolerance,
                       f"binomial mean {sample_mean:.3f} should be reasonably close to {mean}")
        
        # Test that function completes without hanging
        np.random.seed(42)
        result = pdf.binomial_sample(10.0, -0.9)  # Large mean, beta close to -1
        self.assertIsInstance(result, (int, np.integer), "Should return integer with extreme params")
        
        # Test boundary case where beta approaches -1
        np.random.seed(42)
        result = pdf.binomial_sample(1.0, -0.99)
        self.assertIsInstance(result, (int, np.integer), "Should handle beta close to -1")
        
        # Test that samples are reasonable (not all the same value)
        mean, beta = 4.0, -0.4
        np.random.seed(42)
        samples = [pdf.binomial_sample(mean, beta) for _ in range(1000)]
        unique_values = len(set(samples))
        self.assertGreater(unique_values, 1, "Should generate diverse values, not just one value")
                

if __name__ == '__main__':
    import time
    
    # Run the tests
    unittest.main(verbosity=2)
