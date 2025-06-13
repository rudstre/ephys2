# Teensy Digital Input Multiplexer

Intan electrophysiology acquisition systems have a major limitation: **only 2 digital input channels by default**. In behavioral neuroscience experiments, you often need to record many more digital signals:

- Multiple lever presses
- Nose poke detectors  
- Reward delivery signals
- Stimulus presentation markers
- Behavioral state indicators
- Synchronization pulses

This system combines many behavioral inputs into a single channel. Events get encoded by a Teensy into a particular packet structure and sent over one wire. During post-processing, they are later de-multiplexed and you can retrieve a high number of signals from one digital input.

## Experimental Setup

### Hardware Connections

```
     OpCon Box                 Teensy 4.1             Intan System
┌─────────────────┐          ┌────────────┐          ┌─────────────┐
│ Heartbeat (17)  │ ────────▶│ Pin 5      │          │             │
│ Lever 1   (20)  │ ────────▶│ Pin 6      │          │             │
│ Lever 2   (37)  │ ────────▶│ Pin 9      │          │             │
│ Lever 3   (36)  │ ────────▶│ Pin 10     │          │             │
│                 │          │            │          │             │
│ Additional      │ ────────▶│ ...        │          │             │
│ Inputs...       │          │            │          │             │
│                 │          │            │          │             │
│ Common Ground   │ ────────▶│ GND        │ ────────▶│ GND         │
│                 │          │            │          │             │
│                 │          │ Pin 1 (TX) │ ────────▶│ Digital In 0│
└─────────────────┘          └────────────┘          └─────────────┘
```

## Practical Usage

### Step 1: Setup and Program the Teensy

