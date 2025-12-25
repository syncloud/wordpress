import time
from os.path import dirname, join
from subprocess import check_output
import requests
import pytest
from selenium.webdriver.common.by import By
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.screenshots import screenshots

from test import lib

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode, artifact_dir):
    def module_teardown():
        tmp_dir = '/tmp/syncloud/ui'
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(tmp_dir), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(tmp_dir, ui_mode), throw=False)
        device.scp_from_device('{0}/*'.format(tmp_dir), artifact_dir)
        check_output('cp /videos/* {0}'.format(artifact_dir), shell=True)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, domain, device_host):
    add_host_alias(app, device_host, domain)


@pytest.mark.flaky(retries=10, delay=5)
def test_visible_through_platform(app_domain):
    response = requests.get('https://{0}'.format(app_domain), verify=False)
    assert response.status_code == 200, response.text


@pytest.mark.flaky(retries=10, delay=5)
def test_index(selenium):
    selenium.open_app()
    selenium.find_by(By.XPATH, "//a[text()='Syncloud']")
    selenium.screenshot('index')
    

def test_login(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)
    

def test_profile(selenium):

    selenium.open_app("/wp-admin/profile.php")
    selenium.find_by(By.XPATH, "//h2[text()='Personal Options']")
    selenium.screenshot('profile')
    

def test_ldap(driver, app_domain, selenium):

    driver.get("https://{0}/wp-admin/admin.php?page=mo_ldap_local_login".format(app_domain))
    selenium.find_by(By.XPATH, '//h3[.="LDAP Connection Information"]')
    selenium.screenshot('ldap')

    
def test_users(driver, app_domain, selenium, device_user):

    selenium.open_app("/wp-admin/users.php")
    selenium.find_by(By.XPATH, f'//a[.="{device_user}"]')
    selenium.screenshot('users')
    
def test_media(driver, app_domain, selenium):

    selenium.open_app("/wp-admin/media-new.php")
    selenium.find_by(By.XPATH, '//h1[.="Upload New Media"]')
    selenium.screenshot('media')
    selenium.find_by(By.XPATH, '//button[.="browser uploader"]').click()
    file = selenium.find_by(By.CSS_SELECTOR, 'input[id="async-upload"][type="file"]')
    file.send_keys(join(DIR, 'images', 'profile.jpeg'))
    
    selenium.screenshot('media-uploader')
    selenium.find_by(By.CSS_SELECTOR, 'input[id="html-upload"][type="submit"]').click()
    
    selenium.screenshot('media-done')


def test_post(selenium):
    lib.post(selenium)
    lib.read(selenium)
