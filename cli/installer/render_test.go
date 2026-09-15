package installer

import (
	"os"
	"path"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/syncloud/golib/config"
)

func TestWpConfigRendersValidOIDCUrls(t *testing.T) {
	appDir := t.TempDir()
	dataDir := t.TempDir()

	src := path.Join(appDir, "config", "wordpress")
	assert.NoError(t, os.MkdirAll(src, 0755))
	body, err := os.ReadFile("../../config/wordpress/wp-config.php")
	assert.NoError(t, err)
	assert.NoError(t, os.WriteFile(path.Join(src, "wp-config.php"), body, 0644))

	authUrl := "https://auth.example.com"
	authHost := "auth.example.com"
	vars := Variables{
		App: App, AppDir: appDir, DataDir: dataDir, CommonDir: "/common",
		AuthUrl: authUrl, AuthHost: authHost, AuthLocalUrl: "http://127.0.0.1",
		OIDCSecret: "s3cr3t",
	}
	assert.NoError(t, config.Generate(path.Join(appDir, "config"), path.Join(dataDir, "config"), vars))

	out, err := os.ReadFile(path.Join(dataDir, "config", "wordpress", "wp-config.php"))
	assert.NoError(t, err)
	rendered := string(out)

	for _, want := range []string{
		"define('OIDC_ISSUER', 'https://auth.example.com');",
		"define('OIDC_ENDPOINT_LOGIN_URL', 'https://auth.example.com/api/oidc/authorization');",
		"define('OIDC_ENDPOINT_TOKEN_URL', 'http://127.0.0.1/api/oidc/token');",
		"define('OIDC_ENDPOINT_USERINFO_URL', 'http://127.0.0.1/api/oidc/userinfo');",
		"define('OIDC_ENDPOINT_JWKS_URL', 'http://127.0.0.1/jwks.json');",
		"define('OIDC_CLIENT_SECRET', 's3cr3t');",
		"define('SYNCLOUD_AUTH_HOST', 'auth.example.com');",
		"define('SYNCLOUD_AUTH_LOCAL_HOST', '127.0.0.1');",
	} {
		assert.Contains(t, rendered, want)
	}
	assert.False(t, strings.Contains(rendered, "{{"), "unrendered template variable left in wp-config.php")
}
