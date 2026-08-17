param(
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\docs\Frontier_RM_Microsoft_Data_M365_A365_IQ_EBC.pptx'),
    [string]$PreviewDirectory = (Join-Path $PSScriptRoot '..\docs\deck-preview-unified')
)

$ErrorActionPreference = 'Stop'
$ppLayoutBlank = 12
$ppSaveAsOpenXMLPresentation = 24
$ppSaveAsPDF = 32
$msoFalse = 0
$msoTrue = -1
$msoTextOrientationHorizontal = 1
$msoShapeRectangle = 1
$msoShapeRoundedRectangle = 5
$msoShapeOval = 9
$msoShapeChevron = 52
$msoLineDash = 4

$colors = @{
    Red = 0x2E19A6
    RedDark = 0x26127D
    RedLight = 0xF0E9FC
    Ink = 0x242124
    Charcoal = 0x302B2E
    Muted = 0x6A6469
    Line = 0xE4E1E3
    Canvas = 0xF7F7F8
    White = 0xFFFFFF
    Azure = 0xD27A00
    AzureLight = 0xFCEEDD
    Fabric = 0x948000
    FabricLight = 0xF6F4DE
    M365 = 0xC68A23
    M365Light = 0xFAF1E2
    Agent = 0x1672D9
    AgentLight = 0xEAF3FC
    IQ = 0xB237A4
    IQLight = 0xF7EAF5
    Green = 0x4F7A21
    GreenLight = 0xECF4E6
}

function Set-TextStyle {
    param($Range, [double]$Size, [int]$Color, [bool]$Bold = $false, [string]$Font = 'Aptos')
    $Range.Font.Name = $Font
    $Range.Font.Size = $Size
    $Range.Font.Color.RGB = $Color
    $Range.Font.Bold = $(if ($Bold) { $msoTrue } else { $msoFalse })
}

function Add-Text {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [double]$H, [double]$Size = 16, [int]$Color = $colors.Ink, [bool]$Bold = $false, [string]$Font = 'Aptos', [int]$Align = 1)
    $shape = $Slide.Shapes.AddTextbox($msoTextOrientationHorizontal, $X, $Y, $W, $H)
    $shape.TextFrame.MarginLeft = 0; $shape.TextFrame.MarginRight = 0; $shape.TextFrame.MarginTop = 0; $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = $msoTrue
    $shape.TextFrame.AutoSize = 0
    $shape.TextFrame2.AutoSize = 2
    $shape.TextFrame.TextRange.Text = $Text
    $shape.TextFrame.TextRange.ParagraphFormat.Alignment = $Align
    Set-TextStyle $shape.TextFrame.TextRange $Size $Color $Bold $Font
    return $shape
}

function Add-Box {
    param($Slide, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Fill = $colors.White, [int]$Line = $colors.Line, [bool]$Rounded = $false)
    $shape = $Slide.Shapes.AddShape($(if ($Rounded) { $msoShapeRoundedRectangle } else { $msoShapeRectangle }), $X, $Y, $W, $H)
    $shape.Fill.ForeColor.RGB = $Fill
    $shape.Line.ForeColor.RGB = $Line
    $shape.Line.Weight = 1
    return $shape
}

function Add-Pill {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [int]$Fill, [int]$TextColor = $colors.White)
    $null = Add-Box $Slide $X $Y $W 24 $Fill $Fill $true
    $null = Add-Text $Slide $Text ($X + 7) ($Y + 5) ($W - 14) 14 8 $TextColor $true 'Aptos' 2
}

function Add-Title {
    param($Slide, [string]$Section, [string]$Title, [string]$Subtitle = '', [int]$Accent = $colors.Red)
    $null = Add-Text $Slide $Section.ToUpperInvariant() 54 30 700 18 8 $Accent $true
    $null = Add-Text $Slide $Title 54 54 852 56 27 $colors.Ink $true 'Aptos Display'
    if ($Subtitle) { $null = Add-Text $Slide $Subtitle 54 113 852 35 11 $colors.Muted }
}

function Add-Footer {
    param($Slide, [int]$Number, [string]$Section)
    $line = $Slide.Shapes.AddLine(54, 510, 906, 510); $line.Line.ForeColor.RGB = $colors.Line
    $null = Add-Text $Slide "FRONTIER RM · $($Section.ToUpperInvariant())" 54 517 700 12 7 $colors.Muted $true
    $null = Add-Text $Slide ([string]$Number) 865 517 40 12 8 $colors.Muted $true 'Aptos' 3
}

function Add-Notes {
    param($Slide, [string]$Notes)
    try {
        $placeholders = $Slide.NotesPage.Shapes.Placeholders()
        for ($index = 1; $index -le $placeholders.Count; $index++) {
            $placeholder = $placeholders.Item($index)
            if ($placeholder.PlaceholderFormat.Type -eq 2) { $placeholder.TextFrame.TextRange.Text = $Notes; return }
        }
    } catch { Write-Warning "Could not add notes to slide $($Slide.SlideIndex): $($_.Exception.Message)" }
}

function Add-Bullets {
    param($Slide, [string[]]$Items, [double]$X, [double]$Y, [double]$W, [double]$H, [double]$Size = 13)
    $shape = Add-Text $Slide (($Items | ForEach-Object { "• $_" }) -join "`r") $X $Y $W $H $Size $colors.Ink
    $shape.TextFrame.TextRange.ParagraphFormat.SpaceAfter = 7
    return $shape
}

function Add-Card {
    param($Slide, [string]$Label, [string]$Title, [string]$Body, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Accent)
    $null = Add-Box $Slide $X $Y $W $H $colors.White $colors.Line $true
    $null = Add-Box $Slide $X $Y 7 $H $Accent $Accent
    $null = Add-Text $Slide $Label ($X + 19) ($Y + 15) ($W - 34) 15 8 $Accent $true
    $null = Add-Text $Slide $Title ($X + 19) ($Y + 40) ($W - 34) 42 14 $colors.Ink $true 'Aptos Display'
    $null = Add-Text $Slide $Body ($X + 19) ($Y + 88) ($W - 34) ($H - 101) 9.5 $colors.Muted
}

