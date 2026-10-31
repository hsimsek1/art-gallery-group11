""" 
Run: BREAKIT_BASE_URL=http://127.0.0.1:5678 BREAKIT_PROBE_PATH=/admin \
     BREAKIT_EXPECTED_STATUS=403 python -m unittest tests.breakit.test_candidate_access_control

Check an unauthenticated request. Depending on the target's auth
contract, the expected status may be 302 (redirect) or 401 rather than 403.
"""
import os
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class CandidateAccessControl(unittest.TestCase):
    def test_unauthenticated_protected_route(self):
        base = os.environ.get('BREAKIT_BASE_URL', '')
        path = os.environ.get('BREAKIT_PROBE_PATH', '')
        expected = os.environ.get('BREAKIT_EXPECTED_STATUS', '')
        if not base or not path or not expected:
            self.skipTest('No assigned peer target/harness configured; not a verified break')
        if not path.startswith('/'):
            self.fail('BREAKIT_PROBE_PATH must be an absolute path')
        if not base.startswith(('http://127.0.0.1:', 'http://localhost:')):
            self.fail('For safety, candidate runner permits only local test servers')
        try:
            with urlopen(base.rstrip('/') + path, timeout=5) as response:
                actual = response.status
        except HTTPError as error:
            actual = error.code
        except URLError as error:
            self.fail(f'Could not contact local assigned target: {error}')
        self.assertEqual(actual, int(expected),
                         'Behavior differs from the specified expected status; '
                         'investigate and record exact impact before reporting')


if __name__ == '__main__':
    unittest.main()
