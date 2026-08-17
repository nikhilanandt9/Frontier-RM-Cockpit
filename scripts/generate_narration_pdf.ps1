param(
    [string]$Source = (Join-Path $PSScriptRoot '..\docs\end-to-end-demo-narration.md'),
    [string]$Output = (Join-Path $PSScriptRoot '..\docs\Frontier_RM_End_to_End_Demo_Narration.pdf')
)

$ErrorActionPreference = 'Stop'
$sourcePath = [System.IO.Path]::GetFullPath($Source)
$outputPath = [System.IO.Path]::GetFullPath($Output)

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Narration source not found: $sourcePath"
}

$outputDirectory = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

$markdown = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$rendered = ConvertFrom-Markdown -InputObject $markdown
$tempHtml = Join-Path ([System.IO.Path]::GetTempPath()) "frontier-rm-narration-$([guid]::NewGuid().ToString('N')).html"

$styles = @'
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body {
  color: #242424;
  font-family: Aptos, Calibri, sans-serif;
  font-size: 10.5pt;
  line-height: 1.38;
  margin: 0;
}
h1, h2, h3, h4 { color: #191919; page-break-after: avoid; }
h1 { color: #a6192e; font-size: 25pt; margin: 0 0 14pt; }
h2 { border-bottom: 1px solid #d8d8d8; font-size: 17pt; margin: 20pt 0 8pt; padding-bottom: 4pt; }
h3 { color: #7e1526; font-size: 13pt; margin: 15pt 0 5pt; }
h4 { font-size: 11pt; margin: 12pt 0 4pt; }
p { margin: 0 0 7pt; }
ul, ol { margin: 4pt 0 9pt 18pt; padding: 0; }
li { margin: 0 0 3pt; }
blockquote {
  background: #f6f6f6;
  border-left: 4px solid #a6192e;
  margin: 7pt 0 10pt;
  padding: 8pt 10pt;
}
blockquote p { margin: 0 0 5pt; }
blockquote p:last-child { margin-bottom: 0; }
table { border-collapse: collapse; margin: 8pt 0 12pt; width: 100%; }
th { background: #a6192e; color: white; font-weight: 700; }
th, td { border: 1px solid #cfcfcf; padding: 5pt 7pt; text-align: left; }
code { background: #f0f0f0; color: #7e1526; font-family: Consolas, monospace; font-size: 9pt; padding: 1pt 3pt; }
hr { border: 0; border-top: 1px solid #cfcfcf; margin: 16pt 0; }
a { color: #8d1628; text-decoration: none; }
strong { color: #202020; }
'@

$title = [System.Net.WebUtility]::HtmlEncode((Get-Item -LiteralPath $sourcePath).BaseName)
$html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>$title</title>
<style>$styles</style>
</head>
<body>
$($rendered.Html)
</body>
</html>
"@

[System.IO.File]::WriteAllText($tempHtml, $html, [System.Text.UTF8Encoding]::new($false))

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($tempHtml, $false, $true)
    $document.ExportAsFixedFormat($outputPath, 17)
}
finally {
    if ($document) {
        $document.Close($false)
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null
    }
    if ($word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null
    }
    Remove-Item -LiteralPath $tempHtml -Force -ErrorAction SilentlyContinue
    [gc]::Collect()
    [gc]::WaitForPendingFinalizers()
}

if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
    throw "PDF export did not create the expected file: $outputPath"
}

$file = Get-Item -LiteralPath $outputPath
Write-Output "Created: $($file.FullName)"
Write-Output "Bytes: $($file.Length)"
