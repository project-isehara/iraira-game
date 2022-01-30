# iseharaプロジェクト

プロジェクトの成果物管理リポジトリ

## Python開発環境

### Python環境の構築

Python公式などからPython3.9をインストールする。

#### 動作確認

```sh
# pythonコマンドのパスが通っている場合
python --version

# or pyコマンドのパスが通っている場合
py -m --version
```

### Python環境にpipenvをインストールする

[pipenv](https://pipenv-ja.readthedocs.io/ja/translate-ja/) 仮想環境で構築できる。

```sh
pip install pipenv

# or pipにパスが通っていない場合
python -m pip install pipenv

# or pyコマンドにパスが通っている場合
py -m pip install pipenv
```

### 2. ライブラリのインストール

pipenvがインストールされたPython環境下で環境構築する。 カレントディレクトリをPipfileがあるフォルダで実行する。

```sh
cd bilibili # プロジェクトのルートに移動

# pipenv環境のパスが通っている場合
pienv install

# or pythonコマンドのパスが通っている場合
python -m pipenv install

# or pyコマンドのパスが通っている場合
py -m pipenv install
```

### 3. アプリの実行

Pythonプログラム`xxx.py`を動かす例

```sh
# pipenv環境のパスが通っている場合
pienv run xxx.py

# or pythonコマンドのパスが通っている場合
python -m pipenv run xxx.py

# or pyコマンドのパスが通っている場合
py -m pipenv run xxx.py
```
