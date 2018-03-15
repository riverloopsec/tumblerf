#include <SoftwareSerial.h>

// this pin is connected to the TX on the target, so it RX's the target serial
// console's output
#define TARGET_SERIAL_RX 2
// this pin is connected to the RX on the target, so it TX's from our Arduino
// to the target's serial input
#define TARGET_SERIAL_TX 3
// baud rate of the target's serial
#define TARGET_SERIAL_BAUD 9600

// this pin to be connected to a target pin that goes low when a failure occurs
// typically this pin is connected to something on the target, like an SPI line
// or otherwise, that is logic high when functioning properly
#define SIGNAL_PIN 6
// sending this command byte on serial shows we saw it go low
#define SIGNAL_SERIAL_RES 0x03

// this pin will be driven low to cause a reset on the target
// typically this is wired to the target's RST line
#define RESET_PIN 5
// receiving this command byte on serial will cause us to drive it low
#define RESET_SERIAL_CMD 0x01

// for test purposes, we will pull this pin low to tell the target to simulate an invalid state
#define TEST_SWITCH_PIN 7
// receiving this command byte on serial will cause us to drive it low
#define TEST_SWITCH_CMD 0x02

int valSwitchPin = 1;
int valSwResetPin = 1;
byte valSerialByte = -1;

SoftwareSerial targetSerial(TARGET_SERIAL_RX, TARGET_SERIAL_TX);

void setup() {
  // setup code here, to run once:
  Serial.begin(115200);
  pinMode(RESET_PIN, OUTPUT);
  digitalWrite(RESET_PIN, HIGH);
  pinMode(TEST_SWITCH_PIN, OUTPUT);
  digitalWrite(TEST_SWITCH_PIN, HIGH);
  pinMode(SIGNAL_PIN, INPUT_PULLUP);
  targetSerial.begin(TARGET_SERIAL_BAUD);
}

void loop() {
  // first we see if we have a command from the harness
  valSerialByte = Serial.read();
  if (valSerialByte != 0xFF) {
    Serial.print("[HARNESS] Serial command received: ");
    Serial.println(valSerialByte, HEX);

    if (valSerialByte == RESET_SERIAL_CMD) {
      Serial.println("[HARNESS] Resetting target by pulling pin low for 400ms.");
      digitalWrite(RESET_PIN, LOW);
      delay(400);
      digitalWrite(RESET_PIN, HIGH);
    } else if (valSerialByte == TEST_SWITCH_CMD) {
      Serial.println("[HARNESS] Signaling target to invalid state by pulling pin low for 400ms.");
      digitalWrite(TEST_SWITCH_PIN, LOW);
      delay(400);
      digitalWrite(TEST_SWITCH_PIN, HIGH);
    }
  } else {
    Serial.println("[HARNESS] No command received.");
  }
  // then we see if we need to inform the harness of anything
  valSwitchPin = digitalRead(SIGNAL_PIN);
  Serial.print("[HARNESS] Target's signal pin: "); Serial.println(valSwResetPin, DEC);
  if (valSwitchPin == 0) {
    Serial.write(SIGNAL_SERIAL_RES);
    delay(50);
  }
  // then we forward target serial data to the harness
  if (targetSerial.available()) {
    do {
      Serial.write(targetSerial.read());
    } while (targetSerial.available());
    Serial.println("");
  }
  //if (Serial.available()) {
  //  targetSerial.write(Serial.read());
  //}
  // slow down the spin
  delay(300);
}
