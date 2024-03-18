param (
    [Parameter(Mandatory=$false)]
    [string]$results_dir = ".\results",

    [Parameter(Mandatory=$false)]
    [ValidateSet('thinkaloud', 'tracking', 'all')]
    [string]$study = "all",

    [Parameter(Mandatory=$false)]
    [string]$image,

    [Parameter(Mandatory=$false)]
    [bool]$overwrite_csv = $true,

    [Parameter(Mandatory=$false)]
    [string]$grades_csv = "../processed_data/all_grades.csv"
)

$studies = @()
if ($study -ne "all")
{
    $studies = @($study)
}
else
{
    $studies = @('thinkaloud', 'tracking') # FIXME code duplication
}

foreach ($s in $studies)
{
    echo " *** $s ***"

    $images = @()
    if ($image)
    {
        $images = @($image)
    }
    else
    {
        [string[]]$images = (gci -Path "${results_dir}\${s}" -Directory).Name
    }

    foreach ($i in $images)
    {
        echo " ### $i ###"

        $image_dir = "${results_dir}\${s}\${i}\"
        $output_csv = "${image_dir}\strings.csv"

        if ($overwrite_csv -and (Test-Path "${output_csv}" -ErrorAction SilentlyContinue))
        {
            Remove-Item -Path "${output_csv}"
        }

        foreach ($p in (gci -Path "$image_dir" -Directory))
        {
            echo " === $($p.name) ===";

            $string_csv = $p.FullName + "\" + $p.name + "_fixation_string.csv";
            $output_plot_png = $p.FullName + "\" + $p.name + "_fixation_string_plot.png"
            python create_fixation_string.py "${string_csv}" "${grades_csv}" "${output_csv}" "${output_plot_png}";
        }

        echo "" 
    }
}

echo "All done. Have a nice day :)"
