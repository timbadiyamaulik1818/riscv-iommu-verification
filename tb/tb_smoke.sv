// Smoke testbench: can Verilator elaborate and run the RISC-V IOMMU IP?
`include "assertions.svh"
`include "register_interface/typedef.svh"
`include "riscv_pkg.sv"
`include "lint_wrapper_pkg.sv"
`include "rv_iommu_pkg.sv"
`include "rv_iommu_reg_pkg.sv"
`include "rv_iommu_field_pkg.sv"

module tb_smoke
  import lint_wrapper::*;
  import rv_iommu::*;
();
  logic clk = 1'b0, rst_n = 1'b0;
  always #5 clk = ~clk;

  typedef logic [64-1:0] reg_addr_t;
  typedef logic [32-1:0] reg_data_t;
  typedef logic [4-1:0]  reg_strb_t;
  `REG_BUS_TYPEDEF_ALL(iommu_reg, reg_addr_t, reg_data_t, reg_strb_t)

  req_iommu_t dev_tr_req;  resp_t     dev_tr_resp;
  resp_t      dev_comp_resp; req_t    dev_comp_req;
  resp_t      ds_resp;       req_t    ds_req;
  req_slv_t   prog_req;      resp_slv_t prog_resp;
  logic [NumIRQWires-1:0] wsi_wires;

  riscv_iommu #(
    .IOTLB_ENTRIES(16), .DDTC_ENTRIES(8), .PDTC_ENTRIES(8), .MRIFC_ENTRIES(4),
    .InclPC(1'b1), .InclBC(1'b1), .InclDBG(1'b1),
    .MSITrans(MSI_FLAT_MRIF), .IGS(BOTH), .N_INT_VEC(NumIRQWires), .N_IOHPMCTR(16),
    .ADDR_WIDTH(AddrWidth), .DATA_WIDTH(DataWidth), .ID_WIDTH(IdWidth),
    .ID_SLV_WIDTH(IdWidthSlv), .USER_WIDTH(UserWidth),
    .aw_chan_t(aw_chan_t), .w_chan_t(w_chan_t), .b_chan_t(b_chan_t),
    .ar_chan_t(ar_chan_t), .r_chan_t(r_chan_t),
    .axi_req_t(req_t), .axi_rsp_t(resp_t),
    .axi_req_slv_t(req_slv_t), .axi_rsp_slv_t(resp_slv_t),
    .axi_req_iommu_t(req_iommu_t),
    .reg_req_t(iommu_reg_req_t), .reg_rsp_t(iommu_reg_rsp_t)
  ) i_dut (
    .clk_i(clk), .rst_ni(rst_n),
    .dev_tr_req_i(dev_tr_req),     .dev_tr_resp_o(dev_tr_resp),
    .dev_comp_resp_i(dev_comp_resp), .dev_comp_req_o(dev_comp_req),
    .ds_resp_i(ds_resp),           .ds_req_o(ds_req),
    .prog_req_i(prog_req),         .prog_resp_o(prog_resp),
    .wsi_wires_o(wsi_wires)
  );

  int unsigned cyc = 0;
  always @(posedge clk) if (rst_n) cyc++;

  initial begin
    dev_tr_req = '0; dev_comp_resp = '0; ds_resp = '0; prog_req = '0;
    repeat (4) @(posedge clk);
    rst_n = 1'b1;
    repeat (200) @(posedge clk);
    $display("SMOKE OK: ran %0d cycles past reset", cyc);
    $display("  prog_resp.ar_ready=%0b  ds_req.ar_valid=%0b  dev_tr_resp.aw_ready=%0b",
             prog_resp.ar_ready, ds_req.ar_valid, dev_tr_resp.aw_ready);
    $finish;
  end
endmodule
