# An open verification environment for the RISC-V IOMMU

A SystemVerilog testbench, a check suite, and a fault-injection harness for the
[Zero-Day Labs RISC-V IOMMU IP](https://github.com/zero-day-labs/riscv-iommu),
built with open tools only (Verilator). The IP ships no testbench; this is one.

Two write-ups accompany it, in [`docs/`](docs):

| | subject |
|---|---|
| `articleA.pdf` / `paperA.pdf` | the environment, the check suite, and what fault injection says about its adequacy |
| `articleB.pdf` / `paperB.pdf` | device-side invalidation ordering: five properties an IOMMU owes to an OS unmap path, and whether this IP honours them |

## What it does

56 checks covering register access, `ddtp` programming and the Bare/1LVL
directory modes, Sv39 first-stage translation against an independent software
walker, Sv39x4 second-stage translation, IOTLB caching, scoped and global
invalidation, `IOFENCE.C` completion ordering (including with 24 device
transactions in flight), fault-queue records, and PTE permission, reserved-bit
and valid-bit enforcement.

Two further behaviours are reported as **known issues** rather than failures,
because they are observations about the IP rather than checks it fails: with the
fault queue disabled, four of eight faulting transactions go unanswered and a
subsequent valid translation then fails.

Eleven single-line defects are injected into a private copy of the RTL to
measure whether the suite would catch them. The full suite detects all eleven;
the core functional subset detects six, and the five it misses are the
page-table permission, reserved-bit and second-stage faults.

## Running it

Requires Verilator 5.0 or later and Python 3. Results were produced with
Verilator 5.052.

```sh
git clone https://github.com/zero-day-labs/riscv-iommu ext/riscv-iommu
./run.sh              # build + run the suite             (~1 minute)
./run.sh --mutate     # rerun it per injected defect      (~10 minutes)
./run.sh --ablate     # 3 suite levels x 11 faults        (~15 minutes)
```

The suite runs at three nested levels, selected with `+SUITE=<1|2|3>`: core
functional checks (36), plus permission and second-stage tests (46), plus
ordering, scope and concurrency tests (56). The ablation measures all three
against the same fixed set of eleven faults, so the denominator does not move.

Output lands in `results/` as `suite.txt` and `mutation.txt`. To regenerate the
figures and rebuild the documents:

```sh
cd docs && python3 make_figures.py && tectonic -X compile articleA.tex
```

## Layout

```
tb/tb_iommu.sv       the environment: AXI drivers for all four interfaces,
                     the memory image the IOMMU walks, a golden translation
                     model, and the scoreboard
tb/tb_smoke.sv       a minimal elaboration check: can the IP be built at all?
                     This is what established that it cannot be linted as
                     published (see the note below)
tools/mutate.py      fault-injection harness
tools/ablation.py    the same faults against all three suite levels
deps/                a shim supplying the one header the IP includes but
                     does not vendor (see below)
docs/                LaTeX sources, figure generator, built PDFs
results/             suite and fault-injection output
```

## A note on building the IP

As published, the IP cannot be elaborated: its register map includes
`common_cells/assertions.svh`, which the repository does not vendor. The header
in `deps/` forwards to the IP's own assertion macros, which is what makes the
design build. This is described in `docs/articleA.pdf`.

## Licence

The testbench, harness and documents are the author's own work. The IOMMU IP
under `ext/` is not included here and carries its own Apache-2.0 / Solderpad
licences.
