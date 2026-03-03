# -----------------------------------------------------------------------------
# lab1_1.sdc
# User timing constraints for lab1_1.
# -----------------------------------------------------------------------------

# 50 MHz board clock on FPGA_CLK1_50 -> period = 20 ns
create_clock -name FPGA_CLK1_50 -period 20.000 [get_ports {FPGA_CLK1_50}]

# Ask TimeQuest to derive reasonable uncertainties from the clock definition.
derive_clock_uncertainty
