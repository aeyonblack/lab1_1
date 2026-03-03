-- ============================================================
-- uart_tx.vhd
-- UART Transmitter.
-- Serialises an 8-bit byte into an 8N1 UART frame.
-- Uses an internal counter (not the free-running baud_tick)
-- to guarantee every bit is held for exactly one full period.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

ENTITY uart_tx IS
    GENERIC (
        CLK_FREQ  : INTEGER := 50_000_000;
        BAUD_RATE : INTEGER := 115_200
    );
    PORT (
        clk       : IN  STD_LOGIC;
        rst       : IN  STD_LOGIC;
        tx_data   : IN  STD_LOGIC_VECTOR(7 DOWNTO 0);
        tx_start  : IN  STD_LOGIC;
        tx        : OUT STD_LOGIC;
        tx_busy   : OUT STD_LOGIC
    );
END uart_tx;

ARCHITECTURE rtl OF uart_tx IS

    CONSTANT CLKS_PER_BIT : INTEGER := CLK_FREQ / BAUD_RATE - 1;

    TYPE state_type IS (IDLE, START, DATA, STOP);
    SIGNAL state : state_type := IDLE;

    SIGNAL shift_reg : STD_LOGIC_VECTOR(7 DOWNTO 0) := (OTHERS => '0');
    SIGNAL bit_idx   : INTEGER RANGE 0 TO 7 := 0;
    SIGNAL clk_count : INTEGER RANGE 0 TO CLKS_PER_BIT := 0;

BEGIN

    tx_proc : PROCESS(clk)
    BEGIN
        IF rising_edge(clk) THEN
            IF rst = '1' THEN
                state     <= IDLE;
                tx        <= '1';
                tx_busy   <= '0';
                bit_idx   <= 0;
                clk_count <= 0;
                shift_reg <= (OTHERS => '0');

            ELSE
                CASE state IS

                    WHEN IDLE =>
                        tx        <= '1';
                        tx_busy   <= '0';
                        bit_idx   <= 0;
                        clk_count <= 0;

                        IF tx_start = '1' THEN
                            shift_reg <= tx_data;
                            tx_busy   <= '1';
                            state     <= START;
                        END IF;

                    WHEN START =>
                        tx <= '0';   -- Start bit = LOW

                        IF clk_count = CLKS_PER_BIT THEN
                            clk_count <= 0;
                            state     <= DATA;
                        ELSE
                            clk_count <= clk_count + 1;
                        END IF;

                    WHEN DATA =>
                        tx <= shift_reg(0);

                        IF clk_count = CLKS_PER_BIT THEN
                            clk_count <= 0;
                            shift_reg <= '0' & shift_reg(7 DOWNTO 1);

                            IF bit_idx = 7 THEN
                                bit_idx <= 0;
                                state   <= STOP;
                            ELSE
                                bit_idx <= bit_idx + 1;
                            END IF;
                        ELSE
                            clk_count <= clk_count + 1;
                        END IF;

                    WHEN STOP =>
                        tx <= '1';   -- Stop bit = HIGH

                        IF clk_count = CLKS_PER_BIT THEN
                            clk_count <= 0;
                            state     <= IDLE;
                        ELSE
                            clk_count <= clk_count + 1;
                        END IF;

                END CASE;
            END IF;
        END IF;
    END PROCESS;

END rtl;