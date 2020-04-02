#!/bin/bash

# Copyright 2018 Red Hat Inc., Durham, North Carolina.
# All Rights Reserved.
#
# OpenSCAP Test Suite
#
# Authors:
#      Jan Černý <jcerny@redhat.com>

. $builddir/tests/test_common.sh

set -e -o pipefail

function test_offline_mode_textfilecontent54 {
    temp_dir="$(mktemp -d)"

    mkdir -p $temp_dir/tmp/zzz
    mkdir -p /tmp/zzz

    # prepare /bar.txt
    echo "Hello from the inside" > "$temp_dir/tmp/bar.txt"
    echo "Hello from the outside" > "/tmp/bar.txt"

    # prepare /zzz/foo.txt
    mkdir -p "$temp_dir/tmp/zzz"
    echo "Bye from the inside" > "$temp_dir/tmp/zzz/foo.txt"
    echo "Bye from the outside" > "/tmp/zzz/foo.txt"

    # prepare file that is available only outside
    echo "I'm outside" > "/tmp/only_outside.txt"
    result="$(mktemp)"

    export OSCAP_PROBE_ROOT
    OSCAP_PROBE_ROOT="$temp_dir"
    $OSCAP oval eval --results $result $srcdir/textfilecontent54.oval.xml

    [ -s "$result" ]

    assert_exists 1 '/oval_results/results/system/oval_system_characteristics/system_data'

    tfc_item='/oval_results/results/system/oval_system_characteristics/system_data/ind-sys:textfilecontent_item'
    assert_exists 2 $tfc_item

    assert_exists 1 $tfc_item'/ind-sys:filepath[text()="/tmp/bar.txt"]'
    assert_exists 1 $tfc_item'/ind-sys:path[text()="/tmp"]'
    assert_exists 1 $tfc_item'/ind-sys:filename[text()="bar.txt"]'
    assert_exists 1 $tfc_item'/ind-sys:text[text()="Hello from the inside"]'

    assert_exists 1 $tfc_item'/ind-sys:filepath[text()="/tmp/zzz/foo.txt"]'
    assert_exists 1 $tfc_item'/ind-sys:path[text()="/tmp/zzz"]'
    assert_exists 1 $tfc_item'/ind-sys:filename[text()="foo.txt"]'
    assert_exists 1 $tfc_item'/ind-sys:text[text()="Bye from the inside"]'

    assert_exists 1 '/oval_results/results/system/definitions/definition[@definition_id="oval:x:def:3" and @result="true"]'

    rm -rf "$temp_dir"
    rm -f "$result"
    rm -f "/tmp/bar.txt" "/tmp/only_outside.txt"
    rm -rf "/tmp/zzz"
}

# Testing.

test_init "test_offline_mode_textfilecontent54.log"

test_run "test_offline_mode_textfilecontent54" test_offline_mode_textfilecontent54

test_exit
