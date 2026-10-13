#!/usr/bin/env python3
"""
Mutation-based evaluation of the IOMMU verification environment.

Each mutant injects one semantically meaningful IOMMU fault into a private copy
of the RTL, rebuilds, and reruns the whole suite. A mutant is *detected* if any
check fails. Undetected mutants are coverage gaps, and are as informative as the
detected ones.
"""
import os, re, shutil, subprocess, sys, json, time

ROOT = os.path.expanduser('~/dev/riscv-iommu-dv')
IP   = os.path.join(ROOT, 'ext/riscv-iommu')
WORK = os.path.join(ROOT, 'work/mut')
PTW  = 'rtl/translation_logic/ptw/rv_iommu_ptw_sv39x4.sv'
TW   = 'rtl/translation_logic/wrapper/rv_iommu_tw_sv39x4.sv'
IOTLB= 'rtl/translation_logic/rv_iommu_iotlb_sv39x4.sv'
CQ   = 'rtl/software_interface/rv_iommu_cq_handler.sv'

# id, description, file, line, pattern -> replacement
MUTANTS = [
 ("M1","first-stage PTE valid bit ignored",            PTW, 418, r"!pte\.v",            "1'b0"),
 ("M2","PTE accessed bit ignored",                     PTW, 513, r"!pte\.a",            "1'b0"),
 ("M3","PTE dirty bit ignored on stores",              PTW, 513, r"is_store_i && !pte\.d", "1'b0"),
 ("M4","PTE user bit ignored (2nd stage)",             PTW, 514, r"!pte\.u",            "1'b0"),
 ("M5","PTE reserved-bit check removed",               PTW, 636, r"\(\|pte\.reserved\) != 1'b0", "1'b0"),
 ("M6","ddtp=Off no longer blocks transactions",       TW,  739, r"== 4'b0000",         "== 4'b1110"),
 ("M7","ddtp=Bare decoded as a normal mode",           TW,  746, r"== 4'b0001",         "== 4'b1101"),
 ("M8","first-stage enable inverted",                  TW,  193, r"!= 4'b0000",         "== 4'b0000"),
 ("M9","IOTLB invalidation does not clear the entry",  IOTLB,253, r"tags_n\[i\]\.valid = 1'b0;", "tags_n[i].valid = tags_q[i].valid;"),
 ("M10","command queue head never advances",           CQ,  271, r"\(cq_head_i \+ 1\)", "(cq_head_i)"),
 ("M11","invalidate-all clears only the first IOTLB entry", IOTLB,253,
   r"tags_n\[i\]\.valid = 1'b0;", "if (i == 0) tags_n[i].valid = 1'b0;"),
]

def inc_for(ipdir):
    d = [os.path.join(ROOT,'deps'), ipdir]
    for sub in ['include','packages/dependencies','packages/rv_iommu','vendor','rtl',
                'rtl/translation_logic','rtl/translation_logic/cdw','rtl/translation_logic/ptw',
                'rtl/translation_logic/wrapper','rtl/software_interface',
                'rtl/software_interface/regmap','rtl/software_interface/wrapper',
                'rtl/ext_interfaces']:
        d.append(os.path.join(ipdir, sub))
    return ['-I'+x for x in d]

def run_suite(ipdir, mdir, tag, lvl=3):
    obj = os.path.join(mdir, 'obj')
    os.makedirs(obj, exist_ok=True)
    cmd = (['verilator','--binary','--timing','-j','8','--top-module','tb_iommu',
            '--timescale','1ns/1ps', os.path.join(ROOT,'tb/tb_iommu.sv')]
           + inc_for(ipdir) + ['-Wno-fatal','--Mdir',obj,'-o','tb'])
    b = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    exe = os.path.join(obj,'tb')
    if not os.path.exists(exe):
        return None, 'BUILD_FAIL', (b.stderr or '')[-300:]
    r = subprocess.run([exe, f'+SUITE={lvl}'], capture_output=True, text=True,
                       cwd=ROOT, timeout=600)
    m = re.search(r'===\s*(\d+) passed, (\d+) failed', r.stdout)
    if not m:
        return None, 'NO_RESULT', r.stdout[-300:]
    return (int(m.group(1)), int(m.group(2))), 'OK', r.stdout

def failing_checks(out):
    return [l.strip()[6:].split('  ')[0].strip() for l in out.splitlines() if l.strip().startswith('FAIL')]

os.makedirs(WORK, exist_ok=True)
print("baseline:", end=' ', flush=True)
base, st, out = run_suite(IP, os.path.join(WORK,'base'), 'base')
print(f"{base[0]} passed, {base[1]} failed" if base else st)
if not base or base[1] != 0:
    print("baseline must be clean before mutating"); sys.exit(1)

rows = []
for mid, desc, f, line, pat, rep in MUTANTS:
    md = os.path.join(WORK, mid)
    shutil.rmtree(md, ignore_errors=True); os.makedirs(md)
    ipc = os.path.join(md, 'riscv-iommu')
    shutil.copytree(IP, ipc)
    path = os.path.join(ipc, f)
    lines = open(path).read().split('\n')
    orig = lines[line-1]
    new, n = re.subn(pat, rep, orig)
    if n == 0:
        rows.append((mid, desc, 'PATCH_FAIL', 0, [])); print(f"{mid}: PATCH FAILED"); continue
    lines[line-1] = new
    open(path,'w').write('\n'.join(lines))
    t0 = time.time()
    res, st, out = run_suite(ipc, md, mid)
    dt = time.time() - t0
    if res is None:
        # a hang or a build/run that never reports is itself an observable failure
        status = 'DETECTED' if st in ('NO_RESULT',) else st
        rows.append((mid, desc, status, -1, [st]))
        print(f"{mid}: {status:9s} ({st}) ({dt:.0f}s)  {desc}")
    else:
        det = res[1] > 0
        fails = failing_checks(out)
        rows.append((mid, desc, 'DETECTED' if det else 'SURVIVED', res[1], fails))
        print(f"{mid}: {'DETECTED' if det else 'SURVIVED':9s} {res[1]:2d} failing check(s)  ({dt:.0f}s)  {desc}")
    shutil.rmtree(ipc, ignore_errors=True)

det = sum(1 for r in rows if r[2]=='DETECTED')
usable = sum(1 for r in rows if r[2] in ('DETECTED','SURVIVED'))
print()
print(f"mutation score: {det}/{usable} detected")
json.dump([{'id':r[0],'desc':r[1],'status':r[2],'n_fail':r[3],'checks':r[4]} for r in rows],
          open(os.path.join(ROOT,'results/mutation.json'),'w'), indent=1)
with open(os.path.join(ROOT,'results/mutation.txt'),'w') as fh:
    fh.write("MUTATION-BASED EVALUATION\n\n")
    fh.write(f"baseline: {base[0]} checks, 0 failures\n\n")
    fh.write(f"{'id':5s} {'status':10s} {'fails':6s} description\n")
    for r in rows:
        fh.write(f"{r[0]:5s} {r[2]:10s} {r[3]:<6d} {r[1]}\n")
    fh.write(f"\nmutation score: {det}/{usable} detected\n\n")
    for r in rows:
        if r[2]=='DETECTED':
            fh.write(f"{r[0]} caught by: {', '.join(r[4][:4])}\n")
    for r in rows:
        if r[2]=='SURVIVED':
            fh.write(f"{r[0]} SURVIVED (coverage gap): {r[1]}\n")
print("written: results/mutation.txt")
