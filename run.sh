#!/usr/bin/env bash
# Build the IOMMU with the testbench, run the check suite, and (with --mutate)
# rerun it against each injected defect. Requires verilator >= 5.0 and python3.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IP="$ROOT/ext/riscv-iommu"
OBJ="$ROOT/work/obj_tb"

if [ ! -d "$IP/rtl" ]; then
  echo "error: the IOMMU IP is not present at $IP" >&2
  echo "       git clone https://github.com/zero-day-labs/riscv-iommu \"$IP\"" >&2
  exit 1
fi

INC="-I$ROOT/deps -I$IP"
for sub in include packages/dependencies packages/rv_iommu vendor rtl \
           rtl/translation_logic rtl/translation_logic/cdw \
           rtl/translation_logic/ptw rtl/translation_logic/wrapper \
           rtl/software_interface rtl/software_interface/regmap \
           rtl/software_interface/wrapper rtl/ext_interfaces; do
  INC="$INC -I$IP/$sub"
done

mkdir -p "$OBJ" "$ROOT/results"
echo "==> building"
verilator --binary --timing -j 8 --top-module tb_iommu --timescale 1ns/1ps \
  "$ROOT/tb/tb_iommu.sv" ${INC} -Wno-fatal --Mdir "$OBJ" -o tb

echo "==> running the suite"
"$OBJ/tb" | tee "$ROOT/results/suite.txt"

if [ "${1:-}" = "--ablate" ]; then
  echo "==> fixed-fault-set ablation (3 suite levels x 11 faults; ~15 minutes)"
  python3 "$ROOT/tools/ablation.py"
  cat "$ROOT/results/ablation.txt"
fi

if [ "${1:-}" = "--mutate" ]; then
  echo "==> fault injection (rebuilds the design once per defect; several minutes)"
  python3 "$ROOT/tools/mutate.py"
  cat "$ROOT/results/mutation.txt"
fi

echo
echo "suite  -> results/suite.txt"
[ "${1:-}" = "--mutate" ] && echo "defects-> results/mutation.txt"
[ "${1:-}" = "--ablate" ] && echo "ablation-> results/ablation.txt"
exit 0
