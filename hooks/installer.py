import logging
from os.path import isdir, join, isfile
from subprocess import check_output
import subprocess
import shutil
from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage
from subprocess import check_output, CalledProcessError

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
        self.common_dir = paths.get_data_dir(APP_NAME)
        self.data_dir = join('/var/snap', APP_NAME, 'current')
        self.config_dir = join(self.data_dir, 'config')
        self.app_domain = urls.get_app_domain_name(APP_NAME)
        self.app_url = urls.get_app_url(APP_NAME)
           
        self.database_path = join(self.app_data_dir, 'database')
             
    def install_config(self):

        home_folder = join('/home', USER_NAME)
        linux.useradd(USER_NAME, home_folder=home_folder)
        
        fs.makepath(join(self.app_data_dir, 'log'))
        fs.makepath(join(self.app_data_dir, 'nginx'))
        fs.makepath(join(self.app_data_dir, 'temp'))
        
        storage.init_storage(APP_NAME, USER_NAME)

        templates_path = join(self.app_dir, 'config')
        
        variables = {
            'app': APP_NAME,
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir,
            'data_dir': self.data_dir
        }
        gen.generate_files(templates_path, self.config_dir, variables)

    def install(self):
        self.install_config()
        self.database_init()
        
        shutil.copytree(
            join(self.app_dir, 'php', 'wordpress', 'wp-content.template'),
            join(self.app_data_dir, 'wp-content'))
            
        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)
        fs.chownpath(self.data_dir, USER_NAME, recursive=True)

    def refresh(self):
        self.install_config()
        shutil.rmtree(
            join(self.app_data_dir, 'wp-content', 'plugins', 'ldap-login-for-intranet-sites'),
            ignore_errors=True)
        shutil.copytree(
            join(self.app_dir, 'php', 'wordpress', 'wp-content.template', 'mu-plugins'),
            join(self.app_data_dir, 'wp-content', 'mu-plugins'),
            dirs_exist_ok=True)

        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)
        fs.chownpath(self.data_dir, USER_NAME, recursive=True)

    def configure(self):
        self.prepare_storage()
        install_file = join(self.app_data_dir, 'installed')
        if not isfile(install_file):
            self.execute_sql('CREATE DATABASE {0};'.format(DB_NAME))
            self.execute_sql('GRANT ALL PRIVILEGES ON {0}.* TO "{1}"@"localhost" IDENTIFIED BY "{2}";'.format(
                DB_NAME, DB_USER, DB_PASSWORD))
            self.execute_sql('FLUSH PRIVILEGES;')
            self._wp_cli('core install --url={0} --title=Syncloud --admin_user=installer --admin_email=admin@example.com --skip-email'.format(self.app_domain))
            # self._wp_cli('plugin activate ldap-login-for-intranet-sites')
            self._wp_cli('user delete installer --yes')
            self.update_settings()
            self._wp_cli("option update mo_tour_skipped 1")
            fs.touchfile(install_file)
        else:
            self._wp_cli("core update-db")
            self.update_settings()

        self.on_domain_change()

    def update_settings(self):
        self._wp_cli("option update mo_ldap_local_register_user 1")
        self._wp_cli("option update mo_ldap_local_mapping_memberof_attribute memberOf")
        self._wp_cli("option update mo_ldap_local_new_registration true")
        self._wp_cli("option update mo_ldap_local_enable_admin_wp_login 1")
        self._wp_cli("option update mo_ldap_local_anonymous_bind 0")
        self._wp_cli("option update mo_ldap_local_server_url ldap://localhost")
        self._wp_cli("option update mo_ldap_local_server_dn dc=syncloud,dc=org")
        self._wp_cli("option update mo_ldap_local_server_password syncloud")
        self._wp_cli("option update mo_ldap_local_search_filter '(&(objectClass=*)(cn=?))'")
        self._wp_cli("option update mo_ldap_local_search_base ou=users,dc=syncloud,dc=org")
        self._wp_cli("option update mo_ldap_local_enable_role_mapping 1")
        self._wp_cli("option update mo_ldap_local_enable_login 1")
        self._wp_cli("option update mo_ldap_local_server_url_status VALID")
        self._wp_cli("option update mo_ldap_local_service_account_status VALID")
        self._wp_cli("option update mo_ldap_local_user_mapping_status VALID")
        self._wp_cli("option update mo_ldap_local_mapping_value_default administrator")
        self._wp_cli("plugin auto-updates disable --all", throw=False)
 
    def _wp_cli(self, cmd, throw=True):
        try:
            check_output('snap run wordpress.wp-cli {0}'.format(cmd), shell=True, stderr=subprocess.STDOUT)
        except CalledProcessError as e:
            self.log.error(e.output.decode())
            if throw:
                raise e
     
    def on_disk_change(self):
        self.prepare_storage()
        
    def prepare_storage(self):
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
        
    def on_domain_change(self):   
        self._wp_cli("option update siteurl '{0}'".format(self.app_url))
        self._wp_cli("option update home '{0}'".format(self.app_url))
        #self._wp_cli("search-replace 'http://{0}' '{1}'".format(app_domain, app_url))
        
    def execute_sql(self, sql):
        try:
            check_output('{0}/mariadb/usr/bin/mysql --socket={1}/mysql.sock -e \'{2}\''.format(
                self.app_dir, self.app_data_dir, sql), shell=True, stderr=subprocess.STDOUT)
        except CalledProcessError as e:
            self.log.error(e.output.decode())
            raise e

    def database_init(self):
        
        initdb_cmd = '{0}/bin/initdb.sh --user={1} --basedir={0}/mariadb/usr --datadir={2}'.format(
            self.app_dir, DB_USER, self.database_path)
        try:
            check_output(initdb_cmd, shell=True, stderr=subprocess.STDOUT)
        except CalledProcessError as e:
            self.log.error(e.output.decode())
            raise e
