#include <M5Atom.h>
#include <BluetoothSerial.h>

const int analogIn = 25;
const int LED_PIN = 22;

const int MAX=4095;
const int MIN=0;

const unsigned long LONG_PRESS_DURAITON = 1000;
const float ZERO_VALUE_RANGE = 0.02;
const int RESOLUTION = 5;

BluetoothSerial SerialBT;

#define COLOR_BLACK { 0x00, 0x00, 0x00 }
#define COLOR_WHITE { 0xFF, 0xFF, 0xFF }
#define COLOR_RED { 0xFF, 0x00, 0x00 }
#define COLOR_GREEN { 0x00, 0xFF, 0x00 }
#define COLOR_BLUE { 0x00, 0x00, 0xFF }
#define COLOR_YELLOW { 0xFF, 0xFF, 0x00 }
#define COLOR_CYAN { 0x00, 0xFF, 0xFF }
#define COLOR_MAGENTA { 0xFF, 0x00, 0xFF }

const uint8_t digitData[6][25] = {
  { 0,0,0,0,0,
    0,1,1,1,0, 
    1,0,0,0,1, 
    1,0,0,0,1, 
    0,1,1,1,0, },
  {0,0,0,0,0, 
   0,0,0,0,1, 
   1,1,1,1,1, 
   0,1,0,0,1, 
   0,0,0,0,0, },
  { 0,0,0,0,0,
    0,1,0,0,1, 
    1,0,1,0,1, 
    1,0,0,1,1, 
    0,1,0,0,1, },
  { 0,0,0,0,0,
    0,1,0,1,0, 
    1,0,1,0,1, 
    1,0,1,0,1, 
    1,0,0,0,1, },
  { 0,0,0,0,0,
    0,0,0,1,0, 
    1,1,1,1,1, 
    0,1,0,1,0, 
    0,0,1,1,0, },
  { 0,0,0,0,0,
    1,0,0,1,0, 
    1,0,1,0,1, 
    1,0,1,0,1, 
    1,1,1,0,1, }
};


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

void DisplayNumber(int num, CRGB color) {
  for (int i = 0; i < 25; i ++) {
    if(digitData[num][i] == 0){
      M5.dis.drawpix(i, 0x00);
    }else{
      M5.dis.drawpix(i, color);
    }
  }
}

void displayAnalogValue(int analogValue){
  const int ZERO_HIGH = (MAX - MIN)/2 + (MAX - MIN) * ZERO_VALUE_RANGE;
  const int ZERO_LOW = (MAX - MIN)/2 - (MAX - MIN) * ZERO_VALUE_RANGE;
  const int STEP = ((MAX - MIN) - ZERO_HIGH)/RESOLUTION;

  if(ZERO_LOW < analogValue && analogValue < ZERO_HIGH){
    DisplayNumber(0,COLOR_WHITE);
    return;
  }

  if(analogValue>ZERO_HIGH){
    int border = ZERO_HIGH;
    for(int i=1;i<RESOLUTION;i++){
      border += STEP;
      if(analogValue < border){
        DisplayNumber(i,COLOR_RED);
        return;
      }
    }
    DisplayNumber(RESOLUTION,COLOR_RED);
  }else if(analogValue<ZERO_LOW){
    int border = ZERO_LOW;
    for(int i=1;i<RESOLUTION;i++){
      border -= STEP;
      if(analogValue > border){
        DisplayNumber(i,COLOR_BLUE);
        return;
      }
    }
    DisplayNumber(RESOLUTION,COLOR_BLUE);

  }else{
      //Shouldn't come here
      DisplayNumber(0,COLOR_YELLOW);
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
  displayAnalogValue(readAnalogValue);

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


