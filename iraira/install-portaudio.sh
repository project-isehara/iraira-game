#!/bin/bash
set -eu

function install_libasound() {
    sudo apt-get install libasound-dev
}

function make_tmp_dir() {
    # 一時ディレクトリの生成
    mktemp -d
}

function auto_remove_tmp_dir() {
    # 一時ディレクトリの自動削除
    ## 正常終了したとき
    trap 'rm -rf "$1"' EXIT
    ## 異常終了したとき
    trap 'trap - EXIT; rm -rf "$1"; exit -1' INT PIPE TERM
}

function install_portaudio() {
    curl http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz | tar -zx
    cd portaudio/
    ./configure && make
    sudo make install
}

install_libasound

(
    # インストール後にダウンロードファイルは削除される
    tmp_dir=$(make_tmp_dir)
    auto_remove_tmp_dir "${tmp_dir}"
    cd "${tmp_dir}"
    install_portaudio
)
