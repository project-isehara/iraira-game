#include <M5Atom.h>
#include <BluetoothSerial.h>

const int analogIn = 25;
const int parallelOut0 = 33;
const int parallelOut1 = 23;
const int parallelOut2 = 19;

const int MAX=4095;
const int MIN=0;

BluetoothSerial SerialBT;

void setup() {
  M5.begin(true,true,true);//第三引数でdisplayのenable
  delay(50);
  M5.dis.fillpix(0xff0000);

  pinMode(parallelOut0,OUTPUT);
  pinMode(parallelOut1,OUTPUT);
  pinMode(parallelOut2,OUTPUT);

  SerialBT.begin("esp32");
}

int cnt=0;
void loop() {
  int readAnalogValue=analogRead(analogIn);
  float analogValue=(float)(readAnalogValue)/(MAX-MIN);
  uint8_t parallelOrg= (uint8_t)(analogValue*7);

  Serial.printf("%.3f\n",analogValue);
  SerialBT.printf("%.3f\n",analogValue);

  if(parallelOrg&(1<<0)){
    digitalWrite(parallelOut0,HIGH);
  }else{
    digitalWrite(parallelOut0,LOW);
  }

  if(parallelOrg&(1<<1)){
    digitalWrite(parallelOut1,HIGH);
  }else{
    digitalWrite(parallelOut1,LOW);
  }

  if(parallelOrg&(1<<2)){
    digitalWrite(parallelOut2,HIGH);
  }else{
    digitalWrite(parallelOut2,LOW);
  }
  
  delay(20);
}