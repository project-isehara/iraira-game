# 牽引力信号生成プログラム

## Python開発環境

### Python環境の構築

Python公式などからPython3.9をインストールする。

#### 動作確認

```sh
python --version
```

### Python環境にpoetryをインストールする

```sh
python -m pip install poetry
```

### 2. ライブラリのインストール

poetryがインストールされたPython環境下で環境構築する。 pyproject.tomlがあるディレクトリで実行する。

```sh
python -m poetry install
```

### 3. アプリの実行

```sh
python -m poetry python src/iraira
```
