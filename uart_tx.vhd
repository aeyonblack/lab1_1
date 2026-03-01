-- ============================================================
-- uart_tx.vhd
-- UART Transmitter.
-- Serialises an 8-bit byte into an 8N1 UART frame.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

ENTITY uart_tx IS
    PORT (
        clk       : IN  STD_LOGIC;
        rst       : IN  STD_LOGIC;
        tx_data   : IN  STD_LOGIC_VECTOR(7 DOWNTO 0);     -- Byte to send
        tx_start  : IN  STD_LOGIC;                         -- Pulse to begin
        baud_tick : IN  STD_LOGIC;                         -- 1x baud rate tick
        tx        : OUT STD_LOGIC;                         -- Serial output line
        tx_busy   : OUT STD_LOGIC                          -- HIGH while busy
    );
END uart_tx;

ARCHITECTURE rtl OF uart_tx IS

    TYPE state_type IS (IDLE, START, DATA, STOP);
    SIGNAL state : state_type := IDLE;

    -- Local copy of the data to transmit.
    -- We latch it at tx_start so the caller can change tx_data freely
    -- while we're still sending.
    SIGNAL shift_reg : STD_LOGIC_VECTOR(7 DOWNTO 0) := (OTHERS => '0');

    -- Which bit (0..7) we are currently transmitting
    SIGNAL bit_idx : INTEGER RANGE 0 TO 7 := 0;

BEGIN

    tx_proc : PROCESS(clk)
    BEGIN
        IF rising_edge(clk) THEN
            IF rst = '1' THEN
                state     <= IDLE;
                tx        <= '1';      -- Idle line is HIGH
                tx_busy   <= '0';
                bit_idx   <= 0;
                shift_reg <= (OTHERS => '0');

            ELSE
                CASE state IS

                    -- ========================================
                    -- IDLE: Hold TX line HIGH. Wait for the
                    -- user to assert tx_start.
                    -- ========================================
                    WHEN IDLE =>
                        tx      <= '1';    -- Idle = HIGH
                        tx_busy <= '0';
                        bit_idx <= 0;

                        IF tx_start = '1' THEN
                            -- Latch the data and begin
                            shift_reg <= tx_data;
                            tx_busy   <= '1';
                            state     <= START;
                        END IF;

                    -- ========================================
                    -- START: Pull TX LOW for one bit period
                    -- (the start bit).
                    -- ========================================
                    WHEN START =>
                        tx <= '0';    -- Start bit = LOW

                        IF baud_tick = '1' THEN
                            -- One bit period elapsed, move to data
                            state <= DATA;
                        END IF;

                    -- ========================================
                    -- DATA: Output each bit for one bit period.
                    -- LSB first: send shift_reg(0), then shift
                    -- right to prepare the next bit.
                    -- ========================================
                    WHEN DATA =>
                        tx <= shift_reg(0);    -- Drive current LSB onto the line

                        IF baud_tick = '1' THEN
                            -- Shift the register right to bring the
                            -- next bit into position 0
                            shift_reg <= '0' & shift_reg(7 DOWNTO 1);

                            IF bit_idx = 7 THEN
                                bit_idx <= 0;
                                state   <= STOP;
                            ELSE
                                bit_idx <= bit_idx + 1;
                            END IF;
                        END IF;

                    -- ========================================
                    -- STOP: Drive TX HIGH for one bit period
                    -- (the stop bit), then return to IDLE.
                    -- ========================================
                    WHEN STOP =>
                        tx <= '1';    -- Stop bit = HIGH

                        IF baud_tick = '1' THEN
                            state <= IDLE;
                        END IF;

                END CASE;
            END IF;
        END IF;
    END PROCESS;

END rtl;