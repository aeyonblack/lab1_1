"""
serial_handler.py
Serial port communication handler for UART interaction with the FPGA.
"""

import serial
import serial.tools.list_ports
import time
from typing import Optional


class SerialHandler:
    """Manages the serial connection to the FPGA via a USB-to-Serial adapter."""

    def __init__(self, port: str = "", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None

    @staticmethod
    def list_available_ports() -> list[str]:
        """Return a list of available COM port names."""
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    def connect(self, port: str = "") -> bool:
        """
        Open the serial connection.
        Returns True on success, False on failure.
        """
        if port:
            self.port = port
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,     # 8 data bits
                parity=serial.PARITY_NONE,      # No parity
                stopbits=serial.STOPBITS_ONE,   # 1 stop bit
                timeout=self.timeout
            )
            # Small delay to let the connection stabilise
            time.sleep(0.1)
            # Flush any stale data in the buffers
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
            return True
        except serial.SerialException as e:
            print(f"Connection failed:{e}")
            return False

    def disconnect(self):
        """Close the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """Check if the serial port is open."""
        return self.connection is not None and self.connection.is_open

    def send_byte(self, byte_val: int) -> bool:
        """Send a single byte to the FPGA."""
        if not self.is_connected():
            return False
        try:
            self.connection.write(bytes([byte_val & 0xFF]))
            return True
        except serial.SerialException:
            return False

    def receive_byte(self) -> Optional[int]:
        """
        Read a single byte from the FPGA.
        Returns the byte value (0-255), or None on timeout/error.
        """
        if not self.is_connected():
            return None
        try:
            data = self.connection.read(1)
            if len(data) == 1:
                return data[0]
            return None  # Timeout
        except serial.SerialException:
            return None

    def send_and_receive(self, byte_val: int) -> Optional[int]:
        """
        Send a byte and wait for the FPGA's response.
        This is the core transaction for our practical.
        """
        if not self.send_byte(byte_val):
            return None
        return self.receive_byte()