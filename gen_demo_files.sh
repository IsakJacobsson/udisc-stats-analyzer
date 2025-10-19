#/bin/bash

image_commands="hole-distribution performance-curve score-distribution"
text_commands="basic-stats"

demo_dir="docs"
image_file_ending="-demo.png"
text_file_ending="-demo.txt"

for cmd in $image_commands; do
    output_file="$demo_dir/$cmd$image_file_ending"
    python udisc_analysis.py $cmd --csv-dir score_cards --course Vipan --layout Main -o $output_file
done

for cmd in $text_commands; do
    output_file="$demo_dir/$cmd$text_file_ending"
    python udisc_analysis.py $cmd --csv-dir score_cards --course Vipan --layout Main -o $output_file
done
