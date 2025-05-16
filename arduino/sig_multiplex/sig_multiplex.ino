#include <Arduino.h>

// --- Debug and Serial Settings ---
const bool DEBUG = false;             
const int USB_BAUD = 115200;         // USB Serial baud rate (for debugging)
const int SERIAL_BAUD = 3000;        // UART baud rate for external communication

// --- Constants ---
const uint8_t START_MARKER = 0xAA;   // Packet start marker
const int MAX_QUEUE_SIZE = 16;       // Maximum number of events to queue (must be a power of 2)
static constexpr uint8_t QUEUE_MASK = MAX_QUEUE_SIZE - 1; // Mask for wrap‑around
static_assert((MAX_QUEUE_SIZE & (MAX_QUEUE_SIZE - 1)) == 0, "MAX_QUEUE_SIZE must be a power of two");

// --- Pin Definitions ---
const int PIN_HB = 5;   // Heartbeat input (opcon pin 17)
const int PIN_L1 = 6;   // Lever 1 input (opcon pin 20)
const int PIN_L2 = 9;   // Lever 2 input (opcon pin 37)
const int PIN_L3 = 10;  // Lever 3 input (opcon pin 36)

// --- Channel IDs ---
#define CHANNEL_HB  0x01  // Heartbeat events (PIN_HB)
#define CHANNEL_L1  0x02  // Lever 1 events
#define CHANNEL_L2  0x03  // Lever 2 events
#define CHANNEL_L3  0x04  // Lever 3 events

// --- Event Structure ---
struct Event {
  uint8_t channelID;
  uint32_t pulseWidth;
  uint32_t timestamp;
};

// --- Event Queue ---
Event eventQueue[MAX_QUEUE_SIZE];
volatile uint8_t queueHead = 0;
volatile uint8_t queueTail = 0;

// --- Packet Structure ---
struct __attribute__((packed)) Packet {
  uint8_t  startMarker;
  uint8_t  channelID;
  uint32_t pulseWidth;
  uint32_t waitTime;
  uint8_t  checksum;
};

// --- Channel-specific variables ---
struct ChannelState {
  volatile uint32_t startTime;
  volatile bool isActive;
};
ChannelState channels[5]; // Index 0 unused, channels 1-4

// --- Queue Management ---
bool enqueueEvent(uint8_t channelID, uint32_t pulseWidth) {
  uint32_t timestamp = micros();
  uint8_t nextTail = (queueTail + 1) & QUEUE_MASK;
  noInterrupts();
    if (nextTail != queueHead) {
      eventQueue[queueTail] = { channelID, pulseWidth, timestamp };
      queueTail = nextTail;
      interrupts();
      return true;
    }
    interrupts();
  if (DEBUG) {
    Serial.println("ERROR: Event queue overflow!");
  }
  return false;
}

bool dequeueEvent(Event &event) {
  noInterrupts();
    if (queueHead == queueTail) {
      interrupts();
      return false;
    }
    event = eventQueue[queueHead];
    queueHead = (queueHead + 1) & QUEUE_MASK;
  interrupts();
  return true;
}

// --- Checksum Calculation ---
uint8_t calculateChecksum(uint8_t channelID, uint32_t pulseWidth) {
  uint8_t checksum = 0;
  checksum += channelID;
  checksum += (pulseWidth & 0xFF);
  checksum += ((pulseWidth >> 8) & 0xFF);
  checksum += ((pulseWidth >> 16) & 0xFF);
  checksum += ((pulseWidth >> 24) & 0xFF);
  return checksum;
}

// --- Packet Transmission ---
void sendPacket(uint8_t channelID, uint32_t pulseWidth, uint32_t eventTime) {
  uint32_t currentTime = micros();
  if (Serial1.availableForWrite() < sizeof(Packet)) {
    if (DEBUG) Serial.println("ERROR: Serial buffer full, packet dropped!");
    return;
  }
  Packet pkt;
  pkt.startMarker = START_MARKER;
  pkt.channelID   = channelID;
  pkt.pulseWidth  = pulseWidth;
  uint32_t waitTime = (currentTime >= eventTime)
    ? (currentTime - eventTime)
    : ((0xFFFFFFFF - eventTime) + currentTime + 1);
  pkt.waitTime = waitTime;
  pkt.checksum = calculateChecksum(channelID, pulseWidth);
  size_t written = Serial1.write((uint8_t*)&pkt, sizeof(pkt));
  if (written != sizeof(pkt) && DEBUG) {
    Serial.print("ERROR: Serial write incomplete: ");
    Serial.print(written);
    Serial.print(" of ");
    Serial.println(sizeof(pkt));
  }
  if (DEBUG) {
    Serial.print("Sent Packet chan=");
    Serial.print(pkt.channelID);
    Serial.print(" pw=");
    Serial.print(pkt.pulseWidth);
    Serial.print(" wt=");
    Serial.print(pkt.waitTime);
    Serial.print(" cs=0x");
    Serial.println(pkt.checksum, HEX);
  }
}

// --- ISR and Setup/Loop ---
void handlePulseEvent(uint8_t channelID, int pin) {
  uint32_t now = micros();
  bool state = digitalRead(pin);
  if (state) {
    channels[channelID].startTime = now;
    channels[channelID].isActive = true;
  } else if (channels[channelID].isActive) {
    uint32_t width = (now >= channels[channelID].startTime)
      ? (now - channels[channelID].startTime)
      : ((0xFFFFFFFF - channels[channelID].startTime) + now + 1);
    enqueueEvent(channelID, width);
    channels[channelID].isActive = false;
  }
}

void isrHB() { handlePulseEvent(CHANNEL_HB, PIN_HB); }
void isrL1() { handlePulseEvent(CHANNEL_L1, PIN_L1); }
void isrL2() { handlePulseEvent(CHANNEL_L2, PIN_L2); }
void isrL3() { handlePulseEvent(CHANNEL_L3, PIN_L3); }

void setup() {
  Serial.begin(USB_BAUD);
  Serial1.begin(SERIAL_BAUD);
  for (int i = 0; i < 5; i++) {
    channels[i].startTime = 0;
    channels[i].isActive = false;
  }
  for (int i = 0; i < MAX_QUEUE_SIZE; i++) {
    eventQueue[i] = {0,0,0};
  }
  pinMode(PIN_HB, INPUT);
  pinMode(PIN_L1, INPUT);
  pinMode(PIN_L2, INPUT);
  pinMode(PIN_L3, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_HB), isrHB, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_L1), isrL1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_L2), isrL2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_L3), isrL3, CHANGE);
  if (DEBUG) {
    Serial.println("Pulse capture initialized.");
  }
}

void loop() {
  Event evt;
  while (dequeueEvent(evt)) {
    sendPacket(evt.channelID, evt.pulseWidth, evt.timestamp);
  }
}
