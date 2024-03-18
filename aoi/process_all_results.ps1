# analyse the data from all participants

# command line arguments
param (
    [Parameter(Position=0, HelpMessage="Path to the processed results directory")]
    [string]$results_dir = "../processed_data",

    [Parameter(Position=1, HelpMessage="Path to the directory to write outputs")]
    [string]$output_dir = "./results",

    [Parameter(HelpMessage="CSV file containing grading results")]
    [string]$grades_csv = "../processed_data/all_grades.csv",

    [Parameter(HelpMessage="Only process data for these participants (comma separated)")]
    [string[]]$participants = @(),

    [Parameter(HelpMessage="Only process these images (without path or extension, comma separated)")]
    [string[]]$img_root = @(),

    [Parameter(HelpMessage="Studies to process")]
    [ValidateSet('thinkaloud', 'tracking')]
    [String[]]$studies = @('thinkaloud', 'tracking'),

    [Parameter(HelpMessage="Directory containing mask image files (bmp)")]
    [string]$mask_dir = ".\masks"
)

### parse command line arguments ###

if (-not (Test-Path -Path "${results_dir}"))
{
    Write-Host "ERROR: Results directory does not exist: ${results_dir}"
    exit 1
}

if (-not (Test-Path -Path "${output_dir}"))
{
    Write-Host "Output directory does not exist. Creating it now."
    New-Item -ItemType Directory "${output_dir}" | Out-Null
}

if ($participants.count -eq 0)
{
    [string[]]$participants = (Get-ChildItem "${results_dir}" -Directory).Name
}

### iterate through results ###

# the results directory is in this structure:
# <results_dir>/<participant_id>/(thinkaloud|tracking)/<img>.bmp.processed.txt

# output directory will have this structure:
#   <results_dir>/(thinkaloud|tracking)/<img>/<participant_id>
# and create these files:
#   <participant_id>_raw_coords.csv
#   <participant_id>_raw_fixations.csv
#   <participant_id>_fixation_string.csv
#   <participant_id>_fixation_string.stats.csv
#   <participant_id>_fixations_plot.png
#   <participant_id>_fixations_overlay.png
#   <participant_id>_hmm_plot.<k_max>.png
#   <participant_id>_hmm_plot.<k_max>.matrix.png
#   <participant_id>_hmm_plot_overlay.<k_max>.png
#
# copies of the "best" hmm k_max results will be written to:
#   <results_dir>/(thinkaloud|tracking)/<img>/
#     <participant_id>_hmm_plot.best.png
#     <participant_id>_hmm_plot_overlay.best.png

foreach ($participant in $participants)
{
    Write-Host "=== ${participant} ==="
    foreach ($study in $studies)
    {
        Write-Host "== ${study} =="
        $raw_files = Get-ChildItem "${results_dir}\${participant}\${study}\*.bmp.processed.txt" -File
        foreach ($raw_file in $raw_files)
        {
            [string]$raw_file_name = $raw_file.Name
            [string]$raw_file_fullname = $raw_file.FullName

            # extract the image name from the filename
            $image = $raw_file_name.substring(0, $raw_file_name.length - ".bmp.processed.txt".length)

            # ignore if we defined a set of images
            if (($img_root.count -gt 0) -and -not ($img_root.contains($image)))
            {
                Write-Host "= Ignoring image ${image} ="
                continue
            }

            Write-Host "= ${image} ="

            # path to the original image
            $img_path_bmp = "..\images\${image}.bmp"

            # ensure the nested output directory exists
            $outdir = "${output_dir}\${study}\${image}\${participant}"
            if (-not (Test-Path -Path "${outdir}"))
            {
                New-Item -ItemType Directory "${outdir}" | Out-Null
            }

            ### extract data from the raw files ###
            Write-Host "Extracting fixation data"
            $raw_fixations_csv = "${outdir}\${participant}_raw_fixations.csv"
            python extract_fixations.py "${raw_file_fullname}" "${raw_fixations_csv}"

            Write-Host "Generating fixation plot"
            $fixation_plot_png = "${outdir}\${participant}_fixations_plot.png"
            python create_fixation_overlay.py "${raw_fixations_csv}" "${fixation_plot_png}"

            Write-Host "Extracting raw coordinate data"
            $raw_coords_csv = "${outdir}\${participant}_raw_coords.csv"
            python extract_coords.py "${raw_file_fullname}" "${raw_coords_csv}"

            ### generate a fixation overlay image ###
            $fixation_overlay_png = "${outdir}\${participant}_fixations_overlay.png"
            python image_overlay.py "${img_path_bmp}" "${fixation_plot_png}" "${fixation_overlay_png}"

            ### calculate scanpath strings ###
            Write-Host "Calculating scanpath strings"
            $aoi_dir = "${mask_dir}\${image}"
            $fixation_string_csv = "${outdir}\${participant}_fixation_string.csv"
            $fixation_string_plot_png = "${outdir}\${participant}_fixation_string_plot.png"
            $all_strings_csv = "${output_dir}\${study}\${image}\strings.csv"
            if (-not (Test-Path -Path "${aoi_dir}"))
            {
                Write-Host "WARN: AOI directory does not exist (skipping): ${aoi_dir}"
            }
            else
            {
                python match_fixations.py "${raw_fixations_csv}" "${aoi_dir}" "${fixation_string_csv}"
                python create_fixation_string.py "${fixation_string_csv}" "${grades_csv}" "${all_strings_csv}" "${fixation_string_plot_png}"
            }

            ### Hidden Markov model analysis ###
            Write-Host "Performing hidden Markov model analysis"
            $hmm_plot_png = "${outdir}\${participant}_hmm_plot.png"
            python create_hmm_overlay.py "${participant}" "${image}.bmp" "${study}" "${hmm_plot_png}"
        }
    }
}

Write-Host ""
Write-Host "Processing finished! Have a nice day :)"
