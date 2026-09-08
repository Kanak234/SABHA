import unittest
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

class TestSabhaCore(unittest.TestCase):
    def test_sabha_module(self):
        sabha_py = os.path.join(ROOT, 'sabha.py')
        self.assertTrue(os.path.isfile(sabha_py), "sabha.py must exist")

    def test_niyukti_config(self):
        config = os.path.join(ROOT, 'niyukti.json')
        self.assertTrue(os.path.isfile(config), "niyukti.json configuration must exist")

if __name__ == '__main__':
    unittest.main()
