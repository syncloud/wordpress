import json
import os
import sys
from os import listdir
from os.path import dirname, join, exists, abspath, isdir
import time
from subprocess import check_output
import pytest
import shutil

from syncloudlib.integration.installer import local_install, local_remove, wait_for_installer
from syncloudlib.integration.loop import loop_device_cleanup
from syncloudlib.integration.ssh import run_scp, run_ssh
from syncloudlib.http import wait_for_rest
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration import conftest

import requests


DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def module_setup(request, device, platform_data_dir, app_dir, artifact_dir, data_dir):
    def module_teardown():
        platform_log_dir = join(artifact_dir, 'platform_log')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        
        device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False) 
        device.run_ssh('top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR))
        device.run_ssh('ps auxfw > {0}/ps.log'.format(TMP_DIR))
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(TMP_DIR))
        device.run_ssh('journalctl > {0}/journalctl.log'.format(TMP_DIR))
        device.run_ssh('ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la {0}/ > {1}/app.ls.log'.format(app_dir, TMP_DIR), throw=False)    
        device.run_ssh('ls -la {0}/wordpress/ > {1}/wordpress.ls.log'.format(app_dir, TMP_DIR), throw=False)  
        device.run_ssh('ls -la {0}/wp-content.template/ > {1}/wp-content.template.ls.log'.format(app_dir, TMP_DIR), throw=False)  
        device.run_ssh('{0}/bin/wp-cli core is-installed; echo "is installed: $?" > {1}/wp-cli.isinstalled.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('{0}/bin/wp-cli option list > {1}/wp-cli.options.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('{0}/bin/wp-cli user list > {1}/wp-cli.user.list.log 2>&1'.format(app_dir, TMP_DIR), throw=False)  

        app_log_dir  = join(artifact_dir, 'log')
        os.mkdir(app_log_dir )
        device.scp_from_device('{0}/log/*.log'.format(data_dir), app_log_dir)
        device.scp_from_device('{0}/*'.format(TMP_DIR), app_log_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device, app, domain, device_host, settle):
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100, throw=True)
    settle(device)
    device.run_ssh('mkdir {0}'.format(TMP_DIR))


def test_activate_device(device):
    response = device.activate_custom()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_session, device_host, device_password, domain, app_domain):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, domain)
    wait_for_rest(requests.session(), 'https://{0}'.format(app_domain), 200, 100)


def test_phpinfo(device, app_dir, data_dir, device_password):
    device.run_ssh('snap run wordpress.php -i > {0}/phpinfo.log'.format(TMP_DIR))


def test_index(app_domain):
    response = requests.get('https://{0}'.format(app_domain), verify=False)                          
    assert response.status_code == 200, response.text


def test_storage_change_event(device):
    device.run_ssh('snap run wordpress.storage-change > {0}/storage-change.log'.format(TMP_DIR))


def test_access_change_event(device):
    device.run_ssh('snap run wordpress.access-change > {0}/access-change.log'.format(TMP_DIR))


def test_upgrade(app_archive_path, device_host, device_password, device_session, domain):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, domain)
