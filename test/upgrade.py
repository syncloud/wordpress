import pytest
import requests
from subprocess import check_output
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install
from syncloudlib.http import wait_for_rest

TMP_DIR = '/tmp/syncloud'
POST_TITLE = 'syncloud title'
POST_BODY = 'syncloud paragraph'
BEFORE = {}


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/refresh.journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('snap run wordpress.wp-cli core version > {0}/wp.version.log 2>&1'.format(TMP_DIR),
                       throw=False)
        device.run_ssh('snap run wordpress.wp-cli plugin list > {0}/wp.plugins.log 2>&1'.format(TMP_DIR),
                       throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir, throw=False)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def wp(device, args):
    return device.run_ssh('snap run wordpress.wp-cli {0}'.format(args))


def test_start(module_setup, app, device_host, domain, device, settle):
    add_host_alias(app, device_host, domain)
    device.activated()
    settle(device)
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)


def test_record_state_before_upgrade(device):
    BEFORE['version'] = wp(device, 'core version').strip()
    BEFORE['posts'] = wp(device, 'post list --format=csv --fields=post_title')
    BEFORE['users'] = wp(device, 'user list --format=csv --fields=user_login')
    print('before upgrade: {0}'.format(BEFORE))
    assert POST_TITLE in BEFORE['posts'], BEFORE['posts']


def test_upgrade(device_host, device_password, app_archive_path, app_domain):
    local_install(device_host, device_password, app_archive_path)
    wait_for_rest(requests.session(), "https://{0}".format(app_domain), 200, 100)


def test_core_version_moved(device):
    after = wp(device, 'core version').strip()
    print('wordpress {0} -> {1}'.format(BEFORE['version'], after))
    assert after != '', after


def test_database_is_current(device):
    out = wp(device, 'core check-update --format=csv')
    assert 'Error' not in out, out
    status = wp(device, 'core is-installed && echo installed')
    assert 'installed' in status, status


def test_post_survived(device):
    posts = wp(device, 'post list --format=csv --fields=post_title')
    print('after upgrade posts: {0}'.format(posts))
    assert POST_TITLE in posts, posts


def test_users_survived(device):
    users = wp(device, 'user list --format=csv --fields=user_login')
    assert users.strip() == BEFORE['users'].strip(), (BEFORE['users'], users)


def test_ldap_plugin_active(device):
    plugins = wp(device, 'plugin list --format=csv')
    assert 'ldap' in plugins.lower(), plugins


def test_no_php_fatals(device):
    log = device.run_ssh('journalctl --no-pager | tail -2000')
    assert 'PHP Fatal error' not in log, [l for l in log.split('\n') if 'PHP Fatal' in l][:5]
