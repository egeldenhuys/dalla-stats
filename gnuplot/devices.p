dir = '../logs/2016-10/devices/'

files = system('ls '.dir)

set datafile separator ","

set key autotitle columnheader

# set ylabel 'GiB'
# scale = 0.000000001

#set ylabel 'MiB'
#scale = 0.000000954

set ylabel 'KiB'
scale = 0.000976562

set xlabel 'Time'
set xdata time
set timefmt "%s"
set format x "%d - %H:%M"

set title "Usage per device"

#plot for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($4 + $5) * scale) with lines title file

# for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($2) * scale) with lp title file.' Total Bytes', \
#  for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($3) * scale) with lp title file.' Delta', \

plot for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($4) * scale) with lp title file.' On-Peak', \
  for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($5) * scale) with lp title file.' Off-Peak', \
  for [file in files] (dir.file) every 1 using ($1 + 2*60*60):(($4 + $5) * scale) with lp title file.' Total'
