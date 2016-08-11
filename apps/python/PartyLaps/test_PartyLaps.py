# python -m unittest
import unittest
import tempfile

from PartyLaps import cycleDriver, PartyLaps

class ACNOOP(object):
    def newApp(*args):
        pass

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


class TestPersonalBests(unittest.TestCase):
    """
    Tests for reading and writing personal bests.
    """

    def setUp(self):
        self.app = PartyLaps(ACNOOP(), "", "", object())
        self.app.bestLapFile = tempfile.NamedTemporaryFile().name


    def test_writeReadSimple(self):
        """
        A personal bests without unusual characters in the driver name can be written and then read.
        """
        driver = "alpha"
        pb = {
                "time": 1234567890,
                "data": [(0, 0), (1, 1), (2, 2)],
        }
        self.app.personalBests = {
            driver: pb,
        }

        self.app.writePersonalBests()

        self.app.personalBests = {}

        self.app.readPersonalBests()

        self.assertEqual(self.app.personalBests[driver], pb)


    def test_writeReadSpecial(self):
        """
        A personal bests with special characters in the driver name can be written and then read.
        """
        driver = "alpha' omegea"
        pb = {
                "time": 1234567890,
                "data": [(0, 0), (1, 1), (2, 2)],
        }
        self.app.personalBests = {
            driver: pb,
        }

        self.app.writePersonalBests()

        self.app.personalBests = {}

        self.app.readPersonalBests()

        self.assertEqual(self.app.personalBests[driver], pb)


    def test_writeReadUnicode(self):
        """
        A personal bests with special characters in the driver name can be written and then read.
        """
        driver = "alpha⛄️omegea"
        pb = {
                "time": 1234567890,
                "data": [(0, 0), (1, 1), (2, 2)],
        }
        self.app.personalBests = {
            driver: pb,
        }

        self.app.writePersonalBests()
        
        self.app.personalBests = {}

        self.app.readPersonalBests()

        self.assertEqual(self.app.personalBests[driver], pb)
