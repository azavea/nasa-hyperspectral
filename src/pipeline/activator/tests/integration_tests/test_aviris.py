import unittest 
from .utils import run_command


class AvirisTest(unittest.TestCase):
    def test_l1(self):
        cmd = [
            'python', '-m', 'activator.aviris.main',
            '--aviris-stac-id', 'aviris_f130329t01p00r06_sc01'
        ]
        retcode = run_command(cmd)
        self.assertEqual(retcode, 0)


if __name__ == '__main__':
    unittest.main()