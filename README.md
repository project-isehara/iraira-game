# 妨害イライラ棒

## Directory layout

```text
├─experiment        # 実験検証コード
├─iraira            # イライラ棒メインシステム (Python, Raspberry Pi 3)
└─iraira_analog_emb # イライラ棒ゲームコントローラー制御 (C++, M5Atom)
```

## USB CONNECTION
振動コントローラ(M5Atom)とはUSBケーブルで接続します。
接続名は "/dev/M5_ATOM"。
M5 ATOM接続時にこの名前で認識されるように、事前に下記を実行しておく。
1. 新しいudevルールファイルを作成
```bash
sudo vim /etc/udev/rules.d/99-usb-serial.rules
```
2. 下記を入力する。M5 AtomはidVendor=0403, idProduct=6001
```text
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="M5_ATOM"
```
3. udevルールを再読み込みして適用
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```
4. シンボリックリンクでアクセスできるか確認する
```bash
ls -l /dev/M5_ATOM
# lrwxrwxrwx 1 root root 7 Nov  5 09:37 /dev/M5_ATOM -> ttyUSB0 などが出れば設定OK
```
