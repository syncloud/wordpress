package installer

import (
	"os"
	"path"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/syncloud/golib/config"
)

func TestConfigGenerationUsesOnlyDeclaredVariables(t *testing.T) {
	appDir := t.TempDir()
	dataDir := t.TempDir()

	source := path.Join(appDir, "config", "wordpress")
	assert.NoError(t, os.MkdirAll(source, 0755))
	assert.NoError(t, os.WriteFile(
		path.Join(source, "wp-config.php"),
		[]byte("app={{ .App }} appdir={{ .AppDir }} datadir={{ .DataDir }} commondir={{ .CommonDir }}"),
		0644))

	variables := Variables{
		App:       App,
		AppDir:    appDir,
		DataDir:   dataDir,
		CommonDir: "/var/snap/wordpress/common",
	}
	assert.NoError(t, config.Generate(path.Join(appDir, "config"), path.Join(dataDir, "config"), variables))

	body, err := os.ReadFile(path.Join(dataDir, "config", "wordpress", "wp-config.php"))
	assert.NoError(t, err)
	assert.Equal(t,
		"app=wordpress appdir="+appDir+" datadir="+dataDir+" commondir=/var/snap/wordpress/common",
		string(body))
}

func TestDatabaseDirIsUnderDataDir(t *testing.T) {
	dataDir := t.TempDir()
	db := NewDatabase(App, "", dataDir, "", App, nil, nil)
	assert.Equal(t, path.Join(dataDir, "database"), db.DatabaseDir())
}
