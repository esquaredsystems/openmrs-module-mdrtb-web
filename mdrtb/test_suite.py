import unittest
import utilities.test_metadata_util as metadata_test
import utilities.test_restapi_utils as restapi_test

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
# suite.addTests(loader.loadTestsFromModule(rest_test))
suite.addTests(loader.loadTestsFromModule(metadata_test))
# suite.addTests(loader.loadTestsFromModule(restapi_test))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
