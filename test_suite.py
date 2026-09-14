import unittest
import utilities.test_metadata_util as metadata_test
import utilities.test_restapi_utils as restapi_test
import utilities.test_commonutitls as common_utils_test
import utilities.test_commonlab_util as commonlab_utils_test
import utilities.test_patient_utils as patient_utils_test

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(commonlab_utils_test))
suite.addTests(loader.loadTestsFromModule(common_utils_test))
suite.addTests(loader.loadTestsFromModule(metadata_test))
suite.addTests(loader.loadTestsFromModule(restapi_test))
suite.addTests(loader.loadTestsFromModule(patient_utils_test))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
