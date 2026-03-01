"""
main.py
EAS 410 Practical 1 — UART Test Application.
Generates random bytes, sends them to the FPGA via serial,
validates the circular bit shift, and displays results.
"""

import pygame
import random
import time
import sys

from serial_handler import SerialHandler
from shift_logic import circular_shift
from ui_renderer import (
    init_fonts, draw_header, draw_config,
    draw_results_table, draw_summary, draw_controls,
    BG_COLOUR,
)

# ============================================================
# Constants
# ============================================================
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700
NUM_BYTES = 50
FPS = 30


def run_test(serial_handler: SerialHandler, sw0: int, sw1: int) -> tuple[list[dict], float]:
    """
    Send NUM_BYTES random bytes to the FPGA and collect results.

    Returns:
        results: List of result dicts
        elapsed: Total time in seconds
    """
    results = []
    random_bytes = [random.randint(0, 255) for _ in range(NUM_BYTES)]

    start_time = time.time()

    for i, sent_byte in enumerate(random_bytes):
        expected = circular_shift(sent_byte, sw0, sw1)
        received = serial_handler.send_and_receive(sent_byte)

        results.append({
            "index": i + 1,
            "sent": sent_byte,
            "expected": expected,
            "received": received,
            "correct": received == expected,
        })

    elapsed = time.time() - start_time
    return results, elapsed


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("EAS 410 — UART Bit Shift Tester")
    clock = pygame.time.Clock()
    fonts = init_fonts()

    # State
    serial_handler = SerialHandler()
    sw0 = 0
    sw1 = 0
    results: list[dict] = []
    elapsed_time = 0.0
    total = 0
    correct = 0
    scroll_offset = 0
    com_port_num = 3  # Default COM3

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False

                elif event.key == pygame.K_c:
                    # Connect / reconnect
                    port = f"COM{com_port_num}"
                    if serial_handler.is_connected():
                        serial_handler.disconnect()
                    serial_handler.connect(port)

                elif event.key in range(pygame.K_1, pygame.K_9 + 1):
                    # Set COM port number
                    com_port_num = event.key - pygame.K_0

                elif event.key == pygame.K_SPACE:
                    # Run the test
                    if serial_handler.is_connected():
                        results, elapsed_time = run_test(serial_handler, sw0, sw1)
                        total = len(results)
                        correct = sum(1 for r in results if r["correct"])
                        scroll_offset = 0

                elif event.key == pygame.K_s:
                    sw0 = 1 - sw0  # Toggle

                elif event.key == pygame.K_d:
                    sw1 = 1 - sw1  # Toggle

                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - 1)

                elif event.key == pygame.K_DOWN:
                    scroll_offset = min(max(0, len(results) - 20), scroll_offset + 1)

        # ========================================
        # Render
        # ========================================
        screen.fill(BG_COLOUR)

        draw_header(screen, fonts, f"COM{com_port_num}", serial_handler.is_connected())
        y = draw_config(screen, fonts, sw0, sw1, y_start=85)
        y = draw_results_table(screen, fonts, results, y_start=y + 5, scroll_offset=scroll_offset)
        draw_summary(screen, fonts, total, correct, elapsed_time, y_start=y + 5)
        draw_controls(screen, fonts, y_start=WINDOW_HEIGHT - 55)

        pygame.display.flip()
        clock.tick(FPS)

    # Cleanup
    serial_handler.disconnect()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()