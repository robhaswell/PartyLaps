# python -m unittest
import os.path
import tempfile
import unittest

import PartyLaps

class ACNOOP(object):
    def newApp(*args):
        pass


class TestCycleDrivers(unittest.TestCase):
    """
    Tests for ``PartyLaps.cycleDrivers``.
    """

    sampleDrivers = ['alpha', 'beta', 'gamma', 'delta']

    def test_emptyList(self):
        result = PartyLaps.cycleDriver([], "")
        self.assertEqual(result, "")

    def test_emptyDriver(self):
        result = PartyLaps.cycleDriver(self.sampleDrivers, "")
        self.assertEqual(result, "alpha")

    def test_unknownDriver(self):
        result = PartyLaps.cycleDriver(self.sampleDrivers, "The Stig")
        self.assertEqual(result, "alpha")

    def test_nextDriver(self):
        result = PartyLaps.cycleDriver(self.sampleDrivers, "beta")
        self.assertEqual(result, "gamma")

    def test_rollover(self):
        result = PartyLaps.cycleDriver(self.sampleDrivers, "delta")
        self.assertEqual(result, "alpha")


class TestPersonalBests(unittest.TestCase):
    """
    Tests for reading and writing personal bests.
    """

    def setUp(self):
        self.app = PartyLaps.PartyLaps(ACNOOP(), "", "", object())
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


    def test_resetCurrentDriver(self):
        """
        The current driver's personal best is reset.
        """
        PartyLaps.currentDriver = "alpha"
        pb = {
                "time": 1234567890,
                "data": [(0, 0), (1, 1), (2, 2)],
        }
        self.app.personalBests = {
            "alpha": pb,
            "beta": pb,
        }

        self.app.writePersonalBests()

        self.app.resetBestLap()

        self.assertNotIn("alpha", self.app.personalBests)


    def test_otherDriversNotReset(self):
        """
        The other drivers' personal bests are not reset.
        """
        PartyLaps.currentDriver = "alpha"
        pb = {
                "time": 1234567890,
                "data": [(0, 0), (1, 1), (2, 2)],
        }
        self.app.personalBests = {
            "alpha": pb,
            "beta": pb,
        }

        self.app.writePersonalBests()

        self.app.resetBestLap()

        self.assertIn("beta", self.app.personalBests)


    def test_resetRemovesBestLapFile(self):
        """
        The best lap file is removed when the best lap is reset.
        """
        self.app.writeBestLap()
        self.assertTrue(os.path.exists(self.app.bestLapFile))

        self.app.resetBestLap()
        self.assertFalse(os.path.exists(self.app.bestLapFile))
