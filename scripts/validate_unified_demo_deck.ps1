param(
    [string]$Deck = (Join-Path $PSScriptRoot '..\docs\Frontier_RM_Microsoft_Data_M365_A365_IQ_EBC.pptx'),
    [string]$PreviewDirectory = (Join-Path $PSScriptRoot '..\docs\deck-preview-unified')
)

$ErrorActionPreference = 'Stop'
$msoTrue = -1
$deckPath = [System.IO.Path]::GetFullPath($Deck)
$previewPath = [System.IO.Path]::GetFullPath($PreviewDirectory)
if (-not (Test-Path -LiteralPath $deckPath -PathType Leaf)) { throw "Deck not found: $deckPath" }

function Get-ShapeText {
    param($Shape)
    try {
        if ($Shape.HasTextFrame -eq $msoTrue -and $Shape.TextFrame.HasText -eq $msoTrue) {
            return $Shape.TextFrame.TextRange.Text.Trim()
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

$powerPoint = $null; $presentation = $null
$issues = @(); $allText = @(); $visibleText = @(); $zones = @(); $notesCount = 0
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = $msoTrue
    $presentation = $powerPoint.Presentations.Open($deckPath, $true, $true, $false)
    if ($presentation.Slides.Count -ne 40) { $issues += "Expected 40 slides; found $($presentation.Slides.Count)" }
    if ([math]::Abs($presentation.PageSetup.SlideWidth - 960) -gt 0.1 -or [math]::Abs($presentation.PageSetup.SlideHeight - 540) -gt 0.1) {
        $issues += "Unexpected slide size: $($presentation.PageSetup.SlideWidth)x$($presentation.PageSetup.SlideHeight)"
    }
    foreach ($slide in $presentation.Slides) {
        $notes = Get-NotesText $slide
        if ($notes) { $notesCount++ } else { $issues += "Slide $($slide.SlideIndex) has no speaker notes" }
        $allText += $notes
        foreach ($shape in $slide.Shapes) {
            $text = Get-ShapeText $shape
            if ($text) {
                $allText += $text
                $visibleText += $text
            }
            if ($shape.Name -like 'SCREENSHOT_ZONE_S*') {
                $zones += [pscustomobject]@{ Slide = [int]$slide.SlideIndex; Name = $shape.Name; X = [double]$shape.Left; Y = [double]$shape.Top; W = [double]$shape.Width; H = [double]$shape.Height }
            }
        }
    }
}
finally {
    if ($presentation) { $presentation.Close(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null }
    if ($powerPoint) { $powerPoint.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null }
    [gc]::Collect(); [gc]::WaitForPendingFinalizers()
}

$combined = $allText -join "`n"
$visibleCombined = $visibleText -join "`n"
$required = @(
    'One intelligent system around the Relationship Manager',
    'Microsoft Fabric: unified analytics SaaS',
    'Microsoft 365: where client work happens',
    'Agent 365: a control plane for enterprise agents',
    'What Fabric IQ adds',
    '15 entities · 13 relationships · 15 bindings',
    'Same gpt-4.1-mini deployment · different context envelope',
    'Evidence arrives before the question'
)
foreach ($term in $required) { if (-not $combined.Contains($term)) { $issues += "Required text missing: $term" } }

$staleOrProhibited = @(
    @{ Pattern = '7 tables\s*[·|,]\s*8 measures'; Message = 'Stale semantic-model counts found' },
    @{ Pattern = '11 entities\s*[·|,]\s*11 relationships'; Message = 'Stale Ontology counts found' },
    @{ Pattern = 'live Outlook|live SharePoint|continuous live agent execution|private chain-of-thought'; Message = 'Prohibited claim found' },
    @{ Pattern = 'Agent 365\s*[·:-]\s*(deployed|registered|managed)(?!.*evidence pending)'; Message = 'Unverified Agent 365 deployed-state claim found' }
)
foreach ($check in $staleOrProhibited) {
    $targetText = if ($check.Message -like 'Unverified Agent 365*') { $visibleCombined } else { $combined }
    if ($targetText -match $check.Pattern) { $issues += $check.Message }
}

if ($zones.Count -ne 18) { $issues += "Expected 18 screenshot zones; found $($zones.Count)" }

$previews = @(Get-ChildItem -LiteralPath $previewPath -Filter 'Slide*.PNG' -File -ErrorAction SilentlyContinue)
if ($previews.Count -ne 40) { $issues += "Expected 40 preview PNGs; found $($previews.Count)" }

$result = [pscustomobject]@{
    Deck = $deckPath
    Slides = 40
    Notes = $notesCount
    ScreenshotZones = $zones.Count
    PreviewCount = $previews.Count
    Issues = $issues.Count
}
$result | Format-List
if ($issues.Count) {
    $issues | ForEach-Object { Write-Output "ISSUE: $_" }
    exit 1
}
Write-Output 'Unified deck validation: PASS'
