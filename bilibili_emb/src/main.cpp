#include <M5StickCPlus.h>

const uint32_t PIN = 26;
const uint32_t MARGIN_TIME = 1000; // 接触時の無敵時間 [ms]

Button stickBtn = Button(PIN, false, 5); // イライラ棒の接触判定ボタン
uint32_t pressCount;                     // 接触回数
uint32_t pressTime;                      // 接触からの無敵時間用一時変数 [ms]

void setup()
{
  M5.begin();
  pinMode(PIN, INPUT_PULLUP);

  pressCount = 0;
  pressTime = 0;

  // ビープ音設定(初期値)
  M5.Beep.setBeep(300, 1000);
  M5.Beep.setVolume(11);
}

void loop()
{
  M5.update();
  stickBtn.read();
  Serial.println(pressCount);

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
