import os

import unittest 
from .utils import run_command


class AvirisTest(unittest.TestCase):
    def test_l1(self):
        cwd = os.path.dirname(os.path.abspath(__file__))

        cmd = [
            'python', '-m', 'activator.aviris.main',
            '--pipeline-uri', os.path.join(cwd, 'data', 'pipeline-test.json')
        ]
        retcode = run_command(cmd)
        self.assertEqual(retcode, 0)


if __name__ == '__main__':
    unittest.main()