## Initial processing
1. powershell process_all_results.ps1

## Stats
1. `python combine_all_stats.py results/tracking ../processed_data/tracking_grades.csv all_stats.csv` to create `all_stats.csv`
2. python combine_all_strings.py results all_strings.csv
3. `python stats.py all_stats.csv all_strings.csv`

## Clustering
1. cd bitmasks; powershell .\create_all_bitmasks.ps1 -mask_image_dir ../images -outdir ../masks; cd ..
2. python cluster_strings.py all_strings.csv
