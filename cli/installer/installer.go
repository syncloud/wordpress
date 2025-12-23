package installer

import (
	"fmt"
	"os"
	"path"
	"strings"

	cp "github.com/otiai10/copy"
	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const App = "wordpress"

type Variables struct {
	App              string
	AppDir           string
	DataDir          string
	CommonDir        string
	AppKey           string
	AppUrl           string
	Domain           string
	AuthUrl          string
	AuthClientId     string
	AuthClientSecret string
	AuthRedirectUri  string
}

type Installer struct {
	newVersionFile     string
	currentVersionFile string
	configDir          string
	platformClient     *platform.Client
	database           *Database
	installFile        string
	appDir             string
	dataDir            string
	commonDir          string
	artisanPath        string
	executor           *Executor
	logger             *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	configDir := path.Join(dataDir, "config")
	executor := NewExecutor(logger)
	artisanPath := path.Join(appDir, "/bin/artisan.sh")
	return &Installer{
		newVersionFile:     path.Join(appDir, "version"),
		currentVersionFile: path.Join(dataDir, "version"),
		configDir:          configDir,
		platformClient:     platform.New(),
		database:           NewDatabase(App, appDir, dataDir, configDir, App, executor, logger),
		installFile:        path.Join(dataDir, "installed"),
		appDir:             appDir,
		dataDir:            dataDir,
		commonDir:          commonDir,
		executor:           executor,
		artisanPath:        artisanPath,
		logger:             logger,
	}
}

func (i *Installer) Install() error {
	err := CreateUser(App)
	if err != nil {
		return err
	}

	err = i.UpdateConfigs()
	if err != nil {
		return err
	}

	err = i.database.Init()
	if err != nil {
		return err
	}

	err = cp.Copy(
		path.Join(i.appDir, "php", "wordpress", "wp-content.template"),
		path.Join(i.commonDir, "wp-content"))
	if err != nil {
		return err
	}

	err = i.FixPermissions()
	if err != nil {
		return err
	}

	err = i.StorageChange()
	if err != nil {
		return err
	}
	return nil
}

func (i *Installer) Configure() error {
	if i.IsInstalled() {
		err := i.Upgrade()
		if err != nil {
			return err
		}
	} else {
		err := i.Initialize()
		if err != nil {
			return err
		}
	}

	err := i.DomainChange()
	if err != nil {
		return err
	}

	return i.UpdateVersion()
}

func (i *Installer) DomainChange() error {
	appUrl, err := i.platformClient.GetAppUrl(App)
	if err != nil {
		return err
	}
	err = i.wpCli("option", "update", "siteurl", appUrl)
	if err != nil {
		return err
	}
	err = i.wpCli("option", "update", "home", appUrl)
	if err != nil {
		return err
	}
	return nil
	//self._wp_cli("search-replace 'http://{0}' '{1}'".format(app_domain, app_url))
}

func (i *Installer) Initialize() error {
	err := i.StorageChange()
	if err != nil {
		return err
	}

	err = i.database.createDb()
	if err != nil {
		return err
	}

	appDomain, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}
	err = i.wpCli("core", "install", fmt.Sprint("--url=", appDomain), "--title=Syncloud", "--admin_user=installer", "--admin_email=admin@example.com", "--skip-email")
	if err != nil {
		return err
	}
	err = i.wpCli("user", "delete", "installer", "--yes")
	if err != nil {
		return err
	}
	err = i.updateSettings()
	if err != nil {
		return err
	}

	err = i.wpCli("option", "update", "mo_tour_skipped", "1")
	if err != nil {
		return err
	}

	err = os.WriteFile(i.installFile, []byte("installed"), 0644)
	if err != nil {
		return err
	}

	return nil
}

func (i *Installer) wpCli(args ...string) error {
	full := append([]string{"run", "wordpress.wp-cli"}, args...)
	_, err := i.executor.Run("snap", full...)
	return err
}

