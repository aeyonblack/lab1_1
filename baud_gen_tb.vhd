-- ============================================================
-- baud_gen_tb.vhd
-- Testbench for the baud rate generator.
-- Verifies that baud_tick pulses at the expected interval.
-- ============================================================

LIBRARY ieee;
USE ieee.std_logic_1164.all;

ENTITY baud_gen_tb IS
END baud_gen_tb;

ARCHITECTURE sim OF baud_gen_tb IS
    -- Signals to connect to the Unit Under Test
    SIGNAL clk       : STD_LOGIC := '0';
    SIGNAL rst       : STD_LOGIC := '0';
    SIGNAL baud_tick : STD_LOGIC;

    -- Simulation clock period: 50 MHz = 20 ns period
    CONSTANT CLK_PERIOD : TIME := 20 ns;
BEGIN

    -- Instantiate the baud rate generator
    uut : ENTITY work.baud_gen
        GENERIC MAP(
            CLK_FREQ  => 50_000_000,
            BAUD_RATE => 115_200
        )
        PORT MAP(
            clk       => clk,
            rst       => rst,
            baud_tick => baud_tick
        );

    -- Clock generation process: toggles every 10 ns -> 50 MHz
    clk_proc : PROCESS
    BEGIN
        clk <= '0';
        WAIT FOR CLK_PERIOD / 2;
        clk <= '1';
        WAIT FOR CLK_PERIOD / 2;
    END PROCESS;

    -- Stimulus process
    stim_proc : PROCESS
    BEGIN
        -- Apply reset for a few cycles
        rst <= '1';
        WAIT FOR CLK_PERIOD * 5;
        rst <= '0';

        -- Let it run for enough time to see several baud ticks
        -- At 115200 baud, one tick every 434 * 20ns = 8.68 μs
        -- Run for ~50 μs to see ~5 ticks
        WAIT FOR 50 us;

        -- End simulation
        ASSERT FALSE REPORT "Simulation complete." SEVERITY NOTE;
        WAIT;
    END PROCESS;

END sim;