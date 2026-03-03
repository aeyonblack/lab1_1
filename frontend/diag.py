"""
diag.py — Minimal UART diagnostic (no PyGame).
Run: python diag.py COM8
"""
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM8"
BAUD = 115200

print(f"Opening {PORT} at {BAUD}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=2.0)
except Exception as e:
    print(f"FAILED to open: {e}")
    sys.exit(1)

time.sleep(0.2)
ser.reset_input_buffer()
ser.reset_output_buffer()
print(f"Port open. DTR={ser.dtr}, RTS={ser.rts}")

# Test 1: Send a single byte and wait
test_byte = 0xA3
print(f"\n--- Test 1: Send 0x{test_byte:02X}, wait 2s for response ---")
ser.write(bytes([test_byte]))
time.sleep(0.1)  # Give FPGA time
response = ser.read(1)
if response:
    print(f"  Received: 0x{response[0]:02X} (binary: {response[0]:08b})")
else:
    print("  TIMEOUT — no response received.")

# Check if there's extra data in the buffer
extra = ser.read(10)
if extra:
    print(f"  Extra bytes in buffer: {[f'0x{b:02X}' for b in extra]}")

# Test 2: Send 5 bytes one-at-a-time with generous delays
print(f"\n--- Test 2: Send 5 bytes with 200ms gaps ---")
test_bytes = [0x00, 0xFF, 0xA3, 0x55, 0x01]
for i, tb in enumerate(test_bytes):
    ser.reset_input_buffer()
    time.sleep(0.05)
    ser.write(bytes([tb]))
    time.sleep(0.2)
    resp = ser.read(1)
    if resp:
        print(f"  [{i}] Sent 0x{tb:02X} -> Received 0x{resp[0]:02X}  {'OK' if resp[0] != tb else 'ECHO (no shift?)'}")
    else:
        print(f"  [{i}] Sent 0x{tb:02X} -> TIMEOUT")

# Test 3: Check what's on the line when we just listen
print(f"\n--- Test 3: Listen for 1s (no send) ---")
ser.reset_input_buffer()
noise = ser.read(100)
if noise:
    print(f"  Unsolicited data: {[f'0x{b:02X}' for b in noise]}")
    print("  ^ This means the FPGA is transmitting without being asked (possible reset/noise issue)")
else:
    print("  Line is quiet (good).")

ser.close()
print("\nDone. Port closed.")
