#!/usr/bin/env python3
"""
Fixed-fault-set ablation.

The suite grew in three stages. Reporting detection as the fault set also grew
(4/9, then 8/10, then 11/11) moves the denominator and is not a valid
comparison. This script fixes the fault set at the final eleven mutants and
measures all three suite levels against it, so the denominator is constant.

  level 1  core functional checks            (36 checks)
  level 2  + permission / second stage       (46 checks)
  level 3  + ordering, scope, concurrency    (56 checks)
"""
import os, sys, json, shutil, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("mut", os.path.join(os.path.dirname(os.path.abspath(__file__)),"mutate.py"))

ROOT = os.path.expanduser('~/dev/riscv-iommu-dv')
WORK = os.path.join(ROOT, 'work/abl')
IP   = os.path.join(ROOT, 'ext/riscv-iommu')

# import the definitions without running mutate.py's main body
src = open(os.path.join(ROOT,'tools/mutate.py')).read()
head = src.split("os.makedirs(WORK, exist_ok=True)")[0]
ns = {'__name__':'mutdefs'}
exec(compile(head, 'mutdefs', 'exec'), ns)
MUTANTS, run_suite, failing_checks = ns['MUTANTS'], ns['run_suite'], ns['failing_checks']

os.makedirs(WORK, exist_ok=True)
results = {}
for lvl in (1,2,3):
    base_dir = os.path.join(WORK, f'base{lvl}')
    shutil.rmtree(base_dir, ignore_errors=True); os.makedirs(base_dir)
    base, st, out = run_suite(IP, base_dir, f'base{lvl}', lvl)
    print(f"level {lvl} baseline: {base[0] if base else st} checks, {base[1] if base else '?'} failures", flush=True)
    if not base or base[1] != 0:
        print("baseline must be clean"); sys.exit(1)
    results[lvl] = {'checks': base[0], 'detected': [], 'survived': []}
    for mid, desc, f, line, pat, rep in MUTANTS:
        md = os.path.join(WORK, f'L{lvl}_{mid}')
        shutil.rmtree(md, ignore_errors=True); os.makedirs(md)
        ipc = os.path.join(md, 'riscv-iommu'); shutil.copytree(IP, ipc)
        path = os.path.join(ipc, f)
        lines = open(path).read().split('\n')
        new, n = re.subn(pat, rep, lines[line-1])
        if n == 0:
            print(f"  L{lvl} {mid}: PATCH FAILED"); continue
        lines[line-1] = new; open(path,'w').write('\n'.join(lines))
        t0=time.time(); res, st, out = run_suite(ipc, md, mid, lvl); dt=time.time()-t0
        det = (res is None and st == 'NO_RESULT') or (res is not None and res[1] > 0)
        (results[lvl]['detected'] if det else results[lvl]['survived']).append(mid)
        print(f"  L{lvl} {mid}: {'DETECTED' if det else 'SURVIVED':9s} ({dt:.0f}s) {desc}", flush=True)
        shutil.rmtree(ipc, ignore_errors=True)

N = len(MUTANTS)
with open(os.path.join(ROOT,'results/ablation.txt'),'w') as fh:
    fh.write("FIXED-FAULT-SET ABLATION\n\n")
    fh.write(f"fault set: {N} mutants, identical at every level\n\n")
    fh.write(f"{'suite level':12s} {'checks':7s} {'detected':10s} survived\n")
    for lvl in (1,2,3):
        r=results[lvl]
        fh.write(f"{lvl:<12d} {r['checks']:<7d} {len(r['detected'])}/{N:<8d} "
                 f"{', '.join(r['survived']) if r['survived'] else '-'}\n")
    fh.write("\n")
    for lvl in (1,2,3):
        fh.write(f"level {lvl} survivors: "
                 f"{', '.join(results[lvl]['survived']) if results[lvl]['survived'] else 'none'}\n")
json.dump(results, open(os.path.join(ROOT,'results/ablation.json'),'w'), indent=1)
print("\nwritten: results/ablation.txt")
for lvl in (1,2,3):
    r=results[lvl]
    print(f"  level {lvl}: {r['checks']} checks -> {len(r['detected'])}/{N} detected")
