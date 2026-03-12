param(
    [ValidateSet("Global", "Project")]
    [string]$Scope = "Global",
    [ValidateSet("Cline", "DeepAgents")]
    [string]$Target = "Cline",
    [string]$ProjectPath,
    [string]$DeepAgentsHome,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        return
    }

    if ($DryRun) {
        Write-Host "[dry-run] mkdir $Path"
        return
    }

    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Target
    )

    Ensure-Directory -Path $Target

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        $destination = Join-Path $Target $_.Name

        if ($DryRun) {
            Write-Host "[dry-run] copy $($_.FullName) -> $destination"
            return
        }

        Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
    }
}

$sourceRoot = $PSScriptRoot
$rulesSource = Join-Path $sourceRoot "Rules"
$workflowsSource = Join-Path $sourceRoot "Workflows"
$skillsSource = Join-Path $sourceRoot "skills"
$documentsRoot = [Environment]::GetFolderPath("MyDocuments")

if (-not $DeepAgentsHome) {
    $DeepAgentsHome = Join-Path $HOME ".deepagents"
}

if ($Target -eq "Cline") {
    if ($Scope -eq "Global") {
        $rulesTarget = Join-Path (Join-Path $documentsRoot "Cline") "Rules"
        $workflowsTarget = Join-Path (Join-Path $documentsRoot "Cline") "Workflows"
        $skillsTarget = Join-Path (Join-Path $HOME ".cline") "skills"
    }
    else {
        if (-not $ProjectPath) {
            throw "Project mode requires -ProjectPath."
        }

        $resolvedProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
        $rulesTarget = Join-Path $resolvedProjectPath ".clinerules"
        $workflowsTarget = Join-Path $rulesTarget "workflows"
        $skillsTarget = Join-Path (Join-Path $resolvedProjectPath ".cline") "skills"
    }
}
else {
    if ($Scope -eq "Global") {
        $skillsTarget = Join-Path $DeepAgentsHome "skills"
    }
    else {
        if (-not $ProjectPath) {
            throw "Project mode requires -ProjectPath."
        }

        $resolvedProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
        $skillsTarget = Join-Path (Join-Path $resolvedProjectPath ".deepagents") "skills"
    }
}

Write-Host "Installing $Target pack"
Write-Host "  Scope: $Scope"
Write-Host "  Skills target: $skillsTarget"

if ($Target -eq "Cline") {
    Write-Host "  Rules target: $rulesTarget"
    Write-Host "  Workflows target: $workflowsTarget"
    Copy-DirectoryContents -Source $rulesSource -Target $rulesTarget
    Copy-DirectoryContents -Source $workflowsSource -Target $workflowsTarget
}
else {
    Write-Host "  DeepAgents install copies skills only."
}

Copy-DirectoryContents -Source $skillsSource -Target $skillsTarget

Write-Host ""
Write-Host "Install complete."
if ($Target -eq "Cline") {
    Write-Host "Restart or reload Cline to pick up rules, workflows, and skills."
}
else {
    Write-Host "Restart or reload DeepAgents to pick up installed skills."
}
