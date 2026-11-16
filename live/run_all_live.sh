#!/bin/sh
cd /home/claude/work/live
for rep in 0 1 2; do
  for cfg in "FR 0" "DB 0" "DB+B 32" "A 0" "A+B 32" "MP 0"; do
    set -- $cfg
    python3 run_live.py $1 $2 $rep /home/claude/work/live/res 50 3000
  done
done
echo ALLDONE
