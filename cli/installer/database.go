package installer

import (
	"errors"
	"fmt"
	"go.uber.org/zap"
	"os"
	"os/exec"
	"path"
)

type Database struct {
	name          string
	appDir        string
	dataDir       string
	configPath    string
	user          string
	backupFile    string
	databaseDir   string
	oldSqliteFile string
	executor      *Executor
	logger        *zap.Logger
}

func NewDatabase(
	name string,
	appDir string,
	dataDir string,
	configPath string,
	user string,
	executor *Executor,
	logger *zap.Logger,
) *Database {
	return &Database{
		name:        name,
		appDir:      appDir,
		dataDir:     dataDir,
		configPath:  configPath,
		user:        user,
		backupFile:  path.Join(dataDir, "database.dump"),
		databaseDir: path.Join(dataDir, "database"),
		executor:    executor,
		logger:      logger,
	}
}

func (d *Database) DatabaseDir() string {
	return d.databaseDir
}

func (d *Database) Remove() error {

	if _, err := os.Stat(d.backupFile); errors.Is(err, os.ErrNotExist) {
		d.logger.Error("backup file does not exist", zap.String("file", d.backupFile))
		return err
	}

	_ = os.RemoveAll(d.databaseDir)
	return nil
}

func (d *Database) Init() error {
	cmd := exec.Command(
		fmt.Sprintf("%s/bin/initdb.sh", d.appDir),
		fmt.Sprintf("--user=%s", d.user),
		fmt.Sprintf("--basedir=%s/mariadb/usr", d.appDir),
		fmt.Sprintf("--datadir=%s", d.databaseDir),
	)
	out, err := cmd.CombinedOutput()
	d.logger.Info(cmd.String(), zap.ByteString("output", out))
	if err != nil {
		d.logger.Error(cmd.String(), zap.String("error", "failed to init database"))
	}
	return err
}

func (d *Database) Execute(sql string) error {
	_, err := d.executor.Run(fmt.Sprintf("%s/bin/mysql", d.appDir), "--execute", sql)
	return err
}

func (d *Database) ExecuteDb(db string, sql string) error {
	_, err := d.executor.Run(
		fmt.Sprintf("%s/bin/mysql", d.appDir),
		"--database", db,
		"--execute", sql,
	)
	return err
}

func (d *Database) Restore() error {
	return d.ExecuteDb(d.name, fmt.Sprintf("source %s", d.backupFile))
}

func (d *Database) Backup() error {
	_, err := d.executor.Run(
		fmt.Sprintf("%s/mariadb/usr/bin/mariadb-dump", d.appDir),
		App,
		fmt.Sprintf("--socket=%s/mysql.sock", d.dataDir),
		"--single-transaction",
		"--quick",
		fmt.Sprintf("--result-file=%s", d.backupFile),
	)
	return err
}

func (d *Database) createDb() error {
	err := d.Execute(fmt.Sprintf("CREATE DATABASE %s", App))
	if err != nil {
		return err
	}
	err = d.Execute(fmt.Sprintf("GRANT ALL PRIVILEGES ON %s.* TO \"%s\"@\"localhost\" IDENTIFIED BY \"%s\"", App, App, App))
	if err != nil {
		return err
	}
	err = d.Execute("FLUSH PRIVILEGES")
	if err != nil {
		return err
	}
	return nil
}

func (d *Database) ActivatePremium(email string) error {
	err := d.ExecuteDb(d.name,
		fmt.Sprintf(""+
			"INSERT INTO user_roles (role_uuid , user_uuid) VALUES ("+
			" (SELECT uuid FROM roles WHERE name=\"PRO_USER\" ORDER BY version DESC limit 1),"+
			" (SELECT uuid FROM users WHERE email=\"%s\")"+
			") ON DUPLICATE KEY UPDATE role_uuid = VALUES(role_uuid)", email))
	if err != nil {
		return err
	}
	err = d.ExecuteDb(d.name,
		fmt.Sprintf(""+
			"INSERT INTO user_subscriptions SET "+
			"uuid=UUID(), "+
			"plan_name=\"PRO_PLAN\", "+
			"ends_at=8640000000000000, "+
			"created_at=0, "+
			"updated_at=0, "+
			"user_uuid=(SELECT uuid FROM users WHERE email=\"%s\"), "+
			"subscription_id=1,"+
			" subscription_type=\"regular\"", email))
	if err != nil {
		return err
	}
	return nil
}
