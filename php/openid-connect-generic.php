<?php
require WPMU_PLUGIN_DIR.'/daggerhart-openid-connect-generic/openid-connect-generic.php';

add_filter('openid-connect-generic-alter-user-data', function ($user_data, $user_claim) {
    $user_data['role'] = 'administrator';
    return $user_data;
}, 10, 2);

add_filter('http_request_args', function ($args, $url) {
    if (defined('OIDC_ISSUER') && OIDC_ISSUER !== '' && strpos($url, OIDC_ISSUER) === 0) {
        $args['sslcertificates'] = '/var/snap/platform/current/syncloud.ca.crt';
    }
    return $args;
}, 10, 2);
