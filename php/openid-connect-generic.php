<?php
require WPMU_PLUGIN_DIR.'/daggerhart-openid-connect-generic/openid-connect-generic.php';

add_filter('openid-connect-generic-alter-user-data', function ($user_data, $user_claim) {
    $user_data['role'] = 'administrator';
    return $user_data;
}, 10, 2);
