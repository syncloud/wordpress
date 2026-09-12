local name = "wordpress";
local browser = "chrome";
local go = '1.25';
local version = '6.9';
local wp_ldap = '4.1.7';
local wp_cli = '2.8.1';
local nginx = '1.29.3-alpine3.22';
local php = '8.3.9-fpm-bullseye';
local debian = 'bookworm-slim';
local mariadb = '10.5.16-alpine';
local platform = '25.09';
local selenium = '4.35.0-20250828';
local store_publisher = 'stable-346';
local python = '3.12-slim-bookworm';
local distro_default = 'bookworm';
local distros = ['bookworm'];

local build(arch, test_ui, dind) = [{
    kind: "pipeline",
    type: "docker",
    name: arch,
    platform: {
        os: "linux",
        arch: arch
    },
    steps: [
        {
            name: "version",
            image: 'debian:' + debian,
            commands: [
                "echo $DRONE_BUILD_NUMBER > version"
            ]
        },
{
        name: 'cli',
        image: 'golang:' + go,
        commands: [
          'cd cli',
          'CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/install ./cmd/install',
          'CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/configure ./cmd/configure',
          'CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/pre-refresh ./cmd/pre-refresh',
          'CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/post-refresh ./cmd/post-refresh',
          'CGO_ENABLED=0 go build -o ../build/snap/bin/cli ./cmd/cli',
        ],
      },
{
             name: 'nginx',
             image: 'nginx:' + nginx,
             commands: [
               './nginx/build.sh',
             ],
           },
           {
             name: 'nginx test',
             image: 'syncloud/platform-'+ distro_default+'-' + arch + ':' + platform,
             commands: [
               './nginx/test.sh',
             ],
           },
        {
            name: "php",
            image: "php:" + php,
            commands: [
                "./php/build.sh",
                "./php/build-wordpress.sh " + version + " " + wp_ldap + " " + wp_cli
            ],
        },
{
             name: 'php test',
             image: 'syncloud/platform-'+ distro_default+'-' + arch + ':' + platform,
             commands: [
               './php/test.sh',
             ],
           },
        {
             name: 'mariadb',
             image: 'linuxserver/mariadb:' + mariadb,
             commands: [
               './mariadb/build.sh',
             ],
           },
           {
             name: 'mariadb test',
             image: 'syncloud/platform-'+distro_default+'-' + arch + ':' + platform,
             commands: [
               './mariadb/test.sh',
             ],
           },
        
        {
            name: "package",
            image: 'debian:' + debian,
            commands: [
                "VERSION=$(cat version)",
                "./package.sh " + name + " $VERSION "
            ]
        },
       ] + [
      {
        name: 'test ' + distro,
        image: 'python:' + python,
        commands: [
          'cd test',
          './deps.sh',
          'py.test -x -s test.py --distro=' + distro + ' --ver=$DRONE_BUILD_NUMBER --app=' + name,
        ],
      }
      for distro in distros
    ] + (if test_ui then ([
                            {
                              name: 'selenium',
                              image: 'selenium/standalone-' + browser + ':' + selenium,
                              detach: true,
                              environment: {
                                SE_NODE_SESSION_TIMEOUT: '999999',
                                START_XVFB: 'true',
                              },
                              volumes: [{
                                name: 'shm',
                                path: '/dev/shm',
                              }],
                              commands: [
                                'cat /etc/hosts',
                                'DOMAIN="' + distro_default + '.com"',
                                'APP_DOMAIN="' + name + '.' + distro_default + '.com"',
                                'getent hosts $APP_DOMAIN | sed "s/$APP_DOMAIN/auth.$DOMAIN/g" | sudo tee -a /etc/hosts',
                                'cat /etc/hosts',
                                '/opt/bin/entry_point.sh',
                              ],
                            },
                            {
                              name: 'selenium-video',
                              image: 'selenium/video:ffmpeg-6.1.1-20240621',
                              detach: true,
                              environment: {
                                DISPLAY_CONTAINER_NAME: 'selenium',
                                FILE_NAME: 'video.mkv',
                              },
                              volumes: [
                                {
                                  name: 'shm',
                                  path: '/dev/shm',
                                },
                                {
                                  name: 'videos',
                                  path: '/videos',
                                },
                              ],
                            },
                            {
                              name: 'test-ui',
                              image: 'python:' + python,
                              commands: [
                                'cd test',
                                './deps.sh',
                                'py.test -x -s ui.py --distro=' + distro_default + ' --ver=$DRONE_BUILD_NUMBER --app=' + name + ' --browser=' + browser,
                              ],
                              volumes: [{
                                name: 'videos',
                                path: '/videos',
                              }],
                            },
                            {
                              name: 'test-upgrade',
                              image: 'python:' + python,
                              commands: [
                                'cd test',
                                './deps.sh',
                                'py.test -x -s upgrade.py --distro=' + distro_default + ' --ver=$DRONE_BUILD_NUMBER --app=' + name + ' --browser=' + browser,
                              ],
                              privileged: true,
                              volumes: [{
                                name: 'videos',
                                path: '/videos',
                              }],
                            },
                          ]) else []) + [
      {
        name: 'publish',
        image: 'syncloud/store-publisher:' + store_publisher,
        environment: {
          SYNCLOUD_TOKEN: { from_secret: 'SYNCLOUD_TOKEN' },
        },
        command: ['snap', '-c', '${DRONE_BRANCH}'],
        when: {
          branch: ['stable'],
          event: ['push'],
        },
      },
      {
        name: 'artifact',
        image: 'appleboy/drone-scp:1.6.4',
        settings: {
          host: {
            from_secret: 'artifact_host',
          },
          username: 'artifact',
          key: {
            from_secret: 'artifact_key',
          },
          timeout: '2m',
          command_timeout: '2m',
          target: '/home/artifact/repo/' + name + '/${DRONE_BUILD_NUMBER}-' + arch,
          source: 'artifact/*',
          strip_components: 1,
        },
        when: {
          status: ['failure', 'success'],
          event: ['push'],
        },
      },
    ],
    trigger: {
      event: [
        'push',
        'pull_request',
      ],
    },
    services: [
      {
        name: 'docker',
        image: 'docker:' + dind,
        privileged: true,
        volumes: [
          {
            name: 'dockersock',
            path: '/var/run',
          },
        ],
      },
    ] + [
      {
        name: name + '.' + distro + '.com',
        image: 'syncloud/platform-' + distro + '-' + arch + ':' + platform,
        privileged: true,
        volumes: [
          {
            name: 'dbus',
            path: '/var/run/dbus',
          },
          {
            name: 'dev',
            path: '/dev',
          },
        ],
      }
      for distro in distros
    ],
    volumes: [
      {
        name: 'dbus',
        host: {
          path: '/var/run/dbus',
        },
      },
      {
        name: 'dev',
        host: {
          path: '/dev',
        },
      },
      {
        name: 'shm',
        temp: {},
      },
      {
        name: 'dockersock',
        temp: {},
      },
      {
        name: 'videos',
        temp: {},
      },
    ],
  },
];

build("amd64", true, "20.10.21-dind") +
build("arm64", false, "19.03.8-dind") +
build("arm", false, "19.03.8-dind")

