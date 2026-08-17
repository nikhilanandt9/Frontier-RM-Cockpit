param([string]$Root = (Join-Path $PSScriptRoot '..'))

$ErrorActionPreference = 'Stop'
$rootPath = [System.IO.Path]::GetFullPath($Root)
$houseviewPath = Join-Path $rootPath 'packages\demo-data\houseview\houseviews.json'
$regulatoryPath = Join-Path $rootPath 'packages\demo-data\regulatory\faa_n16_control_pack.json'
$houseviews = Get-Content $houseviewPath -Raw | ConvertFrom-Json
$controlPack = Get-Content $regulatoryPath -Raw | ConvertFrom-Json
$wdFormatPDF = 17
$wdPageBreak = 7

function Add-Paragraph {
    param($Document, [string]$Text, [string]$Style = 'Normal', [int]$Color = 0, [bool]$KeepWithNext = $false)
    $paragraph = $Document.Content.Paragraphs.Add()
    $paragraph.Range.Text = $Text
    try { $paragraph.Range.Style = $Style } catch {}
    if ($Color) { $paragraph.Range.Font.Color = $Color }
    $paragraph.Format.KeepWithNext = $KeepWithNext
    $paragraph.Range.InsertParagraphAfter()
}

function Add-Bullets {
    param($Document, [string[]]$Items)
    foreach ($item in $Items) {
        $paragraph = $Document.Content.Paragraphs.Add()
        $paragraph.Range.Text = $item
        $paragraph.Range.ListFormat.ApplyBulletDefault()
        $paragraph.Range.InsertParagraphAfter()
    }
}

function Set-DocumentStyle {
    param($Document)
    $Document.PageSetup.TopMargin = 54
    $Document.PageSetup.BottomMargin = 54
    $Document.PageSetup.LeftMargin = 60
    $Document.PageSetup.RightMargin = 60
    $Document.Styles.Item('Normal').Font.Name = 'Aptos'
    $Document.Styles.Item('Normal').Font.Size = 10
    $Document.Styles.Item('Title').Font.Name = 'Aptos Display'
    $Document.Styles.Item('Title').Font.Size = 30
    $Document.Styles.Item('Title').Font.Color = 0x2000B0
    $Document.Styles.Item('Heading 1').Font.Name = 'Aptos Display'
    $Document.Styles.Item('Heading 1').Font.Color = 0x242124
    $Document.Styles.Item('Heading 2').Font.Name = 'Aptos Display'
    $Document.Styles.Item('Heading 2').Font.Color = 0x2000B0
    $footer = $Document.Sections.Item(1).Footers.Item(1).Range
    $footer.Text = 'FRONTIER RM · INTERNAL FICTIONAL DEMONSTRATION'
    $footer.Font.Name = 'Aptos'
    $footer.Font.Size = 8
    $footer.Font.Color = 0x6A6469
}

function Save-Pdf {
    param($Document, [string]$OutputPath)
    if (Test-Path $OutputPath) { Remove-Item $OutputPath -Force }
    $Document.SaveAs([ref]$OutputPath, [ref]$wdFormatPDF)
    Write-Output "Created: $OutputPath"
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    foreach ($report in $houseviews.reports) {
        $document = $word.Documents.Add()
        try {
            Set-DocumentStyle $document
            Add-Paragraph $document 'FRONTIER CIO RESEARCH' 'Subtitle' 0x6A6469 $true
            Add-Paragraph $document $report.title 'Title' 0 $true
            Add-Paragraph $document "As of $($report.asOf) · $($report.status.ToUpper()) · $($report.cioStance)" 'Subtitle' 0x2000B0 $false
            Add-Paragraph $document $report.disclaimer 'Quote' 0x1A008F $false
            Add-Paragraph $document 'Executive summary' 'Heading 1' 0 $true
            Add-Paragraph $document $report.executiveSummary
            foreach ($section in $report.sections) {
                Add-Paragraph $document "$($section.title) [$($section.id)]" 'Heading 1' 0 $true
                Add-Paragraph $document 'View' 'Heading 2' 0 $true
                Add-Paragraph $document $section.view
                Add-Paragraph $document 'Positioning' 'Heading 2' 0 $true
                Add-Paragraph $document $section.positioning
                Add-Paragraph $document 'Key risks' 'Heading 2' 0 $true
                Add-Bullets $document $section.risks
            }
            Add-Paragraph $document 'Watch items' 'Heading 1' 0 $true
            Add-Bullets $document $report.watchItems
            Add-Paragraph $document 'Important information' 'Heading 1' 0 $true
            Add-Paragraph $document $houseviews.provenance
            $output = Join-Path $rootPath "packages\demo-data\houseview\$($report.id).pdf"
            Save-Pdf $document $output
        } finally {
            $document.Close($false)
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null
        }
    }

    $document = $word.Documents.Add()
    try {
        Set-DocumentStyle $document
        Add-Paragraph $document 'FRONTIER ADVISORY GOVERNANCE' 'Subtitle' 0x6A6469 $true
        Add-Paragraph $document $controlPack.document.title 'Title' 0 $true
        Add-Paragraph $document "Source: $($controlPack.document.sourceTitle) · Issued 28 July 2011 · Last updated 29 December 2025" 'Subtitle' 0x2000B0 $false
        Add-Paragraph $document $controlPack.document.disclaimer 'Quote' 0x1A008F $false
        Add-Paragraph $document 'How to use this control pack' 'Heading 1' 0 $true
        Add-Paragraph $document 'Use the stable control IDs below to explain deterministic recommendation gates in the Frontier RM demonstration. Always consult the authoritative notice and the appropriate Compliance or Legal owner for interpretation.'
        foreach ($rule in $controlPack.rules) {
            Add-Paragraph $document "$($rule.id) · FAA-N16 paragraph $($rule.paragraph)" 'Heading 1' 0 $true
            Add-Paragraph $document $rule.title 'Heading 2' 0 $true
            Add-Paragraph $document $rule.summary
            Add-Paragraph $document "Applicability: $($rule.appliesTo -join ', ') · Gate: $($rule.gate)" 'Caption' 0x6A6469 $false
        }
        Add-Paragraph $document 'Retirement safeguard used in the demo' 'Heading 1' 0 $true
        Add-Paragraph $document 'Retirement invokes an internal enhanced review of income, liquidity, commitments, objectives, horizon, risk capacity and applicable knowledge or experience. It does not automatically set a client to risk score 1, and this control pack does not claim that MAS universally prohibits derivatives for retired clients.'
        $output = Join-Path $rootPath 'packages\demo-data\regulatory\frontier_faa_n16_demo_control_pack.pdf'
        Save-Pdf $document $output
    } finally {
        $document.Close($false)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null
    }
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}