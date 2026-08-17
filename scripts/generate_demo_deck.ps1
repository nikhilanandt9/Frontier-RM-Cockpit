param(
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\docs\Frontier_RM_Intelligent_System_Demo.pptx'),
    [string]$PreviewDirectory = (Join-Path $PSScriptRoot '..\docs\deck-preview')
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
    Red = 0x2000B0
    RedDark = 0x1A008F
    RedLight = 0xE9E5FF
    Ink = 0x242124
    Charcoal = 0x302B2E
    Muted = 0x6A6469
    Line = 0xE4E1E3
    Canvas = 0xF5F5F5
    White = 0xFFFFFF
    Green = 0x527A14
    GreenLight = 0xEFF5E8
    Amber = 0x005DA6
    AmberLight = 0xD9F2FF
    Blue = 0x995F1F
    BlueLight = 0xFAF1E7
}

function Set-TextStyle {
    param($Range, [double]$Size, [int]$Color, [bool]$Bold = $false, [string]$Font = 'Aptos')
    $Range.Font.Name = $Font
    $Range.Font.Size = $Size
    $Range.Font.Color.RGB = $Color
    $Range.Font.Bold = $(if ($Bold) { $msoTrue } else { $msoFalse })
}

function Add-Text {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [double]$H, [double]$Size = 18, [int]$Color = $colors.Ink, [bool]$Bold = $false, [string]$Font = 'Aptos', [int]$Align = 1)
    $shape = $Slide.Shapes.AddTextbox($msoTextOrientationHorizontal, $X, $Y, $W, $H)
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = $msoTrue
    $shape.TextFrame.TextRange.Text = $Text
    $shape.TextFrame.TextRange.ParagraphFormat.Alignment = $Align
    Set-TextStyle $shape.TextFrame.TextRange $Size $Color $Bold $Font
    return $shape
}

function Add-Box {
    param($Slide, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Fill = $colors.White, [int]$Line = $colors.Line, [double]$Radius = 0)
    $type = $(if ($Radius -gt 0) { $msoShapeRoundedRectangle } else { $msoShapeRectangle })
    $shape = $Slide.Shapes.AddShape($type, $X, $Y, $W, $H)
    $shape.Fill.ForeColor.RGB = $Fill
    $shape.Line.ForeColor.RGB = $Line
    $shape.Line.Weight = 1
    return $shape
}

function Add-Pill {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [int]$Fill = $colors.Red, [int]$TextColor = $colors.White)
    $box = Add-Box $Slide $X $Y $W 24 $Fill $Fill 6
    $null = Add-Text $Slide $Text ($X + 7) ($Y + 5) ($W - 14) 14 8 $TextColor $true 'Aptos' 2
    return $box
}

function Add-Title {
    param($Slide, [string]$Eyebrow, [string]$Title, [string]$Subtitle = '')
    $null = Add-Text $Slide $Eyebrow 54 34 850 18 9 $colors.Red $true 'Aptos'
    $null = Add-Text $Slide $Title 54 58 850 58 28 $colors.Ink $true 'Aptos Display'
    if ($Subtitle) { $null = Add-Text $Slide $Subtitle 54 116 850 38 12 $colors.Muted $false 'Aptos' }
}

function Add-Footer {
    param($Slide, [int]$Number, [string]$Label = 'FRONTIER RM · INTERNAL EBC DEMO')
    $line = $Slide.Shapes.AddLine(54, 510, 906, 510)
    $line.Line.ForeColor.RGB = $colors.Line
    $null = Add-Text $Slide $Label 54 517 500 12 7 $colors.Muted $true 'Aptos'
    $null = Add-Text $Slide ([string]$Number) 870 517 36 12 8 $colors.Muted $true 'Aptos' 3
}

