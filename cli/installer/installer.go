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
)

const App = "invoiceninja"

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

	_, err := i.executor.Run(i.artisanPath, "migrate", "--force")
	if err != nil {
		return err
	}
	_, err = i.executor.Run(i.artisanPath, "db:seed", "--force")
	if err != nil {
		return err
	}
	_, err = i.executor.Run(i.artisanPath, "cache:clear")
	if err != nil {
		return err
	}

	return i.UpdateVersion()
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

	err = os.WriteFile(i.installFile, []byte("installed"), 0644)
	if err != nil {
		return err
	}

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
	err := i.UpdateConfigs()
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
		path.Join(i.dataDir, "storage/framework/sessions"),
		path.Join(i.dataDir, "storage/framework/views"),
		path.Join(i.dataDir, "storage/framework/cache"),
	)
	if err != nil {
		return err
	}

	err = Chown(i.dataDir, App)
	if err != nil {
		return err
	}

	appKey, err := i.getOrCreateAppKey()
	if err != nil {
		return err
	}
	appUrl, err := i.platformClient.GetAppUrl(App)
	if err != nil {
		return err
	}

	domain, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}
	authUrl, err := i.platformClient.GetAppUrl("auth")
	if err != nil {
		return err
	}
	redirectUri := "/auth/authelia"
	password, err := i.platformClient.RegisterOIDCClient(App, redirectUri, false, "client_secret_post")
	if err != nil {
		return err
	}

	variables := Variables{
		App:              App,
		AppDir:           i.appDir,
		DataDir:          i.dataDir,
		CommonDir:        i.commonDir,
		AppKey:           appKey,
		AppUrl:           appUrl,
		Domain:           domain,
		AuthUrl:          authUrl,
		AuthClientId:     App,
		AuthClientSecret: password,
		AuthRedirectUri:  redirectUri,
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
