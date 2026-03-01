-- ============================================================
-- baud_gen.vhd
-- Baud rate generator for UART communication.
-- Produces a single-cycle tick at the configured baud rate
-- from the 50 MHz DE0-Nano-SoC master clock.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;          

ENTITY baud_gen IS
    GENERIC (
        CLK_FREQ  : INTEGER := 50_000_000;   -- Input clock frequency in Hz
        BAUD_RATE : INTEGER := 115_200       -- Target baud rate
    );
    PORT (
        clk       : IN  STD_LOGIC;           -- 50 MHz master clock
        rst       : IN  STD_LOGIC;           -- Synchronous reset (active high)
        baud_tick : OUT STD_LOGIC            -- Single-cycle tick output
    );
END baud_gen;

ARCHITECTURE rtl OF baud_gen IS
    -- Calculate the divisor at synthesis time.
    CONSTANT DIVISOR : INTEGER := CLK_FREQ / BAUD_RATE - 1;                                                   

    -- The counter signal.
    SIGNAL counter : INTEGER RANGE 0 TO DIVISOR := 0;
BEGIN

    -- --------------------------------------------------------
    -- Process: tick_proc
    -- A clocked process that increments the counter on every
    -- rising edge of the 50 MHz clock. When the counter reaches
    -- the divisor value, it resets to 0 and asserts baud_tick
    -- for one cycle.
    -- --------------------------------------------------------
    tick_proc : PROCESS(clk)
    BEGIN
        IF rising_edge(clk) THEN
            IF rst = '1' THEN
                -- Synchronous reset: bring everything to a known state
                counter   <= 0;
                baud_tick <= '0';

            ELSIF counter = DIVISOR THEN
                -- We've counted 434 clock cycles — one bit period elapsed
                counter   <= 0;
                baud_tick <= '1';    -- Pulse HIGH for this one cycle

            ELSE
                -- Normal counting
                counter   <= counter + 1;
                baud_tick <= '0';    -- Keep tick LOW while counting
            END IF;
        END IF;
    END PROCESS;

END rtl;