function Add-Notes {
    param($Slide, [string]$Notes)
    try {
        $placeholders = $Slide.NotesPage.Shapes.Placeholders()
        for ($index = 1; $index -le $placeholders.Count; $index++) {
            $placeholder = $placeholders.Item($index)
            if ($placeholder.PlaceholderFormat.Type -eq 2) {
                $placeholder.TextFrame.TextRange.Text = $Notes
                return
            }
        }
    } catch {
        Write-Warning "Could not add speaker notes to slide $($Slide.SlideIndex): $($_.Exception.Message)"
    }
}

function Add-BulletList {
    param($Slide, [string[]]$Items, [double]$X, [double]$Y, [double]$W, [double]$H, [double]$Size = 15, [int]$Color = $colors.Ink)
    $text = ($Items | ForEach-Object { "• $_" }) -join "`r"
    $shape = Add-Text $Slide $text $X $Y $W $H $Size $Color $false 'Aptos'
    $shape.TextFrame.TextRange.ParagraphFormat.SpaceAfter = 8
    return $shape
}

function Add-ScreenshotPlaceholder {
    param($Slide, [string]$System, [string]$Instruction, [double]$X = 54, [double]$Y = 155, [double]$W = 852, [double]$H = 315, [string]$Callout = '')
    $box = Add-Box $Slide $X $Y $W $H $colors.White $colors.Muted 6
    $box.Line.DashStyle = $msoLineDash
    $box.Line.Weight = 1.5
    $null = Add-Pill $Slide "SCREENSHOT PLACEHOLDER · $System" ($X + 22) ($Y + 22) 210 $colors.Charcoal $colors.White
    $icon = $Slide.Shapes.AddShape($msoShapeRectangle, ($X + $W / 2 - 27), ($Y + 82), 54, 42)
    $icon.Fill.ForeColor.RGB = $colors.Canvas
    $icon.Line.ForeColor.RGB = $colors.Line
    $null = Add-Text $Slide '▧' ($X + $W / 2 - 20) ($Y + 88) 40 25 22 $colors.Red $true 'Segoe UI Symbol' 2
    $null = Add-Text $Slide $Instruction ($X + 85) ($Y + 145) ($W - 170) 55 16 $colors.Ink $true 'Aptos' 2
    $null = Add-Text $Slide 'Replace this grouped placeholder with your screenshot. Keep the title and callout visible.' ($X + 120) ($Y + 207) ($W - 240) 36 10 $colors.Muted $false 'Aptos' 2
    if ($Callout) {
        $calloutBox = Add-Box $Slide ($X + 35) ($Y + $H - 52) ($W - 70) 33 $colors.RedLight $colors.RedLight 4
        $null = Add-Text $Slide $Callout ($X + 48) ($Y + $H - 43) ($W - 96) 16 9 $colors.RedDark $true 'Aptos' 2
    }
}