#### Install Arduino IDE with Teensy Support
1. Download and install [Arduino IDE](https://www.arduino.cc/en/software) (version 1.8.19 or newer)
2. Download and install [Teensyduino](https://www.pjrc.com/teensy/td_download.html) 
   - Run the Teensyduino installer after Arduino IDE is installed
   - This adds Teensy support to Arduino IDE
3. Connect your Teensy to your computer via USB

#### Program the Teensy
1. Open Arduino IDE
2. Go to Tools → Board → Teensyduino → Teensy 4.1
3. Open `sig_multiplex/sig_multiplex.ino`
4. Upload to Teensy (the code uses default pin assignments)

**Default Pin Mapping (Digital Pins):**
- Digital Pin 5: Heartbeat/Channel 1
- Digital Pin 6: Lever 1/Channel 2  
- Digital Pin 9: Lever 2/Channel 3
- Digital Pin 10: Lever 3/Channel 4

*Note: These are digital pins (5, 6, 9, 10), not analog pins (A5, A6, etc.)*

![Teensy 4.1 Pinout](https://www.pjrc.com/teensy/card11a_rev3_web.png)

*Advanced: If you need different pins, see the Customization section below*

### Step 2: Connect Everything
1. Connect your behavioral equipment outputs to the assigned Teensy pins:
   - **OpCon Pin 17** → Teensy Pin 5 (Heartbeat/Channel 1)
   - **OpCon Pin 20** → Teensy Pin 6 (Lever 1/Channel 2) 
   - **OpCon Pin 37** → Teensy Pin 9 (Lever 2/Channel 3)
   - **OpCon Pin 36** → Teensy Pin 10 (Lever 3/Channel 4)
2. Run one wire from the Teensy (pin 1) to an Intan digital input
3. **Connect Teensy ground to your system ground** (very important for signal integrity)
   - **OpCon Ground** → Teensy Ground (essential for proper operation)
4. Plug in the Teensy with a USB cable

### Step 3: Record Your Experiment
- In your Intan software, make sure the digital input channel is enabled (the one connected to Teensy)
- Record your experiment normally - everything gets saved automatically
- No special setup needed in Intan

### Step 4: Decode During Analysis
Add to your ephys2 pipeline configuration:

```yaml
- input.rhd2000:
    sessions: /path/to/your/data.rhd
    datetime_pattern: "*_%y%m%d_%H%M%S"
    batch_size: 450000
    batch_overlap: 0
    aux_channels:
      - digital_in: [0]  # Intan digital channel with Teensy signal
        name: decoded_digital_in.h5
        decode_teensy: true  # <----- treats this as an input that needs to be decoded
        baud_rate: 3000 # <------ should always be 3000 to match the 30kHz intan sampling rate
```

The system will automatically:
- Decode the multiplexed signal
- Separate events by original channel
- Provide precise timestamps for each behavioral event
- Save results as `decoded_digital_in_teensy.h5`

## Understanding the Output

After decoding, you'll get separate event files for each channel:

```
session_0_decoded_digital_in_teensy.h5
├── channel_1/  # Heartbeat events
│   └── time: [timestamps of heartbeat signals]
├── channel_2/  # Lever 1 events  
│   └── time: [timestamps of lever 1 presses]
├── channel_3/  # Lever 2 events
│   └── time: [timestamps of lever 2 presses]
├── channel_4/  # Lever 3 events
│   └── time: [timestamps of lever 3 presses]
└── ...
```

Each timestamp corresponds to the exact moment the behavioral event occurred, synchronized with your neural recordings.

## Customizing the System

### Adding More Channels or Changing Pins

The system is easily modifiable to support different numbers of inputs or pin assignments. Here's how to customize it:

#### To Add More Input Channels:

1. **Modify Pin Definitions** in the Arduino code:
```cpp
// Add new pin definitions
const int PIN_L4 = 11;  // New lever 4 input
const int PIN_L5 = 12;  // New lever 5 input
```

2. **Add Channel IDs**:
```cpp
#define CHANNEL_L4  0x05  // Lever 4 events
#define CHANNEL_L5  0x06  // Lever 5 events
```

3. **Create ISR Functions**:
```cpp
void isrL4() { handlePulseEvent(CHANNEL_L4, PIN_L4); }
void isrL5() { handlePulseEvent(CHANNEL_L5, PIN_L5); }
```

4. **Add Setup Code**:
```cpp
pinMode(PIN_L4, INPUT);
pinMode(PIN_L5, INPUT);
attachInterrupt(digitalPinToInterrupt(PIN_L4), isrL4, CHANGE);
attachInterrupt(digitalPinToInterrupt(PIN_L5), isrL5, CHANGE);
```

5. **Expand Channel Array**: Change `ChannelState channels[5];` to `ChannelState channels[7];` (or however many channels you need)

#### To Change Pin Assignments:

Simply modify the pin definitions at the top of the Arduino code:
```cpp
const int PIN_HB = 2;   // Change heartbeat to pin 2
const int PIN_L1 = 3;   // Change lever 1 to pin 3
const int PIN_L2 = 4;   // Change lever 2 to pin 4
const int PIN_L3 = 7;   // Change lever 3 to pin 7
```

#### Pin Requirements:
- **Any digital pin** can be used (pins 0-23 on Teensy 4.1)
- **Avoid pins 0 and 1** (used for USB serial communication)
- **Pin 1 is reserved** for UART output to Intan
- All pins support hardware interrupts on Teensy 4.1

#### No Python Changes Needed:
The decoder automatically handles any number of channels - no modifications required on the analysis side!

## Experimental Considerations

### Timing Accuracy
- Event detection: ~0.1 millisecond accuracy
- Timing is consistent and suitable for behavioral analysis

### Limitations
- Maximum event rate: ~1000 events/second total
- Events need to last longer than 1ms
- Keep wires under 3 feet

### Validation
To verify the system is working:
1. Enable debug mode in Arduino code: `const bool DEBUG = true;`
2. Monitor serial output during recording
3. Check that event counts match your expectations
4. Validate timing against video or other reference signals

## Troubleshooting

### No Events Detected
- Check that wires are connected properly
- Make sure your behavioral equipment is actually generating signals (test with an LED or multimeter)
- Confirm Teensy is powered and programmed correctly

### Missing Events
- If you have very fast behavioral events (>1000/second), the system might miss some
- Check for loose connections or interference from other equipment
- Make sure behavioral events last longer than 1ms

### Timing Issues
- Make sure the communication speed settings match (should be 3000 by default)
- Check that your Intan is recording the digital input channel
- Compare event timing to video recordings to verify accuracy


## Technical Implementation Details

### Overview
This system converts behavioral equipment signals (TTL: 0V/3.3V digital pulses) into serial data (UART: timed bit sequences) that gets recorded by the Intan system and decoded during analysis.

**Key Terms:**
- **TTL (Transistor-Transistor Logic)**: Digital signals that represent information using voltage levels - 0V means "off/false" and 3.3V means "on/true". This is the standard way behavioral equipment (like lever presses, lick detectors) sends signals to recording systems.
- **UART (Universal Asynchronous Receiver-Transmitter)**: A method for sending data between devices by transmitting one bit at a time over a single wire. "Asynchronous" means the devices don't need a shared clock - timing is built into the data stream itself.
- **Baud rate**: How fast data is transmitted, measured in bits per second. Higher baud rates send data faster but require more precise timing.
- **ISR (Interrupt Service Routine)**: Special code that runs immediately when a hardware event occurs (like a voltage change), interrupting whatever the processor was doing. This provides microsecond-level response times instead of the millisecond delays of normal code.
- **Little-endian**: A way of storing multi-byte numbers where the least significant (smallest) byte comes first. For example, the number 1000 (0x03E8 in hex) would be stored as bytes [0xE8, 0x03].
- **Checksum**: A simple error-detection method where you add up all the bytes in a message. If the sum doesn't match what's expected, you know the data was corrupted during transmission.

### Arduino Implementation

#### Event Detection System
The Teensy uses hardware interrupts for precise event capture:
- **Rising edge detection**: When a signal goes from 0V to 3.3V (behavioral event starts), the system immediately records the exact time using the `micros()` function, which counts microseconds since the device started
- **Falling edge detection**: When the signal returns to 0V (event ends), the system calculates how long the pulse lasted and adds the complete event to a queue for transmission
- **Interrupt-driven processing**: Instead of constantly checking for events (called "polling"), the hardware automatically interrupts the processor when voltage changes occur. This is much faster - sub-microsecond response vs. millisecond delays with polling
- **Pin assignments**: PIN_HB=5 (heartbeat channel for system monitoring), PIN_L1=6, PIN_L2=9, PIN_L3=10 (three behavioral input channels)

#### Event Queue Management
Events are temporarily stored in a circular buffer before transmission:
- **Buffer size**: 16 events maximum (chosen as a power of 2 because this allows very fast mathematical operations using bit masking instead of slower division)
- **Thread safety**: Uses `noInterrupts()`/`interrupts()` functions to temporarily disable interrupts while modifying the queue, preventing data corruption if a new event arrives while processing an old one
- **Overflow protection**: If events arrive faster than they can be transmitted (>1000/second), the system drops the oldest events and keeps the newest ones, with debug messages to alert you
- **Queue indexing**: Uses efficient wraparound logic `queueHead = (queueHead + 1) & QUEUE_MASK` where QUEUE_MASK=15, so when the index reaches 16 it automatically wraps back to 0

#### Data Packet Structure
Each behavioral event becomes an 11-byte packet transmitted over UART:

```
Byte 0:     Start Marker (0xAA) - synchronization byte
Byte 1:     Channel ID (1=heartbeat, 2-4=behavioral channels)
Bytes 2-5:  Pulse Width (microseconds, little-endian 32-bit)
Bytes 6-9:  Wait Time (microseconds between event detection and transmission, little-endian 32-bit)
Byte 10:    Checksum (sum of bytes 1-9, modulo 256)
```

#### UART Communication
- **Baud rate**: 3000 bits per second (chosen specifically to match Intan's 30kHz sampling rate - this means each bit takes exactly 10 Intan samples, making decoding much cleaner)
- **Frame format**: Each byte is sent as 10 bits total: 1 start bit (always 0), 8 data bits (the actual information), and 1 stop bit (always 1). The start/stop bits help the receiver know where each byte begins and ends.
- **Encoding**: Multi-byte numbers use little-endian format, meaning the least significant (smallest) byte is transmitted first. This is a common convention that makes the math simpler.
- **Transmission timing**: Events are sent immediately when the main program loop processes the queue, typically within a few milliseconds of detection

#### Timing Precision
- **Event capture**: Hardware interrupts respond in less than 1 microsecond from when the voltage changes, much faster than human behavioral timescales
- **Timer resolution**: The `micros()` function uses a 32-bit counter that increments every microsecond, providing 1-microsecond timing precision
- **Overflow handling**: Since 32-bit counters reset to zero every ~70 minutes (2^32 microseconds), the system detects and compensates for these rollovers to maintain accurate timing
- **Processing delays**: The "wait time" field in each packet records exactly how long elapsed between when the event was detected and when the packet was transmitted, allowing the decoder to reconstruct the precise original event timing

### Python Decoder Implementation

#### Three-Stage Decoding Process

**Stage 1: TTL to UART Conversion** (`decode_uart_from_ttl`)
- **Edge detection**: Looks for falling edges (voltage drops from 3.3V to 0V) which indicate the start of a UART byte transmission
- **Bit timing**: Calculates exactly how many Intan samples each bit should last (`bit_samples = 30000 Hz / 3000 baud = 10 samples per bit`)
- **Sample alignment**: Instead of sampling at the bit edges where noise is highest, samples each bit at its temporal center (5 samples after the bit starts) for maximum reliability
- **Frame validation**: Checks that the start bit is actually 0 and the stop bit is actually 1, at the correct timing intervals. Invalid frames are discarded.
- **Bit extraction**: Converts the 8 data bits into a byte value, using LSB-first encoding (the first bit transmitted represents the smallest value: 1, 2, 4, 8, 16, 32, 64, 128)

**Stage 2: Packet Assembly** (`decode_serial_packets`)
- **Synchronization**: Searches through the stream of decoded bytes looking for the start marker (0xAA = 170 in decimal = 10101010 in binary) which indicates the beginning of each 11-byte packet
- **Packet validation**: Once a start marker is found, collects exactly 11 bytes and verifies the packet structure is correct
- **Checksum verification**: Adds up bytes 1-9 of the packet and compares to byte 10 (the checksum). If they don't match modulo 256, the packet was corrupted and is discarded
- **Data conversion**: Converts the little-endian microsecond timing values back into milliseconds for easier analysis (divides by 1000)
- **Error recovery**: If a packet fails validation, the system doesn't crash - it just skips that packet and continues looking for the next start marker

**Stage 3: Event Reconstruction** (`deserialize_teensy`)
- **Timing correction**: Applies a 0.36ms constant offset to all timestamps to compensate for the small delays introduced by processing and transmission (this offset was measured empirically)
- **Event reconstruction**: Takes the pulse width and timing information from each packet and recreates the original behavioral events as binary arrays (1 = event active, 0 = no event)
- **Sparse storage**: Instead of storing every time point, only stores the times when events actually occurred, which is much more memory-efficient for long recordings with infrequent events
- **Chunk handling**: Large datasets are processed in chunks (smaller pieces), and this stage carefully manages event boundaries so no events are lost when chunks are combined