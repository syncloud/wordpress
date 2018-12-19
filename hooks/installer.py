from os.path import dirname, join, abspath, isdir, realpath
from os import listdir
import sys

from os import environ
from os.path import isfile
import shutil
import uuid
from subprocess import check_output

import logging

from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage, users, service

from subprocess import check_output
from os.path import join


APP_NAME = 'wordpress'

USER_NAME = APP_NAME
DB_NAME = APP_NAME
DB_USER = APP_NAME
DB_PASSWORD = APP_NAME

SYSTEMD_NGINX_NAME = '{0}.nginx'.format(APP_NAME)
SYSTEMD_PHP_FPM_NAME = '{0}.php-fpm'.format(APP_NAME) 


class Installer:
    def __init__(self):
        if not logger.factory_instance:
            logger.init(logging.DEBUG, True)

        self.log = logger.get_logger('{0}_installer'.format(APP_NAME))
        self.app_dir = paths.get_app_dir(APP_NAME)
        self.app_data_dir = paths.get_data_dir(APP_NAME)

        self.database_path = join(self.app_data_dir, 'database')
             
    def install_config(self):

        home_folder = join('/home', USER_NAME)
        linux.useradd(USER_NAME, home_folder=home_folder)
        
        fs.makepath(join(self.app_data_dir, 'log'))
        fs.makepath(join(self.app_data_dir, 'nginx'))
        
        storage.init_storage(APP_NAME, USER_NAME)

        templates_path = join(self.app_dir, 'config.templates')
        config_path = join(self.app_data_dir, 'config')
                   
        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir
        }
        gen.generate_files(templates_path, config_path, variables)

        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)

    def install(self):
        self.install_config()
        self.database_init()
        
    def configure(self):
        self.prepare_storage()
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
  
    def on_disk_change(self):
        self.prepare_storage()
        
    def prepare_storage(self):
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
        
    def on_domain_change(self):
        app_domain = urls.get_app_domain_name(APP_NAME)
        
    def database_init(self):
        
        if not isdir(self.database_path):
            initdb_cmd = '{0}/mariadb/scripts/mysql_install_db --user={1} --basedir={0}/mariadb --datadir={2}'.format(self.app_dir, DB_USER, self.database_path)
            check_output(initdb_cmd, shell=True)
        else:
            self.logger.info('Database path "{0}" already exists'.format(self.database_path))


