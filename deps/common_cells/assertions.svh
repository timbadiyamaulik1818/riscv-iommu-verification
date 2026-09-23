// The RISC-V IOMMU IP ships include/assertions.svh but its register map includes
// "common_cells/assertions.svh", which the IP does not vendor. Importing the
// upstream lowRISC header instead breaks the build: it defines ASSERT_RPT with
// two arguments where the IP's RTL uses one. Forward to the IP's own header so a
// single, self-consistent set of assertion macros is used.
`include "assertions.svh"
