import time
from os.path import dirname, join
from subprocess import check_output

import pytest
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.screenshots import screenshots

from integration import lib

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


def test_index(selenium):
    selenium.open_app()
    selenium.find_by_xpath("//a[text()='Syncloud']")
    selenium.screenshot('index')
    

def test_login(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)
    

def test_profile(selenium):

    selenium.open_app("/wp-admin/profile.php")
    selenium.find_by_xpath("//h2[text()='Personal Options']")
    selenium.screenshot('profile')
    

def test_ldap(driver, app_domain, screenshot_dir, ui_mode):

    driver.get("https://{0}/wp-admin/admin.php?page=mo_ldap_local_login".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'ldap-' + ui_mode)

    
def test_users(driver, app_domain, screenshot_dir, ui_mode):

    driver.get("https://{0}/wp-admin/users.php".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'users-' + ui_mode)
    
def test_media(driver, app_domain, screenshot_dir, ui_mode):

    if ui_mode == "desktop":
        driver.get("https://{0}/wp-admin/media-new.php".format(app_domain))
        time.sleep(2)
        screenshots(driver, screenshot_dir, 'media-new-' + ui_mode)
        driver.find_element_by_css_selector('p[class="upload-flash-bypass"] a').click()
        file = driver.find_element_by_css_selector('input[id="async-upload"][type="file"]')
        file.send_keys(join(DIR, 'images', 'profile.jpeg'))
        time.sleep(2)
        screenshots(driver, screenshot_dir, 'media-' + ui_mode)
        save = driver.find_element_by_css_selector('input[id="html-upload"][type="submit"]')
        save.click()
        time.sleep(5)
        screenshots(driver, screenshot_dir, 'media-done-' + ui_mode)


def test_teardown(driver):
    driver.quit()
