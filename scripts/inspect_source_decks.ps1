param(
    [string[]]$Decks = @(
        'C:\Users\anandnikhil\Downloads\Fabric IQ L100 Pitch Deck.PPTX',
        'C:\Users\anandnikhil\Downloads\NewPresentation_v1.pptx'
    ),
    [string]$Output = (Join-Path $PSScriptRoot '..\docs\source-deck-inventory.json')
)

$ErrorActionPreference = 'Stop'
$msoTrue = -1

function Get-ShapeText {
    param($Shape)
    try {
        if ($Shape.HasTextFrame -eq $msoTrue -and $Shape.TextFrame.HasText -eq $msoTrue) {
            return ($Shape.TextFrame.TextRange.Text -replace '[\r\n]+', ' ' -replace '\s+', ' ').Trim()
        }
    } catch {}
    return ''
}

function Get-NotesText {
    param($Slide)
    $parts = @()
    try {
        foreach ($shape in $Slide.NotesPage.Shapes) {
            $text = Get-ShapeText $shape
            if ($text -and $text -notmatch '^Click to (add|edit)') { $parts += $text }
        }
    } catch {}
    return (($parts -join ' ') -replace '\s+', ' ').Trim()
}

$powerPoint = $null
$inventory = @()
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = $msoTrue
    foreach ($deckPath in $Decks) {
        $fullPath = [System.IO.Path]::GetFullPath($deckPath)
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) { throw "Source deck not found: $fullPath" }
        $presentation = $null
        try {
            $presentation = $powerPoint.Presentations.Open($fullPath, $true, $true, $false)
            foreach ($slide in $presentation.Slides) {
                $texts = @()
                $pictures = 0
                foreach ($shape in $slide.Shapes) {
                    $text = Get-ShapeText $shape
                    if ($text) { $texts += [pscustomobject]@{ Text = $text; Top = [double]$shape.Top; Left = [double]$shape.Left } }
                    if ($shape.Type -in @(11, 13)) { $pictures++ }
                }
                $ordered = @($texts | Sort-Object Top, Left)
                $title = if ($ordered.Count) { $ordered[0].Text } else { "Slide $($slide.SlideIndex)" }
                if ($title.Length -gt 180) { $title = $title.Substring(0, 177) + '...' }
                $body = (($ordered | Select-Object -Skip 1 | ForEach-Object Text) -join ' | ')
                if ($body.Length -gt 1200) { $body = $body.Substring(0, 1197) + '...' }
                $notes = Get-NotesText $slide
                $inventory += [pscustomobject]@{
                    deck = [System.IO.Path]::GetFileName($fullPath)
                    slide = [int]$slide.SlideIndex
                    title = $title
                    body = $body
                    shapeCount = [int]$slide.Shapes.Count
                    pictureCount = [int]$pictures
                    hasNotes = [bool]$notes
                    notes = if ($notes.Length -gt 600) { $notes.Substring(0, 597) + '...' } else { $notes }
                }
            }
        }
        finally {
            if ($presentation) {
                $presentation.Close()
                [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
            }
        }
    }
}
finally {
    if ($powerPoint) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null
    }
    [gc]::Collect()
    [gc]::WaitForPendingFinalizers()
}

$outputPath = [System.IO.Path]::GetFullPath($Output)
New-Item -ItemType Directory -Path (Split-Path -Parent $outputPath) -Force | Out-Null
$inventory | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$inventory | Group-Object deck | ForEach-Object { [pscustomobject]@{ Deck = $_.Name; Slides = $_.Count } } | Format-Table -AutoSize
Write-Output "Inventory: $outputPath"
