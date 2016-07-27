import unittest
from PartyLaps import cycleDriver

class TestCycleDrivers(unittest.TestCase):
    """
    Tests for ``cycleDrivers``.
    """

    sampleDrivers = ['alpha', 'beta', 'gamma', 'delta']

    def test_emptyList(self):
        result = cycleDriver([], "")
        self.assertEqual(result, "")

    def test_emptyDriver(self):
        result = cycleDriver(self.sampleDrivers, "")
        self.assertEqual(result, "alpha")

    def test_unknownDriver(self):
        result = cycleDriver(self.sampleDrivers, "The Stig")
        self.assertEqual(result, "alpha")

    def test_nextDriver(self):
        result = cycleDriver(self.sampleDrivers, "beta")
        self.assertEqual(result, "gamma")

    def test_rollover(self):
        result = cycleDriver(self.sampleDrivers, "delta")
        self.assertEqual(result, "alpha")
