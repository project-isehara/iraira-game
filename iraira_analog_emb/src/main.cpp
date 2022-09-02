#include <M5Atom.h>
#include <BluetoothSerial.h>

const int analogIn = 25;
const int LED_PIN = 22;

const int MAX=4095;
const int MIN=0;

const unsigned long LONG_PRESS_DURAITON = 1000;

BluetoothSerial SerialBT;

int led_lighting_count=0;
void led_put_on(int dulation){
  led_lighting_count = dulation;
  digitalWrite(LED_PIN,HIGH);
}

void remove_led(){
  if(led_lighting_count>0){
    led_lighting_count--;
  }

  if(led_lighting_count==0){
    digitalWrite(LED_PIN,LOW);
  }
}

void setup() {
  M5.begin(true,true,true);//第三引数でdisplayのenable
  delay(50);
  M5.dis.fillpix(0xff0000);

  pinMode(LED_PIN,OUTPUT);
  led_put_on(50);

  SerialBT.begin("esp32");
}

int cnt=0;
unsigned long lastPressedTime=0;
bool isLongPressed=false;
void loop() {
  M5.update();
  int readAnalogValue=analogRead(analogIn);
  float analogValue=(float)(readAnalogValue)/(MAX-MIN);

  Serial.printf("%.3f\n",analogValue);
  SerialBT.printf("%.3f\n",analogValue);

  if(M5.Btn.wasPressed()){
    led_put_on(5);
    lastPressedTime = millis();
    Serial.printf("p\n");
    SerialBT.printf("p\n");
  }

  if(M5.Btn.wasReleased()){
    led_put_on(5);
    isLongPressed=false;
    Serial.printf("r\n");
    SerialBT.printf("r\n");
  }

  if(M5.Btn.isPressed()){
    if(!isLongPressed && millis() - lastPressedTime > LONG_PRESS_DURAITON){
      isLongPressed=true;

      led_put_on(5);
      Serial.printf("l\n");
      SerialBT.printf("l\n");
    }
  }

  remove_led();
  delay(20);
}


