-- ============================================================
-- uart_rx.vhd
-- UART Receiver with 16x oversampling.
-- Deserialises an 8N1 serial stream into parallel bytes.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

ENTITY uart_rx IS
    PORT (
        clk     : IN  STD_LOGIC;
        rst     : IN  STD_LOGIC;
        rx      : IN  STD_LOGIC;                          -- Serial input line
        os_tick : IN  STD_LOGIC;                          -- 16x oversample tick
        rx_data : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);       -- Received byte
        rx_done : OUT STD_LOGIC                           -- Pulse: byte ready
    );
END uart_rx;

ARCHITECTURE rtl OF uart_rx IS

    -- State machine states
    TYPE state_type IS (IDLE, START, DATA, STOP);
    SIGNAL state : state_type := IDLE;

    -- Oversample counter: counts 0..15 within each bit period
    SIGNAL os_count : INTEGER RANGE 0 TO 15 := 0;

    -- Bit index: which of the 8 data bits we are currently receiving
    SIGNAL bit_idx : INTEGER RANGE 0 TO 7 := 0;

    -- Shift register: holds the byte as it is assembled bit-by-bit
    SIGNAL shift_reg : STD_LOGIC_VECTOR(7 DOWNTO 0) := (OTHERS => '0');

    -- Two-flop synchronizer for asynchronous RX input.
    -- This reduces metastability risk before the UART FSM uses rx.
    SIGNAL rx_sync_0 : STD_LOGIC := '1';
    SIGNAL rx_sync_1 : STD_LOGIC := '1';

BEGIN

    rx_proc : PROCESS(clk)
    BEGIN
        IF rising_edge(clk) THEN
            IF rst = '1' THEN
                state     <= IDLE;
                os_count  <= 0;
                bit_idx   <= 0;
                shift_reg <= (OTHERS => '0');
                rx_done   <= '0';
                rx_data   <= (OTHERS => '0');
                rx_sync_0 <= '1';
                rx_sync_1 <= '1';

            ELSE
                -- Synchronize RX to the local clock domain every cycle.
                rx_sync_0 <= rx;
                rx_sync_1 <= rx_sync_0;

                IF os_tick = '1' THEN
                    -- We only advance the state machine on oversample ticks.
                    -- Between ticks, everything holds its value.

                    -- Default: rx_done is LOW unless we explicitly set it
                    rx_done <= '0';

                    CASE state IS

                        -- ========================================
                        -- IDLE: Line is HIGH. Wait for it to drop.
                        -- ========================================
                        WHEN IDLE =>
                            os_count <= 0;
                            bit_idx  <= 0;
                            IF rx_sync_1 = '0' THEN
                                -- Falling edge detected this is a potential start bit
                                state <= START;
                            END IF;

                        -- ========================================
                        -- START: Confirm the start bit is real.
                        -- We wait 7 oversample ticks to reach the
                        -- CENTRE of the start bit, then verify
                        -- the line is still LOW.
                        -- ========================================
                        WHEN START =>
                            IF os_count = 7 THEN
                                os_count <= 0;
                                IF rx_sync_1 = '0' THEN
                                    -- Confirmed: line is still LOW at centre
                                    -- We are now aligned to bit centres
                                    state <= DATA;
                                ELSE
                                    -- False start (noise glitch)
                                    state <= IDLE;
                                END IF;
                            ELSE
                                os_count <= os_count + 1;
                            END IF;

                        -- ========================================
                        -- DATA: Sample each of the 8 data bits at
                        -- the centre of the bit period (every 16
                        -- oversample ticks after alignment).
                        -- ========================================
                        WHEN DATA =>
                            IF os_count = 15 THEN
                                os_count <= 0;

                                -- Sample the bit and store it.
                                -- LSB first: bit 0 arrives first, so we
                                -- shift right and place the new bit at MSB,
                                -- building the byte from right to left.
                                shift_reg <= rx_sync_1 & shift_reg(7 DOWNTO 1);

                                IF bit_idx = 7 THEN
                                    -- All 8 bits received
                                    bit_idx <= 0;
                                    state   <= STOP;
                                ELSE
                                    bit_idx <= bit_idx + 1;
                                END IF;
                            ELSE
                                os_count <= os_count + 1;
                            END IF;

                        -- ========================================
                        -- STOP: Wait for the stop bit (HIGH).
                        -- After 16 ticks, output the byte only if
                        -- stop bit is valid.
                        -- ========================================
                        WHEN STOP =>
                            IF os_count = 15 THEN
                                os_count <= 0;
                                IF rx_sync_1 = '1' THEN
                                    rx_data <= shift_reg;   -- Latch completed byte
                                    rx_done <= '1';         -- Signal: byte is ready
                                END IF;
                                state <= IDLE;
                            ELSE
                                os_count <= os_count + 1;
                            END IF;

                    END CASE;
                ELSE
                    -- No oversample tick this cycle — hold rx_done LOW
                    rx_done <= '0';
                END IF;
            END IF;
        END IF;
    END PROCESS;

END rtl;
