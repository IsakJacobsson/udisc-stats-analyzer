#/bin/bash

commands="hole-distribution performance-curve score-distribution"

image_dir="docs"
file_ending="-demo.png"

for cmd in $commands; do
    output_file="$image_dir/$cmd$file_ending"
    python udisc_analysis.py $cmd --csv-dir score_cards --course Vipan --layout Main -o $output_file
done

