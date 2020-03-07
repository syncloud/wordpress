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
from syncloudlib.integration.hosts import add_host_alias_by_ip
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

        device.run_ssh('top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR))
        device.run_ssh('ps auxfw > {0}/ps.log'.format(TMP_DIR))
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(TMP_DIR))
        device.run_ssh('journalctl > {0}/journalctl.log'.format(TMP_DIR))
        device.run_ssh('cp /var/log/syslog {0}/syslog.log'.format(TMP_DIR))
        device.run_ssh('cp /var/snap/wordpress/common/database/*.err {0}/'.format(TMP_DIR), throw=False)
        device.run_ssh('cp /var/log/messages {0}/messages.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la {0}/ > {1}/app.ls.log'.format(app_dir, TMP_DIR), throw=False)    
        device.run_ssh('ls -la /var/snap/wordpress/common/ > {0}/data.ls.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la /var/snap/wordpress/common/wp-content/ > {0}/data.wp-content.ls.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la /var/snap/wordpress/common/database/ > {0}/database.ls.log'.format(TMP_DIR), throw=False)    
        device.run_ssh('ls -la {0}/wordpress/ > {1}/wordpress.ls.log'.format(app_dir, TMP_DIR), throw=False)  
        device.run_ssh('ls -la {0}/wp-content.template/ > {0}/wp-content.template.ls.log'.format(app_dir, TMP_DIR), throw=False)  
        device.run_ssh('ls -la /var/snap/wordpress/common/log/ > {0}/log.ls.log'.format(TMP_DIR), throw=False)  
        device.run_ssh('{0}/bin/wp-cli core is-installed; echo "is installed: $?" > {1}/wp-cli.isinstalled.log'.format(app_dir, TMP_DIR), env_vars='SNAP_COMMON={0}'.format(data_dir), throw=False)
        device.run_ssh('{0}/bin/wp-cli option list > {1}/wp-cli.options.log'.format(app_dir, TMP_DIR), env_vars='SNAP_COMMON={0}'.format(data_dir), throw=False)
        device.run_ssh('{0}/bin/wp-cli --info > {1}/wp-cli.info.log 2>&1'.format(app_dir, TMP_DIR), env_vars='SNAP_COMMON={0}'.format(data_dir), throw=False)  
        device.run_ssh('{0}/bin/wp-cli user list > {1}/wp-cli.user.list.log 2>&1'.format(app_dir, TMP_DIR), env_vars='SNAP_COMMON={0}'.format(data_dir), throw=False)  

        app_log_dir  = join(artifact_dir, 'log')
        os.mkdir(app_log_dir )
        device.scp_from_device('{0}/log/*.log'.format(data_dir), app_log_dir)
        device.scp_from_device('{0}/*'.format(TMP_DIR), app_log_dir)
    
    request.addfinalizer(module_teardown)


def test_start(module_setup, device, device_host, app, domain):
    add_host_alias_by_ip(app, domain, device_host)
    device.run_ssh('date', retries=100)
    device.run_ssh('mkdir {0}'.format(TMP_DIR))


def test_activate_device(device):
    response = device.activate()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_session, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, device_host)


def test_phpinfo(device, app_dir, data_dir, device_password):
    device.run_ssh('{0}/bin/php -i > {1}/log/phpinfo.log'.format(app_dir, data_dir),
            env_vars='SNAP_COMMON={0}'.format(data_dir))


def test_index(app_domain):
    response = requests.get('https://{0}'.format(app_domain), verify=False)                          
    assert response.status_code == 200, response.text


#def test_storage_change(device_host, app_dir, data_dir, device_password):
#    device.run_ssh('SNAP_COMMON={1} {0}/hooks/storage-change > {1}/log/storage-change.log'.format(app_dir, data_dir), password=device_password, throw=False)

def test_upgrade(app_archive_path, device_host, device_password, device_session):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, device_host)

def test_remove(device, app):
    response = device.app_remove(app)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)
