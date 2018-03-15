// rmspeers 2018

// define RF_CHIBI to target a Freakduino, so you have 802.15.4 support:
#define RF_CHIBI

#ifdef RF_CHIBI
  // NOTE:
  // To compile this, you need the Chibi library added to Arduino.
  // Get the ZIP from https://freaklabs.org/chibiarduino/, rename it, and import it.
  // Also download and add the board support files to your sketch directory, by creating
  // a hardware/ subdirectory if it doesn't exist and dropping the zip contents there.
  #include <chibi.h>
  #define FREAKDUINO 1
  #define CHIBI_PROMISCUOUS 1
  #include <chibiUsrCfg.h>
#endif //RF_CHIBI

// this pin will be pulled low to simulate a "failure"
#define SWITCH_PIN 7
// alternatively, receiving this command string on serial will simulate it
#define SWITCH_SERIAL_CMD 0xFA

// this pin will be set low when a failure occurs
#define SIGNAL_PIN 6

// this pin can be brought low to signal a reset
#define SOFTRESET_PIN 5

// how fast do we want to check signals
#define MSDELAY 500 //every 500 ms we check all items
#define RFDELAY 100 //every 100 ms we check the RF

// these are for state tracking
#define MODE_ABNORMAL 0
#define MODE_NORMAL   1

int valSwitchPin = 1;
int valSwResetPin = 1;
byte valSerialByte = -1;
int mode;

void setup() {
  // setup code here, to run once:
  Serial.begin(9600);
  pinMode(SWITCH_PIN, INPUT_PULLUP);
  pinMode(SOFTRESET_PIN, INPUT_PULLUP);
  pinMode(SIGNAL_PIN, OUTPUT);
  mode = 1;
#ifdef RF_CHIBI
  chibiInit();
  chibiSetShortAddr(0x0000);
  chibiSetChannel(11);
#endif //RF_CHIBI
}

#ifdef RF_CHIBI
void printHexBytes(byte dataLen, byte data[], bool firstByteIsLen) {
  byte i=0;
  if (firstByteIsLen && dataLen >= data[0] + 1) {
    //Serial.print("Adjusting length as: dataLen=");
    //Serial.print(dataLen, DEC);
    dataLen = data[0] + 1;
    i = 1;
    //Serial.print("; first byte=");
    //Serial.println(data[0], DEC);
  } /*else {
    Serial.print("Not adjusting length as: dataLen=");
    Serial.print(dataLen, DEC);
    Serial.print("; first byte=");
    Serial.println(data[0], DEC);
  }*/
  for (; i<dataLen; i++) {
    if (data[i]<0x10) { Serial.print("0"); }
    Serial.print(data[i], HEX);
  }
  Serial.println();
}

void handleRfData() {
  byte rfDataLen;
  byte rfData[CHB_MAX_PAYLOAD];
  if (chibiDataRcvd() == true) {
    rfDataLen = chibiGetData(rfData);
    if (rfDataLen == 0) {
      Serial.println("[WARN] Duplicate data received.");
    } else {
      Serial.println("[INFO] Received: ");
      printHexBytes(rfDataLen, rfData, true);
    }
    // Chibi's stack will automatically send an ACK back
    /*
    int src_addr = chibiGetSrcAddr();
    Serial.print("Source Address = 0x");
    Serial.println(src_addr, HEX);
    Serial.print("Seq number received = 0x");
    Serial.println(rfData[3], HEX);
    byte ackFrame[5] = { 0x02, 0x00, rfData[3], 0x00, 0x00 };
    byte status = chibiTx(0xFFFF, ackFrame, 5); //doesn't allow us to send raw bytes
    */
  }
}
#endif //RF_CHIBI

void loop() {
  // main code here, to run repeatedly:
  if (mode == MODE_NORMAL) {
    Serial.println("[INFO] Running in normal operation...");
  } else {
    Serial.println("[ERROR] Needs a reset");
  }
  valSwitchPin = digitalRead(SWITCH_PIN);
  valSwResetPin = digitalRead(SOFTRESET_PIN);
  //Serial.print("Soft reset pin: "); Serial.println(valSwResetPin, HEX);
  valSerialByte = Serial.read();
  if (valSerialByte != 0xFF) {
    Serial.print("Serial received: ");
    Serial.println(valSerialByte, HEX);
  }
  if (valSwitchPin == 0 || valSerialByte == SWITCH_SERIAL_CMD) {
    Serial.println("[WARN] Failure case triggered.");
    mode = MODE_ABNORMAL;
    delay(50);
    digitalWrite(SIGNAL_PIN, HIGH);
  }
  if (mode != MODE_NORMAL && valSwResetPin == 0) {
    Serial.println("[INFO] Soft reset pulled.");
    mode = MODE_NORMAL;
    digitalWrite(SIGNAL_PIN, LOW);
  }

#ifdef RF_CHIBI
  // Poll RF faster than other items:
  for (byte j=0; j<=MSDELAY/RFDELAY; j++) {
    handleRfData();
    delay(RFDELAY);
  }
#else //!RF_CHIBI
  delay(MSDELAY);
#endif //!RF_CHIBI
}
