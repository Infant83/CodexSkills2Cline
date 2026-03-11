param(
    [ValidateSet("Global", "Project")]
    [string]$Scope = "Global",
    [string]$ProjectPath,
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

if ($Scope -eq "Global") {
    $rulesTarget = Join-Path $HOME "Documents\Cline\Rules"
    $workflowsTarget = Join-Path $HOME "Documents\Cline\Workflows"
    $skillsTarget = Join-Path $HOME ".cline\skills"
}
else {
    if (-not $ProjectPath) {
        throw "Project mode requires -ProjectPath."
    }

    $resolvedProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
    $rulesTarget = Join-Path $resolvedProjectPath ".clinerules"
    $workflowsTarget = Join-Path $rulesTarget "workflows"
    $skillsTarget = Join-Path $resolvedProjectPath ".cline\skills"
}

Write-Host "Installing Cline pack"
Write-Host "  Scope: $Scope"
Write-Host "  Rules target: $rulesTarget"
Write-Host "  Workflows target: $workflowsTarget"
Write-Host "  Skills target: $skillsTarget"

Copy-DirectoryContents -Source $rulesSource -Target $rulesTarget
Copy-DirectoryContents -Source $workflowsSource -Target $workflowsTarget
Copy-DirectoryContents -Source $skillsSource -Target $skillsTarget

Write-Host ""
Write-Host "Install complete."
Write-Host "Restart or reload Cline to pick up rules, workflows, and skills."
