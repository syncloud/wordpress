import logging
from os.path import isdir, join, isfile
from subprocess import check_output

from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage

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
            'app': APP_NAME,
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir
        }
        gen.generate_files(templates_path, config_path, variables)

    def install(self):
        self.install_config()
        self.database_init()
        
        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)

    def configure(self):
        self.prepare_storage()
        install_file = join(self.app_data_dir, 'installed')
        if not isfile(install_file):
            self.execute_sql('CREATE DATABASE {0};'.format(DB_NAME))
            self.execute_sql('GRANT ALL PRIVILEGES ON {0}.* TO "{1}"@"localhost" IDENTIFIED BY "{2}";'.format(
                DB_NAME, DB_USER, DB_PASSWORD))
            self.execute_sql('FLUSH PRIVILEGES;')
            
            app_url = urls.get_app_url(APP_NAME)
            self._wp_cli('core install --url={0} --title=Syncloud --admin_user=admin --admin_password=admon --admin_email=info@example.com'.format(app_url))
                
            self.on_domain_change()
            
            fs.touchfile(install_file)
            
        # else:
            # upgrade
    
    def _wp_cli(self, cmd):
        check_output('sudo -H -E -u {0} {1}/bin/wp-cli {2}'.format(
            USER_NAME, self.app_dir, cmd), shell=True)
             
    
    def on_disk_change(self):
        self.prepare_storage()
        
    def prepare_storage(self):
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
        
    def on_domain_change(self):
        app_url = urls.get_app_url(APP_NAME)
        self._wp_cli('option update siteurl {0}'.format(app_url))
        self._wp_cli('option update home {0}'.format(app_url))
             
    def execute_sql(self, sql):
        check_output('{0}/mariadb/bin/mysql --socket={1}/mysql.sock -e \'{2}\''.format(
            self.app_dir, self.app_data_dir, sql), shell=True)
          
    def database_init(self):
        
        if not isdir(self.database_path):
            initdb_cmd = '{0}/mariadb/scripts/mysql_install_db --user={1} --basedir={0}/mariadb --datadir={2}'.format(
                self.app_dir, DB_USER, self.database_path)
            check_output(initdb_cmd, shell=True)
            
        else:
            self.log.info('Database path "{0}" already exists'.format(self.database_path))


