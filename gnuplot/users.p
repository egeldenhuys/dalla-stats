dir = '../logs/2016-10/users/'

files = system('ls '.dir)

set datafile separator ","

set key autotitle columnheader

set ylabel 'GiB'
scale = 0.000000001

#set ylabel 'KiB'
#scale = 0.000976562

#set ylabel 'MiB'
#scale = 0.000000954

set xlabel 'Time'
set xdata time
set timefmt "%s"
set format x "%d - %H:%M"

set title "Total usage"
# Prev total
plot for [file in files] (dir.file) using ($1 + 2*60*60):(($4 + $5) * scale) with lines title file
#plot for [file in files] (dir.file) using ($1 + 2*60*60):(($3) * scale) with lines title file
