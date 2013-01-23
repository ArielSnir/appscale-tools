#!/usr/bin/env python
# Programmer: Chris Bunch (chris@appscale.com)


# General-purpose Python library imports
import os
import sys
import unittest


# AppScale import, the library that we're testing here
lib = os.path.dirname(__file__) + os.sep + ".." + os.sep + "lib"
sys.path.append(lib)
import local_state
import vm_tools

from custom_exceptions import BadConfigurationException
from parse_args import ParseArgs


class TestParseArgs(unittest.TestCase):
  

  def setUp(self):
    self.argv = ['--min', '1', '--max', '1']
    self.function = "appscale-run-instances"


  def test_flags_that_cause_program_abort(self):
    # using a flag that isn't acceptable should raise
    # an exception
    argv_1 = ['--boo!']
    self.assertRaises(SystemExit, ParseArgs, argv_1, 
      self.function)

    # the version flag should quit and print the current
    # version of the tools
    argv_2 = ['--version']
    all_flags_2 = ['version']
    with self.assertRaises(SystemExit) as context_manager:
      ParseArgs(argv_2, self.function)
    self.assertEquals(local_state.APPSCALE_VERSION,
      context_manager.exception.message)


  def test_get_min_and_max(self):
    # Setting min or max below 1 is not acceptable
    argv_1 = ['--min', '0', '--max', '1']
    self.assertRaises(BadConfigurationException,
      ParseArgs, argv_1, self.function)

    argv_2 = ['--min', '1', '--max', '0']
    self.assertRaises(BadConfigurationException,
      ParseArgs, argv_2, self.function)

    # If max is specified but not min, min should be equal to max
    argv_3 = ['--max', '1']
    actual_3 = ParseArgs(argv_3, self.function)
    self.assertEquals(actual_3.args.min, actual_3.args.max)

    # If max is less than min, it should abort
    argv_4 = ['--min', '10', '--max', '1']
    self.assertRaises(BadConfigurationException, ParseArgs, argv_4,
      self.function)


  def test_table_flags(self):
    # Specifying a table that isn't accepted should abort
    argv_1 = self.argv[:] + ['--table', 'non-existent-database']
    self.assertRaises(BadConfigurationException, ParseArgs, argv_1,
      self.function)

    # Specifying a table that is accepted should return that in the result
    argv_2 = self.argv[:] + ['--table', 'cassandra']
    actual_2 = ParseArgs(argv_2, self.function)
    self.assertEquals('cassandra', actual_2.args.table)

    # Failing to specify a table should default to a predefined table
    args_3 = self.argv[:]
    actual_3 = ParseArgs(args_3, self.function)
    self.assertEquals(local_state.DEFAULT_DATASTORE, actual_3.args.table)

    # Specifying a non-positive integer for n should abort
    argv_4 = self.argv[:] + ['--table', 'cassandra', '-n', '0']
    self.assertRaises(BadConfigurationException, ParseArgs, argv_4,
      self.function)

    # Specifying a positive integer for n should be ok
    argv_5 = self.argv[:] + ['--table', 'cassandra', '-n', '2']
    actual_5 = ParseArgs(argv_5, self.function)
    self.assertEquals(2, actual_5.args.n)


  def test_gather_logs_flags(self):
    # Specifying auto, force, or test should have that carried over
    # to in the resulting hash
    argv = ["--location", "/boo/baz"]
    actual = ParseArgs(argv, "appscale-gather-logs")
    self.assertEquals("/boo/baz", actual.args.location)


  def test_developer_flags(self):
    # Specifying force or test should have that carried over
    # to in the resulting hash
    argv_1 = self.argv[:] + ['--force']
    actual_1 = ParseArgs(argv_1, self.function)
    self.assertEquals(True, actual_1.args.force)

    argv_2 = self.argv[:] + ['--test']
    actual_2 = ParseArgs(argv_2, self.function)
    self.assertEquals(True, actual_2.args.test)


  def test_infrastructure_flags(self):
    # Specifying infastructure as EC2 or Eucalyptus is acceptable.
    argv_1 = self.argv[:] + ['--infrastructure', 'ec2', '--machine', 'ami-XYZ']
    actual_1 = ParseArgs(argv_1, self.function)
    self.assertEquals('ec2', actual_1.args.infrastructure)

    argv_2 = self.argv[:] + ['--infrastructure', 'euca', '--machine', 'emi-ABC']
    actual_2 = ParseArgs(argv_2, self.function)
    self.assertEquals('euca', actual_2.args.infrastructure)

    # Specifying something else as the infrastructure is not acceptable.
    argv_3 = self.argv[:] + ['--infrastructure', 'boocloud', '--machine', 'boo']
    self.assertRaises(BadConfigurationException, ParseArgs,
      argv_3, self.function)


  def test_instance_types(self):
    # Not specifying an instance type should default to a perdetermined
    # value.
    argv_1 = self.argv[:]
    actual = ParseArgs(argv_1, self.function)
    self.assertEquals(vm_tools.DEFAULT_INSTANCE_TYPE,
      actual.args.instance_type)

    # Specifying m1.large as the instance type is acceptable.
    argv_2 = self.argv[:] + ['--instance_type', 'm1.large']
    actual = ParseArgs(argv_2, self.function)
    self.assertEquals("m1.large", actual.args.instance_type)

    # Specifying blarg1.humongous as the instance type is not
    # acceptable.
    argv_3 = self.argv[:] + ['--instance_type', 'blarg1.humongous']
    self.assertRaises(BadConfigurationException, ParseArgs,
      argv_3, self.function)


  def test_machine_not_set_in_cloud_deployments(self):
    # when running in a cloud infrastructure, we need to know what
    # machine image to use
    argv = self.argv[:] + ["--infrastructure", "euca"]
    self.assertRaises(BadConfigurationException, ParseArgs, argv,
      "appscale-run-instances")


  def test_scaling_flags(self):
    # Specifying a value for add_to_existing should fail
    argv_1 = ["--add_to_existing", "boo"]
    self.assertRaises(SystemExit, ParseArgs, argv_1,
      "appscale-add-keypair")

    # not specifying a value should set it to true
    argv_2 = ["--add_to_existing"]
    actual = ParseArgs(argv_2, "appscale-add-keypair")
    self.assertEquals(True, actual.args.add_to_existing)
