#include <M5StickCPlus.h>

const int PIN = 26;

void setup()
{
  M5.begin();
  pinMode(PIN, INPUT_PULLUP);
  M5.Beep.setBeep(400, 100); // ビープ音設定(初期値)
}

void loop()
{
  M5.update();

  bool isPressed = !digitalRead(PIN);
  if (isPressed)
  {
    M5.Beep.beep();
  }

  delay(2);
}
