package installer

import (
	"fmt"
	cp "github.com/otiai10/copy"
	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
	"os"
	"path"
	"strings"
	"time"
)

const App = "wordpress"

type Variables struct {
	App          string
	AppDir       string
	DataDir      string
	CommonDir    string
	AuthUrl      string
	AuthHost     string
	AuthLocalUrl string
	OIDCSecret   string
}

type Installer struct {
	newVersionFile     string
	currentVersionFile string
	configDir          string
	platformClient     *platform.Client
	database           *Database
	installFile        string
	oidcSecretFile     string
	appDir             string
	dataDir            string
	commonDir          string
	executor           *Executor
	logger             *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	configDir := path.Join(dataDir, "config")
	executor := NewExecutor(logger)
	return &Installer{
		newVersionFile:     path.Join(appDir, "version"),
		currentVersionFile: path.Join(dataDir, "version"),
		configDir:          configDir,
		platformClient:     platform.New(),
		database:           NewDatabase(App, appDir, dataDir, configDir, App, executor, logger),
		installFile:        path.Join(dataDir, "installed"),
		oidcSecretFile:     path.Join(dataDir, ".oidc_secret"),
		appDir:             appDir,
		dataDir:            dataDir,
		commonDir:          commonDir,
		executor:           executor,
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

	err := i.database.WaitForDatabase(60 * time.Second)
	if err != nil {
		return err
	}

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

	err = i.RegisterOIDC()
	if err != nil {
		return err
	}

	err = i.UpdateConfigs()
	if err != nil {
		return err
	}

	err = i.DomainChange()
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

func (i *Installer) RegisterOIDC() error {
	secret, err := i.platformClient.RegisterOIDCClient(
		App,
		[]string{"/wp-admin/admin-ajax.php?action=openid-connect-authorize"},
		false,
		"client_secret_basic",
	)
	if err != nil {
		return err
	}
	return os.WriteFile(i.oidcSecretFile, []byte(secret), 0600)
}

func (i *Installer) oidcSecret() string {
	content, err := os.ReadFile(i.oidcSecretFile)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(content))
}

func (i *Installer) Upgrade() error {
	/* enable after the next release when we have a db backup working
	err := i.database.createDb()
		if err != nil {
			return err
		}
		err = i.database.Restore()
		if err != nil {
			return err
		}
	*/

	err := i.wpCli("core", "update-db")
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
	// migrate from common status, remove after the next release
	old := path.Join(i.commonDir, "installed")
	_, err := os.Stat(old)
	if err == nil {
		i.logger.Info("migrating old installed status")

		err = os.WriteFile(i.installFile, []byte("installed"), 0644)
		if err != nil {
			i.logger.Error("cannot migrate installed status", zap.Error(err))
			return true
		}
		return true
	}
	// migrate end

	_, err = os.Stat(i.installFile)
	return err == nil
}

func (i *Installer) PreRefresh() error {
	return i.database.Backup()
}

func (i *Installer) PostRefresh() error {

	err := i.UpdateConfigs()
	if err != nil {
		return err
	}
	/* enable after the next release when we have a db backup working
	 err = i.database.Remove()
		if err != nil {
			return err
		}
		err = i.database.Init()
		if err != nil {
			return err
		}
	*/

	// migrate from common database, remove after the next release
	databaseDir := path.Join(i.dataDir, "database")
	_, err = os.Stat(databaseDir)
	if err != nil {
		i.logger.Info("new db path is not foind, migrating", zap.Error(err))

		err = cp.Copy(
			path.Join(i.commonDir, "database"),
			databaseDir,
		)
		if err != nil {
			return err
		}

	}
	// migrate end

	stale := []string{
		path.Join(i.dataDir, "wp-content", "plugins", "ldap-login-for-intranet-sites"),
		path.Join(i.commonDir, "wp-content", "mu-plugins", "ldap-login-for-intranet-sites"),
		path.Join(i.commonDir, "wp-content", "mu-plugins", "ldap-login-for-intranet-sites.php"),
	}
	for _, dir := range stale {
		err = os.RemoveAll(dir)
		if err != nil {
			return err
		}
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

	authUrl, err := i.platformClient.GetAppUrl("auth")
	if err != nil {
		return err
	}

	authHost := strings.TrimPrefix(strings.TrimPrefix(authUrl, "https://"), "http://")

	variables := Variables{
		App:          App,
		AppDir:       i.appDir,
		DataDir:      i.dataDir,
		CommonDir:    i.commonDir,
		AuthUrl:      authUrl,
		AuthHost:     authHost,
		AuthLocalUrl: "http://127.0.0.1",
		OIDCSecret:   i.oidcSecret(),
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