func (i *Installer) updateSettings() error {
	cmds := [][]string{
		{"option", "update", "mo_ldap_local_register_user", "1"},
		{"option", "update", "mo_ldap_local_mapping_memberof_attribute", "memberOf"},
		{"option", "update", "mo_ldap_local_new_registration", "true"},
		{"option", "update", "mo_ldap_local_enable_admin_wp_login", "1"},
		{"option", "update", "mo_ldap_local_anonymous_bind", "0"},
		{"option", "update", "mo_ldap_local_server_url", "ldap://localhost"},
		{"option", "update", "mo_ldap_local_server_dn", "dc=syncloud,dc=org"},
		{"option", "update", "mo_ldap_local_server_password", "syncloud"},
		{"option", "update", "mo_ldap_local_search_filter", "(&(objectClass=*)(cn=?))"},
		{"option", "update", "mo_ldap_local_search_base", "ou=users,dc=syncloud,dc=org"},
		{"option", "update", "mo_ldap_local_enable_role_mapping", "1"},
		{"option", "update", "mo_ldap_local_enable_login", "1"},
		{"option", "update", "mo_ldap_local_server_url_status", "VALID"},
		{"option", "update", "mo_ldap_local_service_account_status", "VALID"},
		{"option", "update", "mo_ldap_local_user_mapping_status", "VALID"},
		{"option", "update", "mo_ldap_local_mapping_value_default", "administrator"},
	}
	for _, c := range cmds {
		if err := i.wpCli(c...); err != nil {
			return err
		}
	}
	_ = i.wpCli("plugin", "auto-updates", "disable", "--all")
	return nil
}

func (i *Installer) Upgrade() error {
	err := i.database.createDb()
	if err != nil {
		return err
	}
	err = i.database.Restore()
	if err != nil {
		return err
	}
	err = i.StorageChange()
	if err != nil {
		return err
	}

	return nil
}

func (i *Installer) IsInstalled() bool {
	_, err := os.Stat(i.installFile)
	return err == nil
}

func (i *Installer) PreRefresh() error {
	return i.database.Backup()
}

func (i *Installer) PostRefresh() error {
	backupFile := path.Join(i.dataDir, "database.dump")
	_, err := os.Stat(backupFile)
	if err != nil {
		err = cp.Copy(
			path.Join(i.commonDir, "database.dump"),
			backupFile,
		)
		if err != nil {
			return err
		}
	}

	err = i.UpdateConfigs()
	if err != nil {
		return err
	}
	err = i.database.Remove()
	if err != nil {
		return err
	}
	err = i.database.Init()
	if err != nil {
		return err
	}

	pluginDir := path.Join(i.dataDir, "wp-content", "plugins", "ldap-login-for-intranet-sites")
	err = os.RemoveAll(pluginDir)
	if err != nil {
		return err
	}

	err = cp.Copy(
		path.Join(i.appDir, "php", "wordpress", "wp-content.template", "mu-plugins"),
		path.Join(i.commonDir, "wp-content", "mu-plugins"),
	)
	if err != nil {
		return err
	}

	err = i.ClearVersion()
	if err != nil {
		return err
	}

	err = i.FixPermissions()
	if err != nil {
		return err
	}
	return nil
}

func (i *Installer) StorageChange() error {
	storageDir, err := i.platformClient.InitStorage(App, App)
	if err != nil {
		return err
	}

	err = Chown(storageDir, App)
	if err != nil {
		return err
	}
	return nil
}

func (i *Installer) ClearVersion() error {
	return os.RemoveAll(i.currentVersionFile)
}

func (i *Installer) UpdateVersion() error {
	return cp.Copy(i.newVersionFile, i.currentVersionFile)
}

func (i *Installer) UpdateConfigs() error {
	err := linux.CreateMissingDirs(
		path.Join(i.dataDir, "nginx"),
		path.Join(i.dataDir, "temp"),
	)
	if err != nil {
		return err
	}

	err = Chown(i.dataDir, App)
	if err != nil {
		return err
	}

	variables := Variables{
		App:       App,
		AppDir:    i.appDir,
		DataDir:   i.dataDir,
		CommonDir: i.commonDir,
	}

	err = config.Generate(
		path.Join(i.appDir, "config"),
		path.Join(i.dataDir, "config"),
		variables,
	)
	if err != nil {
		return err
	}

	return nil
}

func (i *Installer) BackupPreStop() error {
	return i.PreRefresh()
}

func (i *Installer) RestorePreStart() error {
	return i.PostRefresh()
}

func (i *Installer) RestorePostStart() error {
	return i.Configure()
}

func (i *Installer) AccessChange() error {
	err := i.DomainChange()
	if err != nil {
		return err
	}
	return i.UpdateConfigs()
}

func (i *Installer) FixPermissions() error {
	err := Chown(i.dataDir, App)
	if err != nil {
		return err
	}
	err = Chown(i.commonDir, App)
	if err != nil {
		return err
	}
	return nil
}

func (i *Installer) getOrCreateAppKey() (string, error) {
	file := path.Join(i.dataDir, ".app_key")
	_, err := os.Stat(file)
	if os.IsNotExist(err) {
		secret, err := i.executor.Run(i.artisanPath, "key:generate", "--show")
		if err != nil {
			return "", err
		}
		err = os.WriteFile(file, []byte(strings.TrimSpace(secret)), 0644)
		return secret, err
	}
	content, err := os.ReadFile(file)
	if err != nil {
		return "", err
	}
	return string(content), nil
}
