import os
import shutil
from os.path import dirname, join, exists
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.screenshots import screenshots


DIR = dirname(__file__)


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode, artifact_dir):
    def module_teardown():
        tmp_dir = '/tmp/syncloud/ui'
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(tmp_dir), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(tmp_dir, ui_mode), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(tmp_dir, ui_mode), throw=False)
      
        device.scp_from_device('{0}/*'.format(tmp_dir), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, domain, device_host):
    add_host_alias_by_ip(app, domain, device_host)
    

def test_index(driver, app_domain, screenshot_dir):

    driver.get("https://{0}".format(app_domain))
    time.sleep(10)
  
    screenshots(driver, screenshot_dir, 'index')
    

def test_login(driver, app_domain, device_user, device_password, screenshot_dir):

    driver.get("https://{0}/wp-login.php".format(app_domain))
    wait_driver = WebDriverWait(driver, 120)
    wait_driver.until(EC.element_to_be_clickable((By.ID, 'user_login')))

    user = driver.find_element_by_id("user_login")
    user.send_keys(device_user)
    password = driver.find_element_by_id("user_pass")
    password.send_keys(device_password)
    screenshots(driver, screenshot_dir, 'login')
    password.send_keys(Keys.RETURN)
    
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'login-complete')
    

def test_admin(driver, app_domain, screenshot_dir):

    driver.get("https://{0}/wp-admin".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin')
    

def test_profile(driver, app_domain, screenshot_dir):

    driver.get("https://{0}/wp-admin/profile.php".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'profile')
    

def test_ldap(driver, app_domain, screenshot_dir):

    driver.get("https://{0}/wp-admin/admin.php?page=mo_ldap_local_login".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'ldap')

    
def test_users(driver, app_domain, screenshot_dir):

    driver.get("https://{0}/wp-admin/users.php".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'users')
    
def test_media(driver, app_domain, screenshot_dir):

    driver.get("https://{0}/wp-admin/media-new.php".format(app_domain))
    time.sleep(2)
    driver.find_element_by_css_selector('p[class="upload-flash-bypass"] a').click()
    file = driver.find_element_by_css_selector('input[id="async-upload"][type="file"]')
    file.send_keys(join(DIR, 'images', 'profile.jpeg'))
    time.sleep(2)
    screenshots(driver, screenshot_dir, 'media')
    save = driver.find_element_by_css_selector('input[id="html-upload"][type="submit"]')
    save.click()
    time.sleep(5)
    screenshots(driver, screenshot_dir, 'media-done')
