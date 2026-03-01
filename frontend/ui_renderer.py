"""
ui_renderer.py
PyGame rendering functions for the UART test interface.
"""

import pygame

# Colour palette
BG_COLOUR      = (30, 30, 40)       # Dark blue-grey background
HEADER_COLOUR  = (70, 130, 220)     # Blue for headers
TEXT_COLOUR     = (220, 220, 230)    # Light grey for body text
SUCCESS_COLOUR = (80, 200, 120)     # Green for correct bytes
ERROR_COLOUR   = (220, 80, 80)      # Red for errors
ACCENT_COLOUR  = (255, 200, 60)     # Yellow for highlights
DIM_COLOUR     = (120, 120, 130)    # Dimmed text


def init_fonts() -> dict:
    """Load and return the fonts used throughout the UI."""
    pygame.font.init()
    return {
        "title": pygame.font.SysFont("Consolas", 28, bold=True),
        "header": pygame.font.SysFont("Consolas", 20, bold=True),
        "body": pygame.font.SysFont("Consolas", 16),
        "small": pygame.font.SysFont("Consolas", 13),
    }


def draw_header(surface: pygame.Surface, fonts: dict, port: str, connected: bool):
    """Draw the top header bar with connection status."""
    # Title
    title_surf = fonts["title"].render("EAS 410 — UART Test Application", True, HEADER_COLOUR)
    surface.blit(title_surf, (20, 15))

    # Connection status
    status_text = f"Connected:{port}" if connected else "Disconnected"
    status_colour = SUCCESS_COLOUR if connected else ERROR_COLOUR
    status_surf = fonts["body"].render(status_text, True, status_colour)
    surface.blit(status_surf, (20, 50))


def draw_config(surface: pygame.Surface, fonts: dict, sw0: int, sw1: int, y_start: int) -> int:
    """Draw the switch configuration section. Returns the next Y position."""
    y = y_start
    header = fonts["header"].render("Switch Configuration", True, ACCENT_COLOUR)
    surface.blit(header, (20, y))
    y += 30

    shift_labels = {
        (0, 0): "Rotate LEFT by 1",
        (0, 1): "Rotate RIGHT by 1",
        (1, 0): "Rotate LEFT by 2",
        (1, 1): "Rotate RIGHT by 2",
    }
    label = shift_labels.get((sw1, sw0), "Unknown")

    config_text = f"SW1={sw1}  SW0={sw0}  →{label}"
    config_surf = fonts["body"].render(config_text, True, TEXT_COLOUR)
    surface.blit(config_surf, (20, y))
    y += 30
    return y


def draw_results_table(
    surface: pygame.Surface,
    fonts: dict,
    results: list[dict],
    y_start: int,
    scroll_offset: int = 0,
    max_visible: int = 20,
) -> int:
    """
    Draw the byte results table.
    Each result is a dict: {index, sent, expected, received, correct}
    Returns the next Y position.
    """
    y = y_start
    header = fonts["header"].render("Results", True, ACCENT_COLOUR)
    surface.blit(header, (20, y))
    y += 25

    # Column headers
    col_header = fonts["small"].render(
        f"{'#':>3}{'Sent':>10}{'Expected':>10}{'Received':>10}{'Status':>8}", True, DIM_COLOUR
    )
    surface.blit(col_header, (20, y))
    y += 20

    # Draw a horizontal line
    pygame.draw.line(surface, DIM_COLOUR, (20, y), (600, y))
    y += 5

    # Rows
    visible_results = results[scroll_offset : scroll_offset + max_visible]
    for r in visible_results:
        status = "OK" if r["correct"] else "ERR"
        colour = SUCCESS_COLOUR if r["correct"] else ERROR_COLOUR

        sent_bin = format(r["sent"], "08b")
        exp_bin = format(r["expected"], "08b")
        recv_str = format(r["received"], "08b") if r["received"] is not None else "TIMEOUT "

        row_text = f"{r['index']:>3}{sent_bin}{exp_bin}{recv_str}{status:>8}"
        row_surf = fonts["small"].render(row_text, True, colour)
        surface.blit(row_surf, (20, y))
        y += 18

    return y


def draw_summary(
    surface: pygame.Surface,
    fonts: dict,
    total: int,
    correct: int,
    elapsed_time: float,
    y_start: int,
):
    """Draw the summary statistics at the bottom."""
    y = y_start + 10
    pygame.draw.line(surface, DIM_COLOUR, (20, y - 5), (600, y - 5))

    if total > 0:
        success_rate = (correct / total) * 100
        # Approximate baud rate: each transaction is 10 bits TX + 10 bits RX = 20 bits
        # total bits = total_bytes * 20, time = elapsed_time seconds
        if elapsed_time > 0:
            approx_baud = (total * 20) / elapsed_time
        else:
            approx_baud = 0

        summary_lines = [
            f"Total:{total}    Correct:{correct}    Errors:{total - correct}    Success Rate:{success_rate:.1f}%",
            f"Elapsed:{elapsed_time:.3f}s    Approx Baud Rate:{approx_baud:,.0f} bits/s",
        ]
    else:
        summary_lines = ["No data yet. Press SPACE to start the test."]

    for line in summary_lines:
        surf = fonts["body"].render(line, True, TEXT_COLOUR)
        surface.blit(surf, (20, y))
        y += 25


def draw_controls(surface: pygame.Surface, fonts: dict, y_start: int):
    """Draw the keyboard control hints."""
    y = y_start + 10
    controls = [
        "[SPACE] Run Test    [C] Connect    [1-9] Set COM Port    [Q] Quit",
        "[UP/DOWN] Scroll    [S] Toggle SW0    [D] Toggle SW1",
    ]
    for line in controls:
        surf = fonts["small"].render(line, True, DIM_COLOUR)
        surface.blit(surf, (20, y))
        y += 18