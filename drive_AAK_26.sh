#!/bin/sh
f1=1.2
f2=2.5
ev1=DPRK2
ev2=DPRK6
station=AAK
phase=P
outfile=${station}_${phase}_dt.txt
topdir=../SACwf
python wa_slider.py --f1 ${f1} --f2 ${f2} \
                    --ev1 ${ev1} --ev2 ${ev2} \
                    --station ${station} \
                    --topdir ${topdir} \
                    --phase ${phase} \
                    --outfile ${outfile} \
                    --chan1 AAK.BHZ --chan2 AAK.BHN --chan3 AAK.BHE
