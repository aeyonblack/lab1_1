-- ============================================================
-- uart_tb.vhd
-- UART loopback testbench.
-- Transmits a byte and verifies the receiver captures it.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;

ENTITY uart_tb IS
END uart_tb;

ARCHITECTURE sim OF uart_tb IS
    SIGNAL clk       : STD_LOGIC := '0';
    SIGNAL rst       : STD_LOGIC := '0';

    -- Baud ticks
    SIGNAL baud_tick : STD_LOGIC;
    SIGNAL os_tick   : STD_LOGIC;

    -- TX signals
    SIGNAL tx_data   : STD_LOGIC_VECTOR(7 DOWNTO 0) := x"A3";
    SIGNAL tx_start  : STD_LOGIC := '0';
    SIGNAL tx_line   : STD_LOGIC;
    SIGNAL tx_busy   : STD_LOGIC;

    -- RX signals
    SIGNAL rx_data   : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL rx_done   : STD_LOGIC;

    CONSTANT CLK_PERIOD : TIME := 20 ns;
BEGIN

    -- Clock: 50 MHz
    clk <= NOT clk AFTER CLK_PERIOD / 2;

    -- 1x baud generator (for TX)
    baud_1x : ENTITY work.baud_gen
        GENERIC MAP(CLK_FREQ => 50_000_000, BAUD_RATE => 115_200)
        PORT MAP(clk => clk, rst => rst, baud_tick => baud_tick);

    -- 16x oversampling generator (for RX)
    baud_16x : ENTITY work.baud_gen
        GENERIC MAP(CLK_FREQ => 50_000_000, BAUD_RATE => 115_200 * 16)
        PORT MAP(clk => clk, rst => rst, baud_tick => os_tick);

    -- Transmitter
    uut_tx : ENTITY work.uart_tx
        PORT MAP(
            clk => clk, rst => rst,
            tx_data => tx_data, tx_start => tx_start,
            baud_tick => baud_tick, tx => tx_line, tx_busy => tx_busy
        );

    -- Receiver: wire TX output directly to RX input (loopback)
    uut_rx : ENTITY work.uart_rx
        PORT MAP(
            clk => clk, rst => rst,
            rx => tx_line, os_tick => os_tick,
            rx_data => rx_data, rx_done => rx_done
        );

    -- Stimulus
    stim : PROCESS
    BEGIN
        -- Reset
        rst <= '1';
        WAIT FOR CLK_PERIOD * 10;
        rst <= '0';
        WAIT FOR CLK_PERIOD * 5;

        -- Send byte 0xA3
        tx_data  <= x"A3";
        tx_start <= '1';
        WAIT FOR CLK_PERIOD;
        tx_start <= '0';

        -- Wait for RX to complete
        WAIT UNTIL rx_done = '1';
        WAIT FOR CLK_PERIOD;

        -- Verify
        ASSERT rx_data = x"A3"
            REPORT "FAIL: Expected 0xA3, got " & INTEGER'IMAGE(TO_INTEGER(UNSIGNED(rx_data)))
            SEVERITY ERROR;

        ASSERT rx_data = x"A3"
            REPORT "PASS: Received 0xA3 correctly."
            SEVERITY NOTE;

        -- Wait a bit and end
        WAIT FOR 10 us;
        ASSERT FALSE REPORT "Simulation complete." SEVERITY NOTE;
        WAIT;
    END PROCESS;

END sim;