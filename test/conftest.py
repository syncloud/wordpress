from os.path import dirname

from syncloudlib.integration.conftest import *

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def project_dir():
    return join(DIR, '..')


@pytest.fixture(scope="session")
def settle():
    def hold_snapd(device):
        device.run_ssh('snap wait system seed.loaded', retries=100, throw=False)
        device.run_ssh('snap set system refresh.hold=2099-01-01T00:00:00Z', retries=20, throw=False)
        device.run_ssh('snap abort --last=auto-refresh', throw=False)
        device.run_ssh('snap watch --last=auto-refresh', throw=False)

    return hold_snapd