function Add-Card {
    param($Slide, [string]$Number, [string]$Title, [string]$Body, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Accent = $colors.Red)
    $null = Add-Box $Slide $X $Y $W $H $colors.White $colors.Line 4
    $null = Add-Text $Slide $Number ($X + 16) ($Y + 15) 45 28 18 $Accent $true 'Aptos Display'
    $null = Add-Text $Slide $Title ($X + 16) ($Y + 49) ($W - 32) 38 15 $colors.Ink $true 'Aptos Display'
    $null = Add-Text $Slide $Body ($X + 16) ($Y + 93) ($W - 32) ($H - 106) 10 $colors.Muted $false 'Aptos'
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$previewFullPath = [System.IO.Path]::GetFullPath($PreviewDirectory)
$outputDirectory = Split-Path $outputFullPath -Parent
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
if (Test-Path $previewFullPath) { Remove-Item $previewFullPath -Recurse -Force }
New-Item -ItemType Directory -Path $previewFullPath -Force | Out-Null

$powerPoint = New-Object -ComObject PowerPoint.Application
$powerPoint.Visible = $msoTrue
$presentation = $powerPoint.Presentations.Add()
$presentation.PageSetup.SlideWidth = 960
$presentation.PageSetup.SlideHeight = 540

try {
    # 1. Title
    $slide = $presentation.Slides.Add(1, $ppLayoutBlank)
    $background = Add-Box $slide 0 0 960 540 $colors.Charcoal $colors.Charcoal
    $gridColor = 0x4A4448
    for ($x = 0; $x -le 960; $x += 48) { $line = $slide.Shapes.AddLine($x, 0, $x, 540); $line.Line.ForeColor.RGB = $gridColor; $line.Line.Transparency = 0.65 }
    for ($y = 0; $y -le 540; $y += 48) { $line = $slide.Shapes.AddLine(0, $y, 960, $y); $line.Line.ForeColor.RGB = $gridColor; $line.Line.Transparency = 0.65 }
    $bar = Add-Box $slide 0 0 8 540 $colors.Red $colors.Red
    $null = Add-Pill $slide 'EXECUTIVE BRIEFING CENTRE' 62 58 184 $colors.Red $colors.White
    $null = Add-Text $slide 'What would a day in the life of a Relationship Manager look like…' 62 125 810 98 34 $colors.White $true 'Aptos Display'
    $null = Add-Text $slide '…if bank data, knowledge, applications and AI capabilities worked together as one intelligent system?' 62 238 780 92 24 0x8871FF $true 'Aptos Display'
    $null = Add-Text $slide 'FRONTIER RM' 62 406 200 22 12 $colors.White $true 'Aptos'
    $null = Add-Text $slide 'A governed, human-controlled relationship workspace' 62 435 500 25 13 0xC9C2C6 $false 'Aptos'
    Add-Notes $slide "Open with the question on screen. Pause after 'one intelligent system.' Explain that this is a day-in-the-life story, not a technology tour."

    # 2. The fragmented day
    $slide = $presentation.Slides.Add(2, $ppLayoutBlank)
    Add-Title $slide 'THE CURRENT REALITY' 'The RM spends the day assembling context' 'Signals exist across systems, but the work of connecting them still falls to the relationship manager.'
    Add-Card $slide '01' 'Find the client context' 'Search accounts, holdings, profile, consent and previous interactions.' 54 175 195 235 $colors.Red
    Add-Card $slide '02' 'Interpret the need' 'Connect lifecycle events, objectives, liquidity, risk and market context.' 268 175 195 235 $colors.Amber
    Add-Card $slide '03' 'Prepare the conversation' 'Read correspondence, find guidance and assemble a client-specific talk track.' 482 175 195 235 $colors.Blue
    Add-Card $slide '04' 'Record the follow-up' 'Draft the email, create the CRM record and preserve the evidence trail.' 696 175 195 235 $colors.Green
    $null = Add-Text $slide 'The opportunity is not another assistant. It is an intelligent operating layer around the RM.' 95 442 770 28 15 $colors.RedDark $true 'Aptos' 2
    Add-Footer $slide 2
    Add-Notes $slide "Describe the swivel-chair problem. Avoid naming specific legacy systems. Transition: 'What if the context arrived already understood?'"

    # 3. North star
    $slide = $presentation.Slides.Add(3, $ppLayoutBlank)
    Add-Title $slide 'THE NORTH STAR' 'One governed system around the RM' 'Data and AI do the synthesis. The RM owns the judgment, suitability decision and client relationship.'
    $labels = @(
        @{ T='DATA'; S='Fabric · client facts · lifecycle events'; C=$colors.Blue },
        @{ T='KNOWLEDGE'; S='Policy · product guidance · source boundaries'; C=$colors.Amber },
        @{ T='APPLICATIONS'; S='Outlook-style sources · CRM drafts · Teams'; C=$colors.Green },
        @{ T='AI'; S='Orchestration · generation · verification'; C=$colors.Red }
    )
    for ($i = 0; $i -lt $labels.Count; $i++) {
        $x = 68 + ($i * 206)
        $circle = $slide.Shapes.AddShape($msoShapeOval, $x, 185, 142, 142)
        $circle.Fill.ForeColor.RGB = $labels[$i].C
        $circle.Line.Visible = $msoFalse
        $null = Add-Text $slide $labels[$i].T ($x + 15) 220 112 22 12 $colors.White $true 'Aptos' 2
        $null = Add-Text $slide $labels[$i].S ($x + 12) 252 118 42 8 $colors.White $false 'Aptos' 2
        if ($i -lt 3) { $null = Add-Text $slide '+' ($x + 157) 230 25 25 18 $colors.Muted $true 'Aptos' 2 }
    }
    $null = Add-Box $slide 239 365 482 67 $colors.Charcoal $colors.Charcoal 5
    $null = Add-Text $slide 'RELATIONSHIP MANAGER' 278 379 404 19 14 $colors.White $true 'Aptos' 2
    $null = Add-Text $slide 'Evidence visible · Human judgment in control' 278 405 404 16 10 0xC9C2C6 $false 'Aptos' 2
    Add-Footer $slide 3
    Add-Notes $slide "Use this as the architecture promise in business language. Stress that AI does not replace the RM or remove mandatory checks."

    # 4. Day timeline
    $slide = $presentation.Slides.Add(4, $ppLayoutBlank)
    Add-Title $slide 'A DAY IN MOTION' 'From morning signal to governed follow-up' 'The experience follows relationship-manager work, not the underlying product boundaries.'
    $stages = @(
        @{ Time='08:30'; T='TRIAGE'; B='Priorities and reviews'; C=$colors.Red },
        @{ Time='09:15'; T='UNDERSTAND'; B='Client 360 + sources'; C=$colors.Blue },
        @{ Time='10:00'; T='PREPARE'; B='Meeting briefing'; C=$colors.Amber },
        @{ Time='11:30'; T='DECIDE'; B='Custom recommendations'; C=$colors.Green },
        @{ Time='12:15'; T='FOLLOW UP'; B='Email + CRM draft'; C=$colors.RedDark }
    )
    $timeline = $slide.Shapes.AddLine(105, 278, 855, 278); $timeline.Line.ForeColor.RGB = $colors.Line; $timeline.Line.Weight = 4
    for ($i = 0; $i -lt $stages.Count; $i++) {
        $x = 90 + ($i * 187)
        $circle = $slide.Shapes.AddShape($msoShapeOval, $x, 256, 44, 44)
        $circle.Fill.ForeColor.RGB = $stages[$i].C; $circle.Line.Visible = $msoFalse
        $null = Add-Text $slide ([string]($i + 1)) ($x + 8) 267 28 15 10 $colors.White $true 'Aptos' 2
        $null = Add-Text $slide $stages[$i].Time ($x - 4) 205 52 20 11 $colors.Muted $true 'Aptos' 2
        $null = Add-Text $slide $stages[$i].T ($x - 45) 322 135 18 10 $stages[$i].C $true 'Aptos' 2
        $null = Add-Text $slide $stages[$i].B ($x - 48) 346 140 32 10 $colors.Ink $false 'Aptos' 2
    }
    $null = Add-Text $slide 'John remains accountable at every transition.' 250 430 460 24 15 $colors.RedDark $true 'Aptos' 2
    Add-Footer $slide 4
    Add-Notes $slide "Preview the live demo route. Tell the audience you will use Daniel Lim as the primary client and return to Operations at the end."

    # 5. Live demo guide
    $slide = $presentation.Slides.Add(5, $ppLayoutBlank)
    Add-Title $slide 'LIVE DEMO' 'What you are about to see' 'A simple route through the cockpit, with the slide deck used only for context and architecture.'
    $route = @('Today', 'Client 360', 'Sources', 'Briefing', 'Recommendations', 'Drafts', 'Operations')
    for ($i = 0; $i -lt $route.Count; $i++) {
        $x = 52 + ($i * 127)
        $null = Add-Box $slide $x 205 111 84 $(if ($i -eq 0) { $colors.Red } else { $colors.White }) $(if ($i -eq 0) { $colors.Red } else { $colors.Line }) 4
        $null = Add-Text $slide ([string]($i + 1)).PadLeft(2,'0') ($x + 10) 216 30 15 9 $(if ($i -eq 0) { $colors.White } else { $colors.Red }) $true 'Aptos'
        $null = Add-Text $slide $route[$i] ($x + 10) 245 91 25 10 $(if ($i -eq 0) { $colors.White } else { $colors.Ink }) $true 'Aptos' 2
        if ($i -lt $route.Count - 1) { $null = Add-Text $slide '→' ($x + 112) 235 15 20 12 $colors.Muted $true 'Aptos' 2 }
    }
    $null = Add-Box $slide 120 345 720 77 $colors.RedLight $colors.RedLight 5
    $null = Add-Text $slide 'DEMO PRINCIPLE' 145 362 130 15 9 $colors.Red $true 'Aptos'
    $null = Add-Text $slide 'Prepared, not automated. Explained, not opaque. Drafted, not executed.' 275 358 525 35 16 $colors.RedDark $true 'Aptos'
    Add-Footer $slide 5
    Add-Notes $slide "Switch from the deck to the live cockpit after this slide. Use the narration script for the detailed click path. Return to the deck for the architecture placeholders if helpful."

    # 6. Three stages
    $slide = $presentation.Slides.Add(6, $ppLayoutBlank)
    Add-Title $slide 'THE RM JOURNEY' 'Three artifacts, one governed progression' 'Each stage produces something the RM can inspect, challenge and improve.'
    Add-Card $slide '01' 'Prepare briefing' 'Pre-meeting objective, client context, what changed, talk track, questions, sources and mandatory checks.' 70 185 250 236 $colors.Red
    Add-Card $slide '02' 'Custom recommendations' 'Explicitly fictional product candidates, fit rationale, risks, alternatives, evidence and suitability gates.' 355 185 250 236 $colors.Blue
    Add-Card $slide '03' 'Opportunity draft' 'Editable client email and CRM opportunity record. Nothing is sent or committed.' 640 185 250 236 $colors.Green
    $null = Add-Text $slide 'WHY THIS?' 75 452 90 16 9 $colors.Red $true 'Aptos'
    $null = Add-Text $slide 'Every artifact carries evidence, public decision rules, alternatives, assumptions, limitations and unresolved checks.' 170 447 710 30 12 $colors.Ink $false 'Aptos'
    Add-Footer $slide 6
    Add-Notes $slide "Use this slide if the audience asks what AI actually produces. Explain that later stages are deliberately locked until prior artifacts exist."

    # 7. Fabric placeholder
    $slide = $presentation.Slides.Add(7, $ppLayoutBlank)
    Add-Title $slide 'DATA FOUNDATION' 'Microsoft Fabric: governed client evidence' 'Structured customer, portfolio, opportunity, compliance and event context is prepared through a medallion architecture.'
    Add-ScreenshotPlaceholder $slide 'MICROSOFT FABRIC' 'Insert the Frontier-RM-EBC workspace or Lakehouse / medallion screenshot.' 54 160 852 314 'Suggested callout: 20 fictional clients · Bronze / Silver / Gold · schema-enabled Lakehouse'
    Add-Footer $slide 7
    Add-Notes $slide "Screenshot options: Fabric workspace item list, Lakehouse tables, or medallion notebook. State that the web cockpit serves a validated checked-in snapshot rather than querying Fabric on every page load."

    # 8. Semantic model / Power BI placeholder
    $slide = $presentation.Slides.Add(8, $ppLayoutBlank)
    Add-Title $slide 'BUSINESS MEANING' 'Semantic Model and Power BI: a trusted analytical contract' 'Direct Lake measures and relationships turn platform data into RM-ready business concepts.'
    Add-ScreenshotPlaceholder $slide 'POWER BI · SEMANTIC MODEL' 'Insert the model diagram, DAX validation, or Power BI report screenshot.' 54 160 852 314 'Suggested callout: 7 tables · 8 measures · Direct Lake · DAX-validated monetary evidence'
    Add-Footer $slide 8
    Add-Notes $slide "Explain that direct DAX is authoritative for monetary values and hidden identifiers. Avoid claiming that all cockpit metrics are live report visuals."

    # 9. Ontology placeholder
    $slide = $presentation.Slides.Add(9, $ppLayoutBlank)
    Add-Title $slide 'CONNECTED KNOWLEDGE' 'Fabric IQ Ontology: relationships become traversable' 'The ontology expresses customers, households, accounts, holdings, products, events and opportunities as a connected business graph.'
    Add-ScreenshotPlaceholder $slide 'FABRIC IQ ONTOLOGY' 'Insert the Ontology entity/relationship graph or definition view.' 54 160 852 314 'Suggested callout: 11 entities · 11 relationships · 11 bindings · graph routing deferred pending readiness'
    Add-Footer $slide 9
    Add-Notes $slide "Be explicit: the ontology definition is deployed and validated, but detailed graph routing is currently disabled because the generated graph model is not query-ready."

    # 10. Sources / Copilot placeholder
    $slide = $presentation.Slides.Add(10, $ppLayoutBlank)
    Add-Title $slide 'UNSTRUCTURED CONTEXT' 'Sources and Copilot: client voice meets approved knowledge' 'Correspondence and documents add intent and history; Copilot keeps process knowledge available across the workflow.'
    Add-ScreenshotPlaceholder $slide 'SOURCES · COPILOT' 'Insert a split screenshot of the Daniel Lim source thread and the persistent Frontier Copilot panel.' 54 160 852 314 'Suggested callout: realistic authored Outlook / SharePoint-style context · no Microsoft 365 connection'
    Add-Footer $slide 10
    Add-Notes $slide "Say 'authored fictional Outlook-style correspondence' and 'SharePoint-style document.' Do not imply Graph, mailbox or tenant connectivity."

    # 11. Foundry placeholder
    $slide = $presentation.Slides.Add(11, $ppLayoutBlank)
    Add-Title $slide 'AGENTIC COLLABORATION' 'Microsoft Foundry: specialists with bounded responsibilities' 'The orchestrator coordinates customer intelligence, market context and meeting preparation, then verifies evidence coverage.'
    Add-ScreenshotPlaceholder $slide 'MICROSOFT FOUNDRY' 'Insert the Foundry project, agent versions, or Fabric project connection screenshot.' 54 160 852 314 'Suggested callout: Orchestrator v2 · Customer Intelligence v3 · Market Context v2 · Meeting Preparation v2'
    Add-Footer $slide 11
    Add-Notes $slide "Explain OBO/delegated access for the Fabric Data Agent. Customer Intelligence is the only Foundry agent with the Fabric tool attached."

    # 12. Operations placeholder
    $slide = $presentation.Slides.Add(12, $ppLayoutBlank)
    Add-Title $slide 'TRANSPARENCY' 'Operations: evidence, handoffs and verification are observable' 'Presenters can inspect verified, revision-requested and rehearsal captures without exposing private model reasoning.'
    Add-ScreenshotPlaceholder $slide 'OPERATIONS · AGENT REPLAY' 'Insert the agent fleet, captured-run selector and event stream screenshot.' 54 160 852 314 'Suggested callout: captured-live replay ≠ continuous execution · synthetic signal telemetry is separate'
    Add-Footer $slide 12
    Add-Notes $slide "Use the revision-requested run to show that withheld consent evidence changes the verifier outcome. Distinguish service health, synthetic telemetry and captured replay."

    # 13. Architecture
    $slide = $presentation.Slides.Add(13, $ppLayoutBlank)
    Add-Title $slide 'REFERENCE ARCHITECTURE' 'One intelligent system, clear evidence boundaries' 'The value comes from coordinated contracts, not from collapsing every component into one model.'
    $nodes = @(
        @{ X=55; T='Sources'; S='Authored email + documents'; C=$colors.Amber },
        @{ X=235; T='Fabric'; S='Lakehouse + Semantic Model'; C=$colors.Blue },
        @{ X=415; T='Data Agent'; S='Governed retrieval'; C=$colors.Green },
        @{ X=595; T='Foundry'; S='Specialists + verifier'; C=$colors.Red },
        @{ X=775; T='RM Cockpit'; S='Artifacts + approval'; C=$colors.Charcoal }
    )
    foreach ($node in $nodes) {
        $null = Add-Box $slide $node.X 225 135 105 $colors.White $node.C 4
        $null = Add-Box $slide $node.X 225 7 105 $node.C $node.C
        $null = Add-Text $slide $node.T ($node.X + 17) 245 102 22 13 $colors.Ink $true 'Aptos Display' 2
        $null = Add-Text $slide $node.S ($node.X + 12) 277 112 35 9 $colors.Muted $false 'Aptos' 2
    }
    for ($i = 0; $i -lt 4; $i++) { $null = Add-Text $slide '→' (198 + $i * 180) 261 25 20 16 $colors.Muted $true 'Aptos' 2 }
    $null = Add-Box $slide 180 385 600 57 $colors.RedLight $colors.RedLight 4
    $null = Add-Text $slide 'Managed identity · Delegated access · Source IDs · Direct DAX validation · Human review' 205 404 550 17 11 $colors.RedDark $true 'Aptos' 2
    Add-Footer $slide 13
    Add-Notes $slide "Walk left to right. Explain that authored M365-style sources are demonstration context, Fabric is governed data, and the cockpit does not expose private chain-of-thought."

    # 14. Guardrails
    $slide = $presentation.Slides.Add(14, $ppLayoutBlank)
    Add-Title $slide 'GOVERNANCE BY DESIGN' 'What the intelligent system will not do' 'Boundaries are part of the product experience, not a disclaimer added at the end.'
    $guardrails = @(
        @{ T='No hidden reasoning'; B='Expose evidence and concise rationale, never private chain-of-thought.'; C=$colors.Red },
        @{ T='No unsupported facts'; B='Fail closed when governed client evidence is missing.'; C=$colors.Blue },
        @{ T='No suitability shortcut'; B='KYC, consent, objectives, liquidity, horizon and risk remain gates.'; C=$colors.Amber },
        @{ T='No autonomous execution'; B='Drafted, not sent. Prepared for CRM, not committed.'; C=$colors.Green }
    )
    for ($i = 0; $i -lt $guardrails.Count; $i++) {
        $x = 60 + (($i % 2) * 435); $y = 175 + ([math]::Floor($i / 2) * 135)
        $null = Add-Box $slide $x $y 405 110 $colors.White $colors.Line 4
        $null = Add-Box $slide $x $y 7 110 $guardrails[$i].C $guardrails[$i].C
        $null = Add-Text $slide $guardrails[$i].T ($x + 24) ($y + 20) 350 24 15 $colors.Ink $true 'Aptos Display'
        $null = Add-Text $slide $guardrails[$i].B ($x + 24) ($y + 53) 350 42 10 $colors.Muted $false 'Aptos'
    }
    Add-Footer $slide 14
    Add-Notes $slide "Use this slide to answer risk and compliance questions. The demo uses fictional clients and products, but the controls represent real design principles."

    # 15. Outcome
    $slide = $presentation.Slides.Add(15, $ppLayoutBlank)
    Add-Title $slide 'THE SHIFT' 'From application navigation to client judgment' 'The system returns time and attention to the work only the RM can do.'
    $null = Add-Text $slide 'BEFORE' 90 188 170 22 11 $colors.Muted $true 'Aptos' 2
    $null = Add-BulletList $slide @('Search for context','Reconcile conflicting signals','Draft from a blank page','Document provenance manually') 80 225 250 155 14 $colors.Ink
    $arrow = $slide.Shapes.AddShape($msoShapeChevron, 417, 245, 125, 90)
    $arrow.Fill.ForeColor.RGB = $colors.Red; $arrow.Line.Visible = $msoFalse
    $null = Add-Text $slide 'WITH FRONTIER RM' 650 188 210 22 11 $colors.Red $true 'Aptos' 2
    $null = Add-BulletList $slide @('Priorities already sequenced','Evidence already connected','Artifacts already prepared','Judgment remains with John') 620 225 270 155 14 $colors.Ink
    $null = Add-Box $slide 170 414 620 55 $colors.Charcoal $colors.Charcoal 4
    $null = Add-Text $slide 'More time for trust, advice and the client relationship.' 205 432 550 20 16 $colors.White $true 'Aptos' 2
    Add-Footer $slide 15
    Add-Notes $slide "Bring the discussion back to the RM and client outcome. Avoid claiming measured productivity benefits unless separately validated."

    # 16. Houseview supplement
    $slide = $presentation.Slides.Add(16, $ppLayoutBlank)
    Add-Title $slide 'SECONDARY STORYLINE' 'CIO Houseview: market outlook meets client evidence and controls' 'Show how declared profile, observed activity, full research reports and paragraph-cited controls shape retained and suppressed candidates.'
    Add-ScreenshotPlaceholder $slide 'CIO HOUSEVIEW · ADVISORY CONTEXT' 'Insert the Houseview report reader with the selected-client risk, activity, candidates and regulatory controls panel.' 54 160 852 314 'Suggested callout: declared profile ≠ observed behaviour · activity triggers review · compliance-aware, not certified compliant'
    Add-Footer $slide 16
    Add-Notes $slide "Use Daniel to show a fictional equity sale moving observed behaviour from 3 to 2 while declared profile remains 3. Use Mei to show retirement enhanced review and complex-candidate suppression. Never say MAS automatically assigns retirees score 1 or universally bans derivatives."

    # 17. Close
    $slide = $presentation.Slides.Add(17, $ppLayoutBlank)
    $null = Add-Box $slide 0 0 960 540 $colors.Charcoal $colors.Charcoal
    $null = Add-Text $slide 'THE QUESTION WE STARTED WITH' 62 70 500 18 9 0xB8B0B4 $true 'Aptos'
    $null = Add-Text $slide 'What would a day in the life of a Relationship Manager look like…' 62 120 810 80 30 $colors.White $true 'Aptos Display'
    $null = Add-Text $slide '…if the bank worked as one intelligent system?' 62 220 760 56 25 0x8871FF $true 'Aptos Display'
    $null = Add-Box $slide 62 338 820 2 $colors.Red $colors.Red
    $null = Add-Text $slide 'It looks like evidence arriving before the question, artifacts arriving before the blank page, and human judgment remaining in control.' 62 372 800 72 18 $colors.White $false 'Aptos'
    $null = Add-Text $slide 'FRONTIER RM · DATA + KNOWLEDGE + APPLICATIONS + AI' 62 475 650 16 9 0xB8B0B4 $true 'Aptos'
    Add-Notes $slide "Close by restating the answer in business terms. Invite discussion on which RM journeys and evidence sources should be prioritized next."

    if (Test-Path $outputFullPath) { Remove-Item $outputFullPath -Force }
    $presentation.SaveAs($outputFullPath, $ppSaveAsOpenXMLPresentation)
    $pdfPath = [System.IO.Path]::ChangeExtension($outputFullPath, '.pdf')
    if (Test-Path $pdfPath) { Remove-Item $pdfPath -Force }
    $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
    $presentation.Export($previewFullPath, 'PNG', 1600, 900)
    Write-Output "Created: $outputFullPath"
    Write-Output "Created: $pdfPath"
    Write-Output "Preview: $previewFullPath"
    Write-Output "Slides: $($presentation.Slides.Count)"
}
finally {
    if ($presentation) { $presentation.Close() }
    if ($powerPoint) { $powerPoint.Quit() }
    if ($presentation) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) | Out-Null }
    if ($powerPoint) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}