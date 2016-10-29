datafile = '../logs/2016-10/total.csv'

set datafile separator ","

set key autotitle columnheader

#set ylabel 'GiB'
#scale = 0.000000001

#set ylabel 'MiB'
#scale = 0.000000954

set ylabel 'KiB'
scale = 0.000976562

set xlabel 'Time'
set xdata time
set timefmt "%s"
set format x "%d - %H:%M"

set title "Totals"

plot datafile using ($1 + 2*60*60):($2 * scale) with lines, \
datafile using ($1 + 2*60*60):($4 * scale) with lines, \
datafile using ($1 + 2*60*60):($5 * scale) with lines, \
datafile using ($1 + 2*60*60):(($4 + $5) * scale) with lines title "Total", \
datafile using ($1 + 2*60*60):($3 * scale) with lines
