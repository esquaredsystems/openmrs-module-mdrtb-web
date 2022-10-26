# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 14:40:18 2019

@author: Owais

@description: This module executes all the tests from
"""

import unittest
import ETB.test_metadata_util

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(ETB.test_metadata_util))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
