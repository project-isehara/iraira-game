#include <M5StickCPlus.h>
#include <Ticker.h>

const uint32_t PIN = 26;
const uint32_t MARGIN_TIME = 1000; // 接触時の無敵時間 [ms]

const int16_t BACKGROUND_COLOR = BLACK; // 背景色

Button stickBtn = Button(PIN, false, 5); // イライラ棒の接触判定ボタン
uint32_t pressCount;                     // 接触回数
uint32_t pressTime;                      // 接触からの無敵時間用一時変数 [ms]

Ticker ticker;
String prevString; // 画面表示用状態変数 前回と同じ文字列の場合更新しない処理用

void drawCentreString()
{
  const String string = String(pressCount);
  if (string != prevString)
  {
    M5.Lcd.drawCentreString(string, M5.Lcd.width() / 2, M5.Lcd.height() / 3, 6);
    prevString = string;
  }
}

void clickBtn()
{
  M5.update();
  if (M5.BtnA.wasPressed())
  {
    M5.Lcd.fillScreen(BACKGROUND_COLOR);
    pressCount = 0;
    M5.Lcd.drawCentreString("0", M5.Lcd.width() / 2, M5.Lcd.height() / 3, 6);
  }
}

void setup()
{
  M5.begin();
  pinMode(PIN, INPUT_PULLUP);

  pressCount = 0;
  pressTime = 0;

  // ビープ音設定(初期値)
  M5.Beep.setBeep(300, 1000);
  M5.Beep.setVolume(11);

  M5.Lcd.setRotation(3);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setTextDatum(7);
  M5.Lcd.fillScreen(BACKGROUND_COLOR);

  const String a = String(pressCount);
  ticker.attach_ms(512, drawCentreString);

  attachInterrupt(BUTTON_A_PIN, clickBtn, FALLING);
}

void loop()
{
  M5.update();
  stickBtn.read();

  if (stickBtn.wasPressed())
  {
    uint32_t now_ms = millis();
    if (now_ms - pressTime > MARGIN_TIME)
    {
      M5.Beep.beep();
      pressTime = now_ms;
      pressCount += 1;
    };
  };
}