function Add-Flow {
    param($Slide, [string[]]$Labels, [double]$Y, [int[]]$Accents)
    $count = $Labels.Count; $gap = 22; $totalWidth = 852; $width = ($totalWidth - (($count - 1) * $gap)) / $count
    for ($index = 0; $index -lt $count; $index++) {
        $x = 54 + ($index * ($width + $gap)); $accent = $Accents[$index % $Accents.Count]
        $null = Add-Box $Slide $x $Y $width 76 $colors.White $accent $true
        $null = Add-Text $Slide ([string]($index + 1)).PadLeft(2, '0') ($x + 10) ($Y + 11) 30 14 8 $accent $true
        $null = Add-Text $Slide $Labels[$index] ($x + 10) ($Y + 34) ($width - 20) 30 10.5 $colors.Ink $true 'Aptos' 2
        if ($index -lt $count - 1) { $null = Add-Text $Slide '→' ($x + $width + 3) ($Y + 26) 17 20 12 $colors.Muted $true 'Aptos' 2 }
    }
}

function Add-ScreenshotZone {
    param($Slide, [int]$SlideNumber, [string]$System, [string]$Instruction, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Accent)
    $box = Add-Box $Slide $X $Y $W $H $colors.White $Accent $true
    $box.Name = "SCREENSHOT_ZONE_S$($SlideNumber.ToString('00'))"
    $box.Line.DashStyle = $msoLineDash; $box.Line.Weight = 1.5
    $null = Add-Pill $Slide "IMAGE PLACEHOLDER · $System" ($X + 15) ($Y + 15) ([Math]::Min(210, $W - 30)) $Accent
    $null = Add-Text $Slide '▧' ($X + ($W / 2) - 20) ($Y + ($H / 2) - 35) 40 32 24 $Accent $true 'Segoe UI Symbol' 2
    $null = Add-Text $Slide $Instruction ($X + 28) ($Y + ($H / 2) + 8) ($W - 56) 50 11 $colors.Ink $true 'Aptos' 2
    $null = Add-Text $Slide 'Replace this zone with your screenshot; retain the slide title and adjacent callouts.' ($X + 25) ($Y + $H - 35) ($W - 50) 20 8 $colors.Muted $false 'Aptos' 2
}

function Add-SectionSlide {
    param($Presentation, [int]$Number, [string]$Act, [string]$Title, [string]$Subtitle, [int]$Accent, [string]$Notes)
    $slide = $Presentation.Slides.Add($Number, $ppLayoutBlank)
    $null = Add-Box $slide 0 0 960 540 $colors.Charcoal $colors.Charcoal
    $null = Add-Box $slide 0 0 10 540 $Accent $Accent
    $null = Add-Pill $slide $Act 62 62 150 $Accent
    $null = Add-Text $slide $Title 62 155 790 100 34 $colors.White $true 'Aptos Display'
    $null = Add-Text $slide $Subtitle 62 282 760 55 15 0xD2CCCF
    $null = Add-Text $slide ([string]$Number).PadLeft(2, '0') 820 400 80 70 44 $Accent $true 'Aptos Display' 3
    Add-Notes $slide $Notes
    return $slide
}

