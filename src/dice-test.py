import unittest
import dices


class MyTestCase(unittest.TestCase):

    def testSegmenting(self):
        for usecase in ["1d20", "d20", "20",
                        "adv d20", "dadv d20",
                        "d20 + 3", "d20+ 3", "d20 +3", "d20+3",
                        "d20 > 14", "d20 >= 14", "d20>4", "d20>=20"]:
            dices.decipher(usecase)


if __name__ == '__main__':
    dices.verbose = False
    unittest.main()
