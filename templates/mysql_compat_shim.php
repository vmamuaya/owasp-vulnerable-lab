# PHP 8 Compatibility Shim for WackoPicko
# Maps deprecated mysql_* functions to mysqli_* equivalents
# Usage in nginx: fastcgi_param PHP_VALUE "auto_prepend_file=/path/to/mysql_compat.php";

<?php
global $mysql_link;

function mysql_connect($host, $user, $pass, $new_link = false, $client_flags = 0) {
    global $mysql_link;
    $mysql_link = mysqli_connect($host, $user, $pass);
    return $mysql_link;
}

function mysql_select_db($db, $link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_select_db($link, $db);
}

function mysql_query($query, $link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_query($link, $query);
}

function mysql_fetch_array($result, $type = MYSQLI_BOTH) {
    return mysqli_fetch_array($result, $type);
}

function mysql_fetch_assoc($result) {
    return mysqli_fetch_assoc($result);
}

function mysql_fetch_row($result) {
    return mysqli_fetch_row($result);
}

function mysql_fetch_object($result) {
    return mysqli_fetch_object($result);
}

function mysql_num_rows($result) {
    return mysqli_num_rows($result);
}

function mysql_real_escape_string($str, $link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_real_escape_string($link, $str);
}

function mysql_error($link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_error($link);
}

function mysql_insert_id($link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_insert_id($link);
}

function mysql_close($link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_close($link);
}

function mysql_result($result, $row, $field = 0) {
    mysqli_data_seek($result, $row);
    $row_data = mysqli_fetch_array($result);
    return $row_data[$field];
}

function mysql_data_seek($result, $row) {
    return mysqli_data_seek($result, $row);
}

function mysql_free_result($result) {
    return mysqli_free_result($result);
}

function mysql_set_charset($charset, $link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_set_charset($link, $charset);
}

function mysql_affected_rows($link = null) {
    global $mysql_link;
    $link = $link ?: $mysql_link;
    return mysqli_affected_rows($link);
}

function mysql_escape_string($str) {
    global $mysql_link;
    return mysqli_real_escape_string($mysql_link, $str);
}

if (!defined('MYSQL_ASSOC')) define('MYSQL_ASSOC', MYSQLI_ASSOC);
if (!defined('MYSQL_NUM')) define('MYSQL_NUM', MYSQLI_NUM);
if (!defined('MYSQL_BOTH')) define('MYSQL_BOTH', MYSQLI_BOTH);
?>