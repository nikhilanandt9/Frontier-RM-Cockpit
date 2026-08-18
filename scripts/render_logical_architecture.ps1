param(
    [string]$Source = (Join-Path $PSScriptRoot '..\docs\architecture\frontier-rm-logical-architecture.svg'),
    [string]$Output = (Join-Path $PSScriptRoot '..\docs\architecture\frontier-rm-logical-architecture.png')
)

$ErrorActionPreference = 'Stop'
$sourcePath = [System.IO.Path]::GetFullPath($Source)
$outputPath = [System.IO.Path]::GetFullPath($Output)

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Architecture SVG not found: $sourcePath"
}

New-Item -ItemType Directory -Path (Split-Path -Parent $outputPath) -Force | Out-Null
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) "frontier-rm-architecture-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = -1
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540
    $slide = $presentation.Slides.Add(1, 12)
    $picture = $slide.Shapes.AddPicture($sourcePath, 0, -1, 0, 0, 960, 540)
    $presentation.Export($temporaryDirectory, 'PNG', 1920, 1080)

    $rendered = Join-Path $temporaryDirectory 'Slide1.PNG'
    if (-not (Test-Path -LiteralPath $rendered -PathType Leaf)) {
        throw "PowerPoint did not create the expected PNG: $rendered"
    }
    Copy-Item -LiteralPath $rendered -Destination $outputPath -Force
}
finally {
    if ($presentation) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    if ($powerPoint) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null
    }
    Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
    [gc]::Collect()
    [gc]::WaitForPendingFinalizers()
}

$outputFile = Get-Item -LiteralPath $outputPath
Write-Output "Created: $($outputFile.FullName)"
Write-Output "Bytes: $($outputFile.Length)"