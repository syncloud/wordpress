<?php
require WPMU_PLUGIN_DIR.'/daggerhart-openid-connect-generic/openid-connect-generic.php';

function syncloud_oidc_role($user_claim) {
    $groups = array();
    if (isset($user_claim['groups']) && is_array($user_claim['groups'])) {
        $groups = $user_claim['groups'];
    }
    return in_array(SYNCLOUD_ADMIN_GROUP, $groups, true) ? 'administrator' : 'subscriber';
}

function syncloud_oidc_is_local($url) {
    return defined('SYNCLOUD_AUTH_LOCAL_HOST')
        && parse_url($url, PHP_URL_HOST) === SYNCLOUD_AUTH_LOCAL_HOST;
}

add_filter('openid-connect-generic-alter-user-data', function ($user_data, $user_claim) {
    $user_data['role'] = syncloud_oidc_role($user_claim);
    return $user_data;
}, 10, 2);

add_action('openid-connect-generic-update-user-using-current-claim', function ($user, $user_claim) {
    $role = syncloud_oidc_role($user_claim);
    if (!in_array($role, (array) $user->roles, true)) {
        $user->set_role($role);
    }
}, 10, 2);

add_filter('http_request_host_is_external', function ($external, $host, $url) {
    return syncloud_oidc_is_local($url) ? true : $external;
}, 10, 3);

add_action('http_api_curl', function ($handle, $args, $url) {
    if (syncloud_oidc_is_local($url)) {
        curl_setopt($handle, CURLOPT_UNIX_SOCKET_PATH, SYNCLOUD_AUTH_SOCKET);
    }
}, 10, 3);

add_filter('http_request_args', function ($args, $url) {
    if (syncloud_oidc_is_local($url)) {
        $args['headers']['Host'] = SYNCLOUD_AUTH_HOST;
        $args['headers']['X-Forwarded-Proto'] = 'https';
        $args['headers']['X-Forwarded-Host'] = SYNCLOUD_AUTH_HOST;
    }
    return $args;
}, 10, 2);
