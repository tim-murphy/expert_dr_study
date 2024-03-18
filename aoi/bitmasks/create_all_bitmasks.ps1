# create all bitmasks for a given image

param (
    [Parameter(HelpMessage="Path to the mask image directory")]
    [string]$mask_image_dir = "../images",

    [Parameter(HelpMessage="Path to output directory")]
    [string]$outdir = "../masks",

    [Parameter(HelpMessage="AOIs to join all masks with the same prefix together (comma separated)")]
    [string[]]$aoi_join = @("arcade_inferior", "arcade_superior"),

    [Parameter(HelpMessage="Data accuracy, in pixels")]
    [int]$accuracy_px = 70
)

# create the output directory
New-Item -ItemType Directory -Path $outdir -Force

$images = (gci -Path "$mask_image_dir" -Directory | Select-Object Name)
foreach ($i in $images)
{
    $filename = $i.name
    Write-Host "==" $i.Name "=="

    $image_maskdir = "${mask_image_dir}\" + $i.Name
    $image_outdir = "${outdir}\" + $i.Name
    New-Item -ItemType Directory -Path $image_outdir -Force

    # generate each of the masks in turn
    Get-ChildItem -Path "${image_maskdir}" -Filter *.bmp | Foreach-Object {
        Write-Host "=== $($_.Name) ==="

        $infile = $_.FullName
        $outfile = $image_outdir + "\" + $_.Name

        # does this AOI need to be joined?
        $join = $false
        foreach ($aoi in $aoi_join)
        {
            if ($_.Name.startswith($aoi))
            {
                $join = $true
            }
        }

        # we'll do the joined AOI masks later
        if (!$join)
        {
            python create_bitmask.py "${outfile}" "${accuracy_px}" "${infile}"
        }
    }

    echo $aoi_join

    # now do all of the joined AOIs
    foreach ($aoi in $aoi_join)
    {
        Write-Host "### joining AOIs: ${aoi} ###"

        $outfile = $image_outdir + "\${aoi}.bmp"
        $infiles = @()
        Get-ChildItem -Path "${image_maskdir}" -Filter "${aoi}*.bmp" | Foreach-Object {
            Write-Host "=== $($_.Name) ==="

            $infiles += $_.FullName
        }

        if ($infiles.count -gt 0)
        {
            python create_bitmask.py "${outfile}" "${accuracy_px}" @infiles
        }
        else
        {
            Write-Host "No AOIs found"
        }
    }
}
