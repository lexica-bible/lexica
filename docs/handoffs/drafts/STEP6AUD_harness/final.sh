# the final test pass with the final block + check program: T1 clean (h4) and T3 plants (h5) in parallel, then the STOP cases
# (h3 re-made), T2 re-paste and T8 hand-edited outputs (on h4)
set -uo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
G=/home/jp/gate6
bash "$S6/mkhome.sh" $G/h4 > $G/mk_h4.out 2>&1
bash "$S6/mkhome.sh" $G/h5 > $G/mk_h5.out 2>&1
( cd $G/h5/bible-db && HOME=$G/h5 python3 "$S6/mkplants.py" $G/h5 ) > $G/plants_h5.out 2>&1
bash "$S6/run.sh" $G/h4 T1 &
bash "$S6/run.sh" $G/h5 T3 XCD=179 XCDOT=156 XCDNT=23 &
wait
bash "$S6/tstops.sh" > $G/TSTOPS.out 2>&1
echo "=============== T2 re-paste (h4) ==============="  > $G/T2.out
( export HOME=$G/h4; cd $G/h4; bash $G/block_T1.sh ) >> $G/T2.out 2>&1; echo "(exit $?)" >> $G/T2.out
bash "$S6/t8.sh" $G/h4 $G/block_T1.sh > $G/T8.out 2>&1
echo FINAL-DONE
