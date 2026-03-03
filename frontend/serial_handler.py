"""
serial_handler.py
Simple and robust one-byte UART transaction handler.
"""

from __future__ import annotations

import re
import time
from typing import Optional

import serial
import serial.tools.list_ports


def _port_sort_key(name: str) -> tuple[int, str]:
    match = re.match(r"^COM(\d+)$", name.upper())
    if match:
        return (0, f"{int(match.group(1)):06d}")
    return (1, name.upper())


class SerialHandler:
    """Manages a serial connection to the FPGA."""

    def __init__(
        self,
        port: str = "",
        baudrate: int = 115200,
        timeout: float = 0.20,
        write_timeout: float = 0.20,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.connection: Optional[serial.Serial] = None
        self.last_error = ""

    @staticmethod
    def list_available_ports() -> list[str]:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return sorted(ports, key=_port_sort_key)

    def connect(self, port: str = "") -> bool:
        if port:
            self.port = port
        if not self.port:
            self.last_error = "No port selected."
            return False

        self.disconnect()
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            time.sleep(0.1)
            self.clear_buffers()
            self.last_error = ""
            return True
        except serial.SerialException as exc:
            self.connection = None
            self.last_error = f"Connection failed: {exc}"
            return False

    def disconnect(self):
        if self.connection and self.connection.is_open:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_open

    def clear_buffers(self):
        if not self.is_connected():
            return
        try:
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
        except serial.SerialException as exc:
            self.last_error = f"Buffer reset failed: {exc}"

    def send_byte(self, byte_val: int) -> bool:
        if not self.is_connected():
            self.last_error = "Serial not connected."
            return False
        try:
            written = self.connection.write(bytes([byte_val & 0xFF]))
            if written != 1:
                self.last_error = "Incomplete write."
                return False
            return True
        except serial.SerialTimeoutException:
            self.last_error = "Serial write timeout."
            return False
        except serial.SerialException as exc:
            self.last_error = f"Serial write failed: {exc}"
            return False

    def receive_byte(self, timeout_override: Optional[float] = None) -> Optional[int]:
        if not self.is_connected():
            self.last_error = "Serial not connected."
            return None

        old_timeout = self.connection.timeout
        try:
            if timeout_override is not None:
                self.connection.timeout = timeout_override
            data = self.connection.read(1)
            if len(data) == 1:
                return data[0]
            self.last_error = "Read timeout."
            return None
        except serial.SerialException as exc:
            self.last_error = f"Serial read failed: {exc}"
            return None
        finally:
            if timeout_override is not None and self.connection:
                self.connection.timeout = old_timeout

    def send_and_receive_detailed(
        self,
        byte_val: int,
        retries: int = 1,
        read_timeout: Optional[float] = None,
        inter_byte_gap: float = 0.002,
        clear_stale_input: bool = True,
    ) -> tuple[Optional[int], int]:
        if not self.is_connected():
            self.last_error = "Serial not connected."
            return None, 0

        rx_timeout = read_timeout if read_timeout is not None else self.timeout
        attempts = 0
        for attempts in range(1, retries + 2):
            if clear_stale_input:
                try:
                    self.connection.reset_input_buffer()
                except serial.SerialException:
                    pass

            if not self.send_byte(byte_val):
                break

            result = self.receive_byte(timeout_override=rx_timeout)
            if result is not None:
                if inter_byte_gap > 0:
                    time.sleep(inter_byte_gap)
                return result, attempts

            time.sleep(0.005)

        if inter_byte_gap > 0:
            time.sleep(inter_byte_gap)
        return None, attempts

    def send_and_receive(
        self,
        byte_val: int,
        retries: int = 1,
        read_timeout: Optional[float] = None,
        inter_byte_gap: float = 0.002,
        clear_stale_input: bool = False,
    ) -> Optional[int]:
        value, _ = self.send_and_receive_detailed(
            byte_val=byte_val,
            retries=retries,
            read_timeout=read_timeout,
            inter_byte_gap=inter_byte_gap,
            clear_stale_input=clear_stale_input,
        )
        return value
