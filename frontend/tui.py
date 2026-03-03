"""
tui.py — Terminal UI for EAS 410 UART Bit-Shift Tester.

Usage:
    python tui.py              (interactive menu)
    python tui.py --port COM8  (skip port selection)

Depends on: serial_handler.py, shift_logic.py (PyGame-free).
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from typing import Optional

from serial_handler import SerialHandler
from shift_logic import circular_shift

# ── ANSI helpers ────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# Enable ANSI on Windows 10+
if sys.platform == "win32":
    os.system("")


def coloured(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"


# ── Shift mode helpers ──────────────────────────────────────
SHIFT_TABLE = {
    (0, 0): "Rotate LEFT  by 1",
    (0, 1): "Rotate RIGHT by 1",
    (1, 0): "Rotate LEFT  by 2",
    (1, 1): "Rotate RIGHT by 2",
}


def print_header():
    print()
    print(coloured("═" * 56, CYAN))
    print(coloured("  EAS 410 — UART Circular Bit-Shift Tester (TUI)", BOLD))
    print(coloured("═" * 56, CYAN))


def print_shift_mode(sw0: int, sw1: int):
    label = SHIFT_TABLE[(sw1, sw0)]
    print(f"  Shift mode : SW1={sw1} SW0={sw0} → {coloured(label, YELLOW)}")


# ── Auto batch test ─────────────────────────────────────────
def run_batch(
    handler: SerialHandler,
    sw0: int,
    sw1: int,
    count: int = 50,
) -> None:
    """Generate `count` random bytes, send each to the FPGA, validate."""
    print()
    print(coloured(f"── Batch Test: {count} random bytes ──", BOLD))
    print_shift_mode(sw0, sw1)
    print()

    # Table header
    hdr = f"{'#':>3}  {'Sent':>12}  {'Expected':>12}  {'Received':>12}  {'Status':>8}"
    print(coloured(hdr, DIM))
    print(coloured("─" * 56, DIM))

    ok = 0
    err = 0
    timeouts = 0
    handler.clear_buffers()
    start = time.perf_counter()

    for i in range(1, count + 1):
        sent = random.randint(0, 255)
        expected = circular_shift(sent, sw0, sw1)
        received = handler.send_and_receive(sent, retries=2, inter_byte_gap=0.005)

        sent_str = f"0x{sent:02X} {sent:08b}"
        exp_str  = f"0x{expected:02X} {expected:08b}"

        if received is None:
            recv_str = "  TIMEOUT   "
            status = coloured("TIMEOUT", RED)
            timeouts += 1
        elif received == expected:
            recv_str = f"0x{received:02X} {received:08b}"
            status = coloured("     OK", GREEN)
            ok += 1
        else:
            recv_str = f"0x{received:02X} {received:08b}"
            status = coloured("    ERR", RED)
            err += 1

        print(f"{i:>3}  {sent_str}  {exp_str}  {recv_str}  {status}")

    elapsed = time.perf_counter() - start
    total = ok + err + timeouts
    rate = (ok / total * 100) if total else 0

    print(coloured("─" * 56, DIM))
    print()
    print(coloured("  Summary", BOLD))
    print(f"  Total     : {total}")
    print(f"  Correct   : {coloured(str(ok), GREEN)}")
    print(f"  Errors    : {coloured(str(err), RED) if err else '0'}")
    print(f"  Timeouts  : {coloured(str(timeouts), RED) if timeouts else '0'}")
    print(f"  Success   : {coloured(f'{rate:.1f}%', GREEN if rate == 100 else YELLOW)}")
    print(f"  Elapsed   : {elapsed:.3f}s")
    if elapsed > 0:
        bits = total * 20  # 10 bits TX + 10 bits RX per byte
        print(f"  Throughput: {bits / elapsed:,.0f} bits/s  (effective)")
    print()


# ── Manual single-byte test ────────────────────────────────
def run_manual(handler: SerialHandler, sw0: int, sw1: int) -> None:
    """Prompt user for hex bytes, send one at a time."""
    print()
    print(coloured("── Manual Mode ──", BOLD))
    print_shift_mode(sw0, sw1)
    print(f"  Type a hex byte (e.g. A3) and press Enter.")
    print(f"  Type {coloured('q', YELLOW)} to return to menu.\n")

    while True:
        raw = input(f"  {coloured('TX>', CYAN)} ").strip()
        if raw.lower() in ("q", "quit", "exit", ""):
            break

        try:
            sent = int(raw, 16) & 0xFF
        except ValueError:
            print(coloured("    Invalid hex. Try again.", RED))
            continue

        expected = circular_shift(sent, sw0, sw1)
        t0 = time.perf_counter()
        received = handler.send_and_receive(sent, retries=2, inter_byte_gap=0.005)
        latency = (time.perf_counter() - t0) * 1000

        exp_str = f"0x{expected:02X} ({expected:08b})"

        if received is None:
            print(f"    Sent 0x{sent:02X} ({sent:08b})")
            print(f"    Expected {exp_str}")
            print(f"    Received {coloured('TIMEOUT', RED)}  [{latency:.1f}ms]")
        elif received == expected:
            print(f"    Sent 0x{sent:02X} ({sent:08b})")
            print(f"    Expected {exp_str}")
            print(f"    Received 0x{received:02X} ({received:08b})  {coloured('OK', GREEN)}  [{latency:.1f}ms]")
        else:
            print(f"    Sent 0x{sent:02X} ({sent:08b})")
            print(f"    Expected {exp_str}")
            print(f"    Received 0x{received:02X} ({received:08b})  {coloured('MISMATCH', RED)}  [{latency:.1f}ms]")
        print()


# ── Interactive menu ────────────────────────────────────────
def menu_loop(handler: SerialHandler, initial_port: str):
    sw0, sw1 = 0, 0
    port = initial_port

    while True:
        print_header()
        connected = handler.is_connected()
        if connected:
            print(f"  Port       : {coloured(port, GREEN)}  (connected)")
        else:
            print(f"  Port       : {coloured(port or 'none', RED)}  (disconnected)")
        print_shift_mode(sw0, sw1)

        print()
        print(f"  {coloured('[1]', CYAN)} Auto batch test (50 bytes)")
        print(f"  {coloured('[2]', CYAN)} Manual send mode")
        print(f"  {coloured('[3]', CYAN)} Change COM port         (current: {port})")
        print(f"  {coloured('[4]', CYAN)} Toggle SW0               (current: {sw0})")
        print(f"  {coloured('[5]', CYAN)} Toggle SW1               (current: {sw1})")
        if connected:
            print(f"  {coloured('[6]', CYAN)} Disconnect")
        else:
            print(f"  {coloured('[6]', CYAN)} Connect")
        print(f"  {coloured('[7]', CYAN)} List available ports")
        print(f"  {coloured('[q]', CYAN)} Quit")
        print()

        choice = input(f"  {coloured('>', CYAN)} ").strip().lower()

        if choice == "1":
            if not connected:
                print(coloured("  ✗ Not connected. Connect first.", RED))
                continue
            run_batch(handler, sw0, sw1)
            input(coloured("  Press Enter to continue...", DIM))

        elif choice == "2":
            if not connected:
                print(coloured("  ✗ Not connected. Connect first.", RED))
                continue
            run_manual(handler, sw0, sw1)

        elif choice == "3":
            new_port = input(f"  Enter port name (e.g. COM8): ").strip()
            if new_port:
                if handler.is_connected():
                    handler.disconnect()
                port = new_port
                ok = handler.connect(port)
                if ok:
                    print(coloured(f"  ✓ Connected to {port}.", GREEN))
                else:
                    print(coloured(f"  ✗ {handler.last_error}", RED))
            time.sleep(0.5)

        elif choice == "4":
            sw0 = 1 - sw0
            print(f"  SW0 → {sw0}")
            time.sleep(0.3)

        elif choice == "5":
            sw1 = 1 - sw1
            print(f"  SW1 → {sw1}")
            time.sleep(0.3)

        elif choice == "6":
            if connected:
                handler.disconnect()
                print(coloured("  Disconnected.", YELLOW))
            else:
                if not port:
                    port = input("  Enter port name (e.g. COM8): ").strip()
                ok = handler.connect(port)
                if ok:
                    print(coloured(f"  ✓ Connected to {port}.", GREEN))
                else:
                    print(coloured(f"  ✗ {handler.last_error}", RED))
            time.sleep(0.5)

        elif choice == "7":
            ports = SerialHandler.list_available_ports()
            if ports:
                print(f"  Available: {', '.join(ports)}")
            else:
                print(coloured("  No serial ports found.", RED))
            time.sleep(1)

        elif choice in ("q", "quit", "exit"):
            break

        else:
            print(coloured("  Invalid choice.", RED))
            time.sleep(0.3)


# ── Entry point ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="EAS 410 UART Tester (TUI)")
    parser.add_argument("--port", "-p", default="COM8", help="Serial port (default: COM8)")
    parser.add_argument("--baud", "-b", type=int, default=115200, help="Baud rate")
    args = parser.parse_args()

    handler = SerialHandler(baudrate=args.baud)

    # Auto-connect on start
    if args.port:
        ok = handler.connect(args.port)
        if ok:
            print(coloured(f"  ✓ Connected to {args.port}.", GREEN))
        else:
            print(coloured(f"  ✗ Could not connect to {args.port}: {handler.last_error}", RED))

    try:
        menu_loop(handler, args.port)
    except KeyboardInterrupt:
        print("\n  Interrupted.")
    finally:
        handler.disconnect()
        print(coloured("  Goodbye.", DIM))


if __name__ == "__main__":
    main()
