-- ============================================================
-- lab1_1.vhd
-- Top-level entity for EAS 410 Practical 1.
-- Simple datapath:
--   RX byte -> circular shift by SW[1:0] -> TX byte
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

        -- Dedicated UART pins (Arduino header pins 0 and 1)
        UART_RXD     : IN  STD_LOGIC;     -- PIN_AG13: data FROM PC
        UART_TXD     : OUT STD_LOGIC      -- PIN_AF13: data TO PC
    );
END lab1_1;

ARCHITECTURE structural OF lab1_1 IS

    -- Clock and reset
    SIGNAL clk : STD_LOGIC;
    SIGNAL rst : STD_LOGIC;

    -- Baud rate ticks
    SIGNAL os_tick   : STD_LOGIC;   -- 16x baud rate (for RX oversampling)

    -- UART RX outputs
    SIGNAL rx_data : STD_LOGIC_VECTOR(7 DOWNTO 0);
    SIGNAL rx_done : STD_LOGIC;

    -- Shifted data
    SIGNAL shifted_byte : STD_LOGIC_VECTOR(7 DOWNTO 0);

    -- UART TX control
    SIGNAL tx_busy     : STD_LOGIC;
    SIGNAL tx_start    : STD_LOGIC;
    SIGNAL tx_data_reg : STD_LOGIC_VECTOR(7 DOWNTO 0);

    -- One-byte pending buffer so RX results are not lost while TX is busy
    SIGNAL pending_valid : STD_LOGIC;
    SIGNAL pending_byte  : STD_LOGIC_VECTOR(7 DOWNTO 0);

    -- Internal serial lines
    SIGNAL uart_rx_pin : STD_LOGIC;
    SIGNAL uart_tx_pin : STD_LOGIC;

BEGIN

    -- ========================================================
    -- Pin Mapping
    -- ========================================================
    clk <= FPGA_CLK1_50;
    rst <= NOT KEY(0);  -- KEY[0] is active-low

    uart_rx_pin <= UART_RXD;       -- Direct input — no tristate
    UART_TXD    <= uart_tx_pin;    -- Direct output — no tristate

    -- Debug: show last received byte
    LED <= rx_data;

    -- ========================================================
    -- Module Instantiations
    -- ========================================================

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

    -- UART Transmitter (self-timed — has its own internal baud counter)
    tx_inst : ENTITY work.uart_tx
        GENERIC MAP(
            CLK_FREQ  => 50_000_000,
            BAUD_RATE => 115_200
        )
        PORT MAP(
            clk       => clk,
            rst       => rst,
            tx_data   => tx_data_reg,
            tx_start  => tx_start,
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
                shifted_byte <= rx_data(6 DOWNTO 0) & rx_data(7);             -- L1
            WHEN "01" =>
                shifted_byte <= rx_data(0) & rx_data(7 DOWNTO 1);             -- R1
            WHEN "10" =>
                shifted_byte <= rx_data(5 DOWNTO 0) & rx_data(7 DOWNTO 6);    -- L2
            WHEN OTHERS =>
                shifted_byte <= rx_data(1 DOWNTO 0) & rx_data(7 DOWNTO 2);    -- R2
        END CASE;
    END PROCESS;

    -- ========================================================
    -- TX Scheduler
    -- ========================================================
    tx_sched_proc : PROCESS(clk)
    BEGIN
        IF rising_edge(clk) THEN
            IF rst = '1' THEN
                tx_start      <= '0';
                tx_data_reg   <= (OTHERS => '0');
                pending_valid <= '0';
                pending_byte  <= (OTHERS => '0');
            ELSE
                tx_start <= '0';

                -- Send pending byte when TX is idle
                IF pending_valid = '1' AND tx_busy = '0' THEN
                    tx_data_reg   <= pending_byte;
                    tx_start      <= '1';
                    pending_valid <= '0';
                END IF;

                -- Capture latest shifted byte from RX
                IF rx_done = '1' THEN
                    pending_byte  <= shifted_byte;
                    pending_valid <= '1';
                END IF;
            END IF;
        END IF;
    END PROCESS;

END structural;
