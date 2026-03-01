-- ============================================================
-- lab1_1.vhd
-- Top-level entity for EAS 410 Practical 1.
-- Integrates: baud_gen (×2), uart_rx, uart_tx, and
-- circular bit shifter.
--
-- Board: DE0-Nano-SoC (Cyclone V - 5CSEMA4U23C6)
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

ENTITY lab1_1 IS
    PORT (
        FPGA_CLK1_50 : IN  STD_LOGIC;
        KEY          : IN  STD_LOGIC_VECTOR(1 DOWNTO 0);
        SW           : IN  STD_LOGIC_VECTOR(3 DOWNTO 0);
        LED          : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        ARDUINO_IO   : INOUT STD_LOGIC_VECTOR(15 DOWNTO 0)
    );
END lab1_1;

ARCHITECTURE structural OF lab1_1 IS

    -- ========================================================
    -- Internal signals
    -- ========================================================

    -- Clock and reset
    SIGNAL clk : STD_LOGIC;
    SIGNAL rst : STD_LOGIC;

    -- Baud rate ticks
    SIGNAL baud_tick : STD_LOGIC;   -- 1x baud rate (for TX)
    SIGNAL os_tick   : STD_LOGIC;   -- 16x baud rate (for RX oversampling)

    -- UART RX outputs
    SIGNAL rx_data : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL rx_done : STD_LOGIC;

    -- Shifted data
    SIGNAL shifted_byte : STD_LOGIC_VECTOR(7 DOWNTO 0);

    -- UART TX control
    SIGNAL tx_busy : STD_LOGIC;

    -- Serial lines
    SIGNAL uart_rx_pin : STD_LOGIC;
    SIGNAL uart_tx_pin : STD_LOGIC;

BEGIN

    -- ========================================================
    -- Pin Mapping
    -- ========================================================

    -- Map the 50 MHz clock input to our internal clock signal
    clk <= FPGA_CLK1_50;

    -- KEY[0] is active-LOW on the DE0-Nano-SoC.
    -- We invert it so rst = '1' means "reset active" in our logic.
    rst <= NOT KEY(0);

    -- ARDUINO_IO[0] is our UART RX (data FROM the PC)
    uart_rx_pin <= ARDUINO_IO(0);

    -- ARDUINO_IO[1] is our UART TX (data TO the PC)
    ARDUINO_IO(1) <= uart_tx_pin;

    -- Debug: show the last received byte on LEDs
    LED <= rx_data;

    -- ========================================================
    -- Module Instantiations
    -- ========================================================

    -- 1x Baud Rate Generator (for transmitter)
    baud_1x : ENTITY work.baud_gen
        GENERIC MAP(
            CLK_FREQ  => 50_000_000,
            BAUD_RATE => 115_200
        )
        PORT MAP(
            clk       => clk,
            rst       => rst,
            baud_tick => baud_tick
        );

    -- 16x Oversampling Generator (for receiver)
    baud_16x : ENTITY work.baud_gen
        GENERIC MAP(
            CLK_FREQ  => 50_000_000,
            BAUD_RATE => 115_200 * 16
        )
        PORT MAP(
            clk       => clk,
            rst       => rst,
            baud_tick => os_tick
        );

    -- UART Receiver
    rx_inst : ENTITY work.uart_rx
        PORT MAP(
            clk     => clk,
            rst     => rst,
            rx      => uart_rx_pin,
            os_tick => os_tick,
            rx_data => rx_data,
            rx_done => rx_done
        );

    -- UART Transmitter
    tx_inst : ENTITY work.uart_tx
        PORT MAP(
            clk       => clk,
            rst       => rst,
            tx_data   => shifted_byte,  -- Send the SHIFTED byte back
            tx_start  => rx_done,       -- Transmit as soon as a byte is received
            baud_tick => baud_tick,
            tx        => uart_tx_pin,
            tx_busy   => tx_busy
        );

    -- ========================================================
    -- Circular Bit Shifter
    -- ========================================================

    shift_proc : PROCESS(rx_data, SW)
    BEGIN
        CASE SW(1 DOWNTO 0) IS
            WHEN "00" =>
                -- Rotate left by 1
                shifted_byte <= rx_data(6 DOWNTO 0) & rx_data(7);
            WHEN "01" =>
                -- Rotate right by 1
                shifted_byte <= rx_data(0) & rx_data(7 DOWNTO 1);
            WHEN "10" =>
                -- Rotate left by 2
                shifted_byte <= rx_data(5 DOWNTO 0) & rx_data(7 DOWNTO 6);
            WHEN "11" =>
                -- Rotate right by 2
                shifted_byte <= rx_data(1 DOWNTO 0) & rx_data(7 DOWNTO 2);
            WHEN OTHERS =>
                -- Safety catch for simulation (handles 'X', 'U' etc.)
                shifted_byte <= rx_data;
        END CASE;
    END PROCESS;

END structural;