function Add-StandardSlide {
    param($Presentation, [int]$Number, [string]$Section, [string]$Title, [string]$Subtitle, [int]$Accent, [string]$Notes)
    $slide = $Presentation.Slides.Add($Number, $ppLayoutBlank)
    $null = Add-Box $slide 0 0 960 540 $colors.Canvas $colors.Canvas
    Add-Title $slide $Section $Title $Subtitle $Accent
    Add-Footer $slide $Number $Section
    Add-Notes $slide $Notes
    return $slide
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$pdfPath = [System.IO.Path]::ChangeExtension($outputFullPath, '.pdf')
$previewFullPath = [System.IO.Path]::GetFullPath($PreviewDirectory)
New-Item -ItemType Directory -Path (Split-Path -Parent $outputFullPath) -Force | Out-Null
if (Test-Path $previewFullPath) { Remove-Item $previewFullPath -Recurse -Force }
New-Item -ItemType Directory -Path $previewFullPath -Force | Out-Null

$powerPoint = $null; $presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = $msoTrue
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960; $presentation.PageSetup.SlideHeight = 540

    # 1 Title
    $slide = $presentation.Slides.Add(1, $ppLayoutBlank)
    $null = Add-Box $slide 0 0 960 540 $colors.Charcoal $colors.Charcoal
    for ($x = 0; $x -le 960; $x += 48) { $line = $slide.Shapes.AddLine($x, 0, $x, 540); $line.Line.ForeColor.RGB = 0x4A4448; $line.Line.Transparency = 0.72 }
    for ($y = 0; $y -le 540; $y += 48) { $line = $slide.Shapes.AddLine(0, $y, 960, $y); $line.Line.ForeColor.RGB = 0x4A4448; $line.Line.Transparency = 0.72 }
    $null = Add-Box $slide 0 0 9 540 $colors.Red $colors.Red
    $null = Add-Pill $slide 'EXECUTIVE BRIEFING CENTRE' 62 54 190 $colors.Red
    $null = Add-Text $slide 'One intelligent system around the Relationship Manager' 62 128 820 112 35 $colors.White $true 'Aptos Display'
    $null = Add-Text $slide 'Microsoft Data · Azure · Microsoft 365 · Agent 365 · Fabric IQ' 62 270 780 35 17 0xD8C9EE $true 'Aptos Display'
    $null = Add-Text $slide 'A governed, human-controlled day in the life of John Doe' 62 402 620 25 14 0xC8C2C6
    $null = Add-Text $slide 'FRONTIER RM' 62 456 220 18 10 $colors.White $true
    Add-Notes $slide "Open with the EBC question: what changes when data, knowledge, applications and AI work as one governed system? This deck combines concepts restyled from the Fabric IQ L100 and NewPresentation_v1 source decks with verified Frontier deployment facts."

    # 2 Agenda
    $slide = Add-StandardSlide $presentation 2 'INTRODUCTION' 'Agenda' 'Five acts: business proof first, then the Microsoft platform that makes it possible.' $colors.Red "Preview the five acts. The RM story is the through-line; platform sections explain why the experience is possible."
    $agenda = @(
        @{N='01';T='RM DAY';B='A governed day in the life';C=$colors.Red},
        @{N='02';T='DATA + AZURE';B='Unified, open, AI-ready data';C=$colors.Azure},
        @{N='03';T='M365 + AGENT 365';B='Work context and agent control';C=$colors.Agent},
        @{N='04';T='FABRIC IQ';B='Shared business meaning';C=$colors.IQ},
        @{N='05';T='CLOSE';B='Outcomes and next steps';C=$colors.Green}
    )
    for ($i=0;$i -lt 5;$i++){Add-Card $slide $agenda[$i].N $agenda[$i].T $agenda[$i].B (54+$i*170) 190 150 185 $agenda[$i].C}

    $null = Add-SectionSlide $presentation 3 'ACT 1' 'A day in the life of John Doe' 'Begin with the client and the RM workflow. Technology follows the work.' $colors.Red "Introduce John Doe as a fictional Singapore Premier RM. Human judgment and accountability remain in control."

    # 4
    $slide = Add-StandardSlide $presentation 4 'RM DAY' 'The RM spends the day assembling context' 'Signals exist across systems, but connecting them still falls to the relationship manager.' $colors.Red "Describe swivel-chair work. Avoid naming customer systems not represented in the demo. Source concept: Fabric IQ L100 slides 7-10, adapted to RM work."
    Add-Card $slide '01' 'Find context' 'Accounts, holdings, profile, consent, interactions.' 54 180 195 220 $colors.Red
    Add-Card $slide '02' 'Interpret need' 'Events, objectives, liquidity, risk, market context.' 268 180 195 220 $colors.Azure
    Add-Card $slide '03' 'Prepare' 'Correspondence, guidance, talk track, checks.' 482 180 195 220 $colors.IQ
    Add-Card $slide '04' 'Follow up' 'Client email, CRM draft, evidence trail.' 696 180 195 220 $colors.Green

    # 5
    $slide = Add-StandardSlide $presentation 5 'RM DAY' 'The moments that matter' 'A working day moves from signal to governed follow-up.' $colors.Red "Use Daniel Lim as the primary through-line. This timeline mirrors the Guided Story and live-demo sequence."
    Add-Flow $slide @('08:30 Triage','09:15 Understand','10:00 Prepare','11:30 Decide','12:15 Follow up') 225 @($colors.Red,$colors.Azure,$colors.Fabric,$colors.IQ,$colors.Green)
    $null = Add-Text $slide 'John remains accountable at every transition.' 230 370 500 30 16 $colors.RedDark $true 'Aptos' 2

    # 6 placeholder
    $slide = Add-StandardSlide $presentation 6 'RM DAY' 'Start with the Guided Story' 'A 60-second executive promise before the working cockpit.' $colors.Red "Insert a Guided Story opening or montage. Launch with ?present=1. After the story say: now let me show the working system behind each moment."
    Add-ScreenshotZone $slide 6 'GUIDED STORY' 'Insert the opening scene or a montage of the seven scenes.' 54 165 555 310 $colors.Red
    Add-Card $slide 'LIVE HANDOFF' 'Seven scenes' 'The day begins · sources converge · Client 360 · briefing · recommendations · draft · impact.' 635 165 271 148 $colors.Red
    Add-Card $slide 'CONTROL' 'Presenter-ready' 'Auto progression, pause, direct scene navigation, and deterministic rehearsal fallback.' 635 330 271 145 $colors.Charcoal

    # 7 placeholder
    $slide = Add-StandardSlide $presentation 7 'RM DAY' 'Today: priorities become a working plan' 'Portfolio signals, report-style metrics, workflow cards, and action progress share one data contract.' $colors.Red "Show the Today page. Metrics are interactive reports; the signal feed is fictional demo data."
    Add-ScreenshotZone $slide 7 'TODAY' 'Insert Today with morning pulse, metrics, workflow cards, and day plan.' 54 165 600 310 $colors.Red
    Add-Card $slide 'OUTCOME' 'Actionable, not decorative' 'Metrics drill into clients and actions. Completing work updates session state and coverage.' 680 190 226 215 $colors.Red

    # 8 placeholder
    $slide = Add-StandardSlide $presentation 8 'RM DAY' 'Client 360: governed context before conversation' "Daniel's relationship, consent, timeline, profile, and activity evidence in one decision surface." $colors.Red "Show Daniel Lim. Declared Investment Risk Profile is separate from activity-derived Observed Behaviour. Activity may trigger review but cannot rewrite the declared score."
    Add-ScreenshotZone $slide 8 'CLIENT 360' 'Insert Daniel Lim Client 360 with risk and activity evidence visible.' 54 165 600 310 $colors.Red
    Add-Card $slide 'CONTROL' 'Declared ≠ observed' 'Observed activity is review evidence. The client-confirmed profile remains controlled.' 680 190 226 215 $colors.Green

    # 9
    $slide = Add-StandardSlide $presentation 9 'RM DAY' 'Three artifacts, one governed progression' 'Each stage produces something John can inspect, challenge, and improve.' $colors.Red "Explain stage locks and human review. Nothing is sent, committed, or transacted."
    Add-Flow $slide @('Prepare briefing','Custom recommendations','Opportunity draft') 205 @($colors.Red,$colors.IQ,$colors.Green)
    $null = Add-Bullets $slide @('Evidence and required checks travel with every artifact','Later stages unlock only after earlier context exists','John edits and approves; the system never executes') 150 335 660 100 13

    # 10 split placeholders
    $slide = Add-StandardSlide $presentation 10 'RM DAY' 'Same model. Different grounding.' 'The Opportunity Studio makes the value of Fabric IQ directly observable.' $colors.IQ "Use the same Daniel stage in both modes. Without IQ is not wrong; it is deliberately less informed. Fabric IQ does not guarantee suitability or compliance."
    Add-ScreenshotZone $slide 10 'WITHOUT FABRIC IQ' 'Insert the General AI draft with no enterprise citations.' 54 165 400 270 $colors.Muted
    Add-ScreenshotZone $slide 10 'WITH FABRIC IQ' 'Insert the Fabric IQ grounded artifact with evidence and controls.' 506 165 400 270 $colors.IQ
    $null = Add-Text $slide 'gpt-4.1-mini · managed identity in both modes' 280 455 400 20 12 $colors.IQ $true 'Aptos' 2

    # 11 split
    $slide = Add-StandardSlide $presentation 11 'RM DAY' 'Sources and Frontier Copilot' 'Client voice and approved knowledge remain available across the workflow.' $colors.M365 "Current demo uses authored fictional Outlook/SharePoint-style sources, not live Microsoft Graph retrieval. Copilot is persistent and grounded in approved sources."
    Add-ScreenshotZone $slide 11 'SOURCES' 'Insert an authored Daniel email or advisory document.' 54 165 400 285 $colors.M365
    Add-ScreenshotZone $slide 11 'FRONTIER COPILOT' 'Insert the persistent Copilot panel with a cited answer.' 506 165 400 285 $colors.Agent

    # 12
    $slide = Add-StandardSlide $presentation 12 'RM DAY' 'CIO Houseview meets client evidence and controls' 'The active 19 August 2026 market view is tailored without collapsing research, risk, activity, and controls.' $colors.IQ "Show Daniel; optionally use Mei for retirement enhanced review. The internal FAA-N16 pack is not the official notice or legal advice."
    Add-ScreenshotZone $slide 12 'CIO HOUSEVIEW' 'Insert the report reader and selected-client advisory panel.' 54 165 600 310 $colors.IQ
    Add-Card $slide 'BOUNDARY' 'Compliance-aware' 'Retained and suppressed fictional candidates remain explainable. No automatic suitability conclusion.' 680 190 226 215 $colors.Green

    # 13
    $slide = Add-StandardSlide $presentation 13 'RM DAY' 'Transparent multi-agent operations' 'Service health, synthetic telemetry, and captured agent replay remain visibly distinct.' $colors.Agent "Show verified, revision-required, and rehearsal runs. Captured replay is not continuous execution and does not expose private reasoning."
    Add-ScreenshotZone $slide 13 'OPERATIONS' 'Insert connected services, run selector, agent fleet, event stream, and outcome.' 54 165 600 310 $colors.Agent
    Add-Card $slide 'TRUTH STATES' 'Live ≠ synthetic ≠ replay' 'Health is deployed state. Motion is demo telemetry. Events are a selected captured run.' 680 190 226 215 $colors.Agent

    # 14
    $slide = Add-StandardSlide $presentation 14 'RM DAY' 'From application navigation to client judgement' 'The system returns attention to the work only the RM can do.' $colors.Green "Avoid claiming measured productivity gains. Frame these as designed workflow shifts."
    Add-Card $slide 'BEFORE' 'Assemble the picture' 'Search context · reconcile signals · draft from blank · document provenance manually.' 90 190 330 220 $colors.Muted
    $arrow = $slide.Shapes.AddShape($msoShapeChevron, 445, 250, 70, 75); $arrow.Fill.ForeColor.RGB=$colors.Red; $arrow.Line.Visible=$msoFalse
    Add-Card $slide 'WITH FRONTIER RM' 'Start from evidence' 'Priorities sequenced · context connected · artifacts prepared · judgement retained.' 540 190 330 220 $colors.Green

    $null = Add-SectionSlide $presentation 15 'ACT 2' 'From fragmented data to an intelligent data estate' 'Microsoft Data and Azure provide the operational, analytical, and AI-ready foundation.' $colors.Azure "Transition from the business proof to the broader Microsoft capability landscape. Not every service shown is deployed in Frontier."

    # 16 landscape
    $slide = Add-StandardSlide $presentation 16 'MICROSOFT DATA + AZURE' 'The Microsoft data-to-AI capability landscape' 'Operational data, analytics, governance, AI, and work experiences form one connected system.' $colors.Azure "This is broader Microsoft capability context, not the Frontier bill of materials."
    $layers=@(
        @{Y=175;T='WORK + ACTION';B='Microsoft 365 · Dynamics 365 · Power BI · custom applications';C=$colors.M365},
        @{Y=235;T='AI + AGENTS';B='Azure AI · Microsoft Foundry · Copilot Studio · Agent 365';C=$colors.Agent},
        @{Y=295;T='ANALYTICS + IQ';B='Microsoft Fabric · Power BI · Real-Time Intelligence · Fabric IQ';C=$colors.IQ},
        @{Y=355;T='OPERATIONAL DATA';B='Azure SQL · PostgreSQL · Cosmos DB · Event Hubs · open ecosystems';C=$colors.Azure},
        @{Y=415;T='SECURITY + GOVERNANCE';B='Microsoft Entra · Purview · Defender · policy and lineage';C=$colors.Green}
    ); foreach($l in $layers){$null=Add-Box $slide 90 $l.Y 780 45 $l.C $l.C $true;$null=Add-Text $slide $l.T 110 ($l.Y+9) 180 20 10 $colors.White $true;$null=Add-Text $slide $l.B 300 ($l.Y+9) 540 20 10 $colors.White}

    # 17 Azure services
    $slide = Add-StandardSlide $presentation 17 'MICROSOFT DATA + AZURE' 'Azure data services: operational, open, and real-time' 'Choose the right engine while keeping governance, identity, and AI readiness consistent.' $colors.Azure "Capability landscape only. Frontier currently uses Fabric Lakehouse and related Azure services; do not imply every service is deployed."
    Add-Card $slide 'TRANSACTIONAL' 'Operational data' 'Azure SQL · PostgreSQL · Cosmos DB for cloud-native and mission-critical applications.' 54 175 260 230 $colors.Azure
    Add-Card $slide 'STREAMING' 'Real-time data' 'Event Hubs and streaming patterns bring signals into operational analytics.' 350 175 260 230 $colors.Agent
    Add-Card $slide 'OPEN' 'Lake and ecosystem' 'Storage, open formats, shortcuts, and interoperability with partner engines.' 646 175 260 230 $colors.Fabric

    # 18 Fabric
    $slide = Add-StandardSlide $presentation 18 'MICROSOFT DATA + AZURE' 'Microsoft Fabric: unified analytics SaaS' 'A complete data platform with shared experiences, governance, Copilot, and OneLake.' $colors.Fabric "Restyled from source decks: Fabric IQ L100 slides 14-15 and NewPresentation slide 5. Describe platform capability, then connect to Frontier deployment on slide 20."
    $workloads=@('Data Factory','Data Engineering','Data Science','Data Warehouse','Real-Time Intelligence','Power BI','Fabric IQ'); for($i=0;$i -lt $workloads.Count;$i++){ $x=54+($i%4)*213;$y=180+[math]::Floor($i/4)*90;$null=Add-Box $slide $x $y 195 70 $colors.White $colors.Fabric $true;$null=Add-Text $slide $workloads[$i] ($x+12) ($y+24) 171 20 11 $colors.Ink $true 'Aptos' 2 }
    $null=Add-Box $slide 160 390 640 55 $colors.Fabric $colors.Fabric $true;$null=Add-Text $slide 'ONE LAKE · ONE SECURITY MODEL · ONE SAAS EXPERIENCE' 190 408 580 20 12 $colors.White $true 'Aptos' 2

    # 19 OneLake
    $slide = Add-StandardSlide $presentation 19 'MICROSOFT DATA + AZURE' 'OneLake: one logical data lake for the organization' 'Open formats and shortcuts reduce unnecessary copies while preserving domain ownership.' $colors.Fabric "Restyled from NewPresentation slide 7. Avoid saying zero ETL universally; describe shortcuts and mirroring as capability options."
    Add-Flow $slide @('Cloud + on-prem sources','Shortcuts / mirroring','OneLake open data','Fabric workloads','Governed consumption') 210 @($colors.Azure,$colors.Agent,$colors.Fabric,$colors.IQ,$colors.Green)
    $null=Add-Bullets $slide @('One logical data lake across Fabric','Open table formats and interoperable engines','Domain organization, discovery, lineage, and security') 190 340 580 100 13

    # 20 placeholder
    $slide = Add-StandardSlide $presentation 20 'MICROSOFT DATA + AZURE' 'Frontier data foundation: Bronze, Silver, Gold' 'A schema-enabled Lakehouse turns deterministic source data into governed RM context.' $colors.Fabric "Verified Frontier deployment: 21 Bronze, 21 Silver, 12 Gold tables. The cockpit serves a validated checked-in snapshot rather than querying Fabric on every page load."
    Add-ScreenshotZone $slide 20 'FABRIC WORKSPACE' 'Insert workspace, Lakehouse, medallion notebook, or tables.' 54 165 520 300 $colors.Fabric
    $medallion = @(
        @{N='01';T='21 Bronze';B='Source-aligned landing tables';C=$colors.Azure},
        @{N='02';T='21 Silver';B='Validated, deduplicated domain data';C=$colors.Fabric},
        @{N='03';T='12 Gold';B='RM-ready business context';C=$colors.Green}
    )
    for ($index=0; $index -lt $medallion.Count; $index++) {
        $y = 165 + ($index * 95)
        $null=Add-Box $slide 610 $y 296 82 $colors.White $medallion[$index].C $true
        $null=Add-Text $slide $medallion[$index].N 625 ($y+14) 28 14 8 $medallion[$index].C $true
        $null=Add-Text $slide $medallion[$index].T 665 ($y+12) 215 20 12 $colors.Ink $true
        $null=Add-Text $slide $medallion[$index].B 665 ($y+39) 215 18 9 $colors.Muted
    }
    $null=Add-Text $slide '20 fictional clients · 399 rows' 635 455 246 20 11 $colors.Fabric $true 'Aptos' 2

    # 21 placeholder
    $slide = Add-StandardSlide $presentation 21 'MICROSOFT DATA + AZURE' 'Power BI and Direct Lake: business meaning at data speed' 'Curated measures and relationships ground analytics and AI in trusted business concepts.' $colors.Azure "Verified model: 12 tables, 11 measures, Direct Lake, DAX-validated. Direct DAX remains authoritative for hidden identifiers and monetary values."
    Add-ScreenshotZone $slide 21 'SEMANTIC MODEL / POWER BI' 'Insert model diagram, DAX validation, or Power BI view.' 54 165 560 300 $colors.Azure
    Add-Card $slide 'DIRECT LAKE' '12 tables · 11 measures' 'Shared business definitions and relationships without duplicating imported data.' 645 180 261 120 $colors.Azure
    Add-Card $slide 'AUTHORITY' 'Validated DAX' 'Authoritative monetary values and hidden identifiers stay governed.' 645 320 261 120 $colors.Green

    # 22 transition
    $slide = Add-StandardSlide $presentation 22 'MICROSOFT DATA + AZURE' 'From data platform to business workflow' 'Data becomes valuable when trusted meaning reaches people, applications, and agents.' $colors.Azure "Bridge to Microsoft 365 and Agent 365. The next section distinguishes work context from data context and agent control."
    Add-Flow $slide @('Operational + analytical data','Shared business meaning','Work context','Governed agents','RM action') 230 @($colors.Azure,$colors.Fabric,$colors.M365,$colors.Agent,$colors.Green)

    $null = Add-SectionSlide $presentation 23 'ACT 3' 'Bring intelligence into the flow of work. Govern agents as a workforce.' 'Microsoft 365 supplies work context; Agent 365 provides the enterprise control-plane pattern.' $colors.Agent "New first-class section informed by NewPresentation slides 20-24. Agent 365 deployment wording remains evidence-gated."

    # 24 M365
    $slide = Add-StandardSlide $presentation 24 'MICROSOFT 365 + AGENT 365' 'Microsoft 365: where client work happens' 'Communication, content, meetings, collaboration, and Copilot form the everyday work surface.' $colors.M365 "Restyled from NewPresentation slides 20-22. This is Microsoft platform capability. Frontier uses authored source patterns and an authenticated Teams bot, not live Graph retrieval."
    Add-Card $slide 'COMMUNICATE' 'Outlook + Teams' 'Client conversations, meetings, calls, and follow-up.' 54 180 260 225 $colors.M365
    Add-Card $slide 'KNOWLEDGE' 'SharePoint + files' 'Authoritative documents, versions, permissions, and collaboration.' 350 180 260 225 $colors.Fabric
    Add-Card $slide 'ASSIST' 'Microsoft 365 Copilot' 'Work-aware assistance across people, content, activity, and workflows.' 646 180 260 225 $colors.Agent

    # 25 Work context
    $slide = Add-StandardSlide $presentation 25 'MICROSOFT 365 + AGENT 365' 'Work context is continuous, evolving, and connected' 'Snapshots miss the sequence of conversations, content, people, and changing priorities.' $colors.M365 "Restyled from NewPresentation slides 23-24. Use capability language; avoid claiming Work IQ is integrated into the current Frontier app."
    Add-Flow $slide @('People','Messages + meetings','Files + knowledge','Activity + memory','Business change') 210 @($colors.M365,$colors.Agent,$colors.Fabric,$colors.IQ,$colors.Green)
    $null=Add-Text $slide 'Work IQ connects context across the flow of work.' 230 350 500 30 16 $colors.M365 $true 'Aptos' 2

    # 26 placeholders
    $slide = Add-StandardSlide $presentation 26 'MICROSOFT 365 + AGENT 365' 'Microsoft 365 patterns in the RM journey' 'Client voice and collaboration can enrich governed data while preserving permissions and provenance.' $colors.M365 "Current implementation: authored Outlook/SharePoint-style sources and authenticated Teams bot. Target capability: production Microsoft 365 connections under tenant policy."
    Add-ScreenshotZone $slide 26 'OUTLOOK / SHAREPOINT' 'Insert M365 source or work-context screenshot.' 54 165 400 275 $colors.M365
    Add-ScreenshotZone $slide 26 'TEAMS / COPILOT' 'Insert Teams bot or Copilot delivery screenshot.' 506 165 400 275 $colors.Agent

    # 27 Agent 365 definition
    $slide = Add-StandardSlide $presentation 27 'MICROSOFT 365 + AGENT 365' 'Agent 365: a control plane for enterprise agents' 'Know every agent, control access and actions, and operate the agent estate through its lifecycle.' $colors.Agent "Agent 365 is requested as deployed but evidence is not yet present in the Frontier inventory. Present as capability/target state until registration or control-plane evidence is supplied."
    Add-Card $slide 'IDENTITY' 'Know every agent' 'Unique identity, ownership, purpose, and trust posture.' 54 180 260 225 $colors.Agent
    Add-Card $slide 'CONTROL' 'Govern access + action' 'Least privilege, policy, data scope, tools, and approval.' 350 180 260 225 $colors.Green
    Add-Card $slide 'OPERATE' 'Observe the lifecycle' 'Inventory, health, evaluation, incidents, versions, and retirement.' 646 180 260 225 $colors.IQ

    # 28 placeholder
    $slide = Add-StandardSlide $presentation 28 'MICROSOFT 365 + AGENT 365' 'Know every agent: identity and registry' 'An enterprise agent estate needs ownership and discovery before it can be governed.' $colors.Agent "Replace with verified Agent 365 registry evidence when provided. Until then, the status banner must remain evidence pending."
    Add-ScreenshotZone $slide 28 'AGENT 365 REGISTRY' 'Insert registered-agent inventory or identity screenshot.' 54 165 560 295 $colors.Agent
    Add-Card $slide 'STATUS' 'Evidence pending' 'Do not mark Agent 365 registration as verified until supporting details are supplied.' 645 190 261 200 $colors.Agent

    # 29 control
    $slide = Add-StandardSlide $presentation 29 'MICROSOFT 365 + AGENT 365' 'Control what agents can access and do' 'Agent identity is useful only when paired with least privilege, policy, and human approval.' $colors.Green "Connect this target control-plane pattern to verified Frontier controls: managed identity, scoped tools, deterministic gates, and human review."
    Add-Flow $slide @('Agent identity','Data + tool scope','Policy evaluation','Approval boundary','Auditable action') 215 @($colors.Agent,$colors.Azure,$colors.Green,$colors.Red,$colors.IQ)
    $null=Add-Bullets $slide @('Separate read, draft, and execute permissions','Preserve source-level authorization and provenance','Require explicit approval for consequential actions') 190 340 580 95 13

    # 30 placeholder
    $slide = Add-StandardSlide $presentation 30 'MICROSOFT 365 + AGENT 365' 'Operate agents with observability and lifecycle controls' 'Health, evaluations, versions, incidents, and retirement turn individual agents into a managed estate.' $colors.Agent "Insert Agent 365 operations evidence if available. Current Frontier Operations page shows deployed health, synthetic telemetry, and captured replay, not Agent 365 control-plane telemetry."
    Add-ScreenshotZone $slide 30 'AGENT 365 OPERATIONS' 'Insert observability, evaluation, lifecycle, or incident view.' 54 165 560 295 $colors.Agent
    Add-Card $slide 'LIFECYCLE' 'Build → evaluate → deploy → observe → improve → retire' 'Use explicit owners, versions, policies, and evidence throughout.' 645 190 261 200 $colors.IQ

    # 31 estate matrix
    $slide = Add-StandardSlide $presentation 31 'MICROSOFT 365 + AGENT 365' 'Frontier agent estate mapped to Agent 365' 'A transparent inventory makes the target registration and governance work concrete.' $colors.Agent "All current statuses are verified deployed in Foundry/Fabric, but Agent 365 management is evidence pending. Update this slide only after supplied proof."
    $agents=@('RM Orchestrator v2','Customer Intelligence v3','Market Context v2','Meeting Preparation v2','Fabric Data Agent','Teams delivery'); for($i=0;$i -lt $agents.Count;$i++){ $y=170+$i*48;$null=Add-Box $slide 90 $y 780 38 $colors.White $colors.Line $true;$null=Add-Text $slide $agents[$i] 110 ($y+10) 260 16 10 $colors.Ink $true;$null=Add-Pill $slide $(if($i -eq 4){'FABRIC · DEPLOYED'}else{'FOUNDRY / AZURE · DEPLOYED'}) 390 ($y+7) 155 $(if($i -eq 4){$colors.Fabric}else{$colors.Azure});$null=Add-Pill $slide 'AGENT 365 · EVIDENCE PENDING' 570 ($y+7) 230 $colors.Agent }

    $null = Add-SectionSlide $presentation 32 'ACT 4' 'From unified data to shared business meaning' 'Fabric IQ gives people and AI a connected language for the state of the business.' $colors.IQ "Transition from work/agent context to Fabric IQ business context. Source concepts: Fabric IQ L100 slides 11-13 and 17-20."

    # 33 IQ definition
    $slide = Add-StandardSlide $presentation 33 'FABRIC IQ' 'What Fabric IQ adds' 'A semantic foundation that connects data, models, rules, relationships, and actions.' $colors.IQ "Restyled from L100 slides 17-20. Keep claims at executive level and distinguish deployed Frontier subset from wider platform capability."
    Add-Card $slide 'MEANING' 'Unify semantics' 'Shared definitions across data, models, rules, and actions.' 54 180 260 225 $colors.IQ
    Add-Card $slide 'CONTEXT' 'Understand relationships' 'Reason over business entities and what connects them.' 350 180 260 225 $colors.Fabric
    Add-Card $slide 'GROUNDING' 'Power people + AI' 'Give analytics, Copilot, and agents consistent business context.' 646 180 260 225 $colors.Agent

    # 34 placeholder
    $slide = Add-StandardSlide $presentation 34 'FABRIC IQ' 'Ontology: model the business, not just the tables' 'Business entities, relationships, and rules extend trusted semantics into connected intelligence.' $colors.IQ "Verified Frontier Ontology definition: 15 entities, 13 relationships, 15 bindings, 58 parts. Graph routing remains disabled pending readiness. Source concepts: L100 slides 32-34."
    Add-ScreenshotZone $slide 34 'FABRIC IQ ONTOLOGY' 'Insert deployed definition, entity map, or graph view.' 54 165 560 295 $colors.IQ
    Add-Card $slide 'DEPLOYED DEFINITION' '15 entities · 13 relationships · 15 bindings' 'Definition readback is validated. Live graph traversal is not claimed.' 645 190 261 200 $colors.IQ

    # 35 value chain
    $slide = Add-StandardSlide $presentation 35 'FABRIC IQ' 'The IQ value chain: data → meaning → context → action' 'Connected intelligence is a sequence of governed contracts, not one opaque model.' $colors.IQ "Show how Fabric and IQ complement M365 work context and Agent 365 control."
    Add-Flow $slide @('OneLake + Fabric data','Semantic model + Ontology','Data Agent + Copilot','Foundry specialists','RM-approved action') 220 @($colors.Fabric,$colors.IQ,$colors.Azure,$colors.Agent,$colors.Green)

    # 36 conceptual comparison
    $slide = Add-StandardSlide $presentation 36 'FABRIC IQ' 'Fabric IQ in the RM workflow' 'The same model becomes more tailored and explainable when grounded in governed enterprise context.' $colors.IQ "Mirror the live toggle. Do not say general mode is wrong or IQ mode is automatically compliant."
    Add-Card $slide 'WITHOUT IQ' 'General AI draft' 'Basic client facts · generic framing · mandatory safety checks · no enterprise citations.' 80 185 355 220 $colors.Muted
    Add-Card $slide 'WITH FABRIC IQ' 'Governed RM artifact' 'Client 360 · sources · Houseview · activity · relationships · controls · provenance.' 525 185 355 220 $colors.IQ
    $null=Add-Text $slide 'Same gpt-4.1-mini deployment · different context envelope' 260 440 440 22 12 $colors.IQ $true 'Aptos' 2

    # 37 placeholder
    $slide = Add-StandardSlide $presentation 37 'FABRIC IQ' 'Fabric Data Agent, Foundry, and Agent 365' 'Governed retrieval, specialist orchestration, enterprise control, and human review are distinct responsibilities.' $colors.Agent "Verified: semantic-model-only Fabric Data Agent and four Foundry agents. Agent 365 band remains evidence pending. Source concepts: L100 slides 25-26 and 36."
    Add-ScreenshotZone $slide 37 'DATA AGENT / FOUNDRY / AGENT 365' 'Insert Fabric Data Agent, Foundry project, or verified Agent 365 evidence.' 54 165 520 295 $colors.Agent
    $responsibilities = @(
        @{N='01';T='Data Agent';B='Governed semantic retrieval';C=$colors.Fabric},
        @{N='02';T='Foundry agents';B='Specialist orchestration';C=$colors.Azure},
        @{N='03';T='Agent 365';B='Control plane · evidence pending';C=$colors.Agent},
        @{N='04';T='RM review';B='Human accountability';C=$colors.Green}
    )
    for ($index=0; $index -lt $responsibilities.Count; $index++) {
        $y = 165 + ($index * 76)
        $null=Add-Box $slide 610 $y 296 66 $colors.White $responsibilities[$index].C $true
        $null=Add-Text $slide $responsibilities[$index].N 625 ($y+12) 28 14 8 $responsibilities[$index].C $true
        $null=Add-Text $slide $responsibilities[$index].T 665 ($y+10) 215 18 11 $colors.Ink $true
        $null=Add-Text $slide $responsibilities[$index].B 665 ($y+34) 215 16 8.5 $colors.Muted
    }

    # 38 architecture placeholder + native
    $slide = Add-StandardSlide $presentation 38 'FABRIC IQ' 'End-to-end reference architecture and governance' 'The deployed system keeps evidence, identity, controls, and human accountability visible.' $colors.Green "Verified deployed path: authored sources, Fabric medallion, Direct Lake model, Ontology definition, Data Agent, Foundry agents, managed-identity Azure OpenAI, Container Apps/Teams, RM cockpit. Agent 365 is not shown as deployed until evidence arrives."
    Add-ScreenshotZone $slide 38 'REFERENCE ARCHITECTURE' 'Optionally replace with your detailed architecture screenshot.' 54 165 360 285 $colors.Green
    $architecture = @(
        @{T='Sources';C=$colors.M365}, @{T='Fabric';C=$colors.Fabric}, @{T='IQ';C=$colors.IQ},
        @{T='Agents';C=$colors.Agent}, @{T='RM cockpit';C=$colors.Red}
    )
    for ($index=0; $index -lt $architecture.Count; $index++) {
        $y = 165 + ($index * 50)
        $null = Add-Box $slide 455 $y 210 38 $colors.White $architecture[$index].C $true
        $null = Add-Text $slide ([string]($index + 1)).PadLeft(2,'0') 467 ($y + 10) 25 14 8 $architecture[$index].C $true
        $null = Add-Text $slide $architecture[$index].T 500 ($y + 9) 145 17 10 $colors.Ink $true
        if ($index -lt $architecture.Count - 1) { $null = Add-Text $slide '↓' 665 ($y + 28) 18 18 10 $colors.Muted $true 'Aptos' 2 }
    }
    $null=Add-Bullets $slide @('Managed identity and scoped tools','Stable source IDs and deterministic gates','Public rationale and human approval','Agent 365: evidence pending') 700 175 206 225 10

    # 39 takeaways
    $slide = Add-StandardSlide $presentation 39 'CLOSING' 'Three takeaways and a practical next step' 'Turn platform capability into repeatable, governed RM outcomes.' $colors.Green "Close the platform tour. Next step should be framed as prioritization and validation, not an assumed production rollout."
    Add-Card $slide '01' 'Unify the data foundation' 'Operational and analytical data becomes open, governed, and AI-ready with Azure and Fabric.' 54 180 260 225 $colors.Azure
    Add-Card $slide '02' 'Connect work and agents' 'Microsoft 365 brings work context; Agent 365 provides the target control-plane pattern.' 350 180 260 225 $colors.Agent
    Add-Card $slide '03' 'Share business meaning' 'Fabric IQ grounds people, analytics, and agents in consistent context and provenance.' 646 180 260 225 $colors.IQ
    $null=Add-Text $slide 'NEXT: prioritize production connections, Agent 365 evidence, and the next RM journeys.' 130 445 700 20 12 $colors.Green $true 'Aptos' 2

    # 40 close
    $slide = $presentation.Slides.Add(40, $ppLayoutBlank)
    $null = Add-Box $slide 0 0 960 540 $colors.Charcoal $colors.Charcoal
    $null = Add-Text $slide 'THE QUESTION WE STARTED WITH' 62 65 600 18 9 0xB8B0B4 $true
    $null = Add-Text $slide 'What changes when the bank works as one intelligent system?' 62 125 800 85 31 $colors.White $true 'Aptos Display'
    $null = Add-Box $slide 62 255 820 2 $colors.Red $colors.Red
    $null = Add-Text $slide 'Evidence arrives before the question. Artifacts arrive before the blank page. Human judgement remains in control.' 62 305 800 95 20 $colors.White $false 'Aptos Display'
    $null = Add-Text $slide 'MICROSOFT DATA · M365 · AGENT 365 · FABRIC IQ · AZURE' 62 465 720 18 9 0xB8B0B4 $true
    Add-Notes $slide "Final close: the value is not another chatbot. It is a governed operating system for RM work. Agent 365 deployment language remains evidence-gated until verified."

    if ($presentation.Slides.Count -ne 40) { throw "Expected 40 slides, found $($presentation.Slides.Count)" }
    if (Test-Path $outputFullPath) { Remove-Item $outputFullPath -Force }
    if (Test-Path $pdfPath) { Remove-Item $pdfPath -Force }
    $presentation.SaveAs($outputFullPath, $ppSaveAsOpenXMLPresentation)
    $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
    $presentation.Export($previewFullPath, 'PNG', 1600, 900)
    Write-Output "Created: $outputFullPath"
    Write-Output "Created: $pdfPath"
    Write-Output "Preview: $previewFullPath"
    Write-Output "Slides: $($presentation.Slides.Count)"
}
finally {
    if ($presentation) { $presentation.Close(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null }
    if ($powerPoint) { $powerPoint.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null }
    [gc]::Collect(); [gc]::WaitForPendingFinalizers()
}
