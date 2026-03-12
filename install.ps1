param(
    [ValidateSet("All", "Cline", "DeepAgents")]
    [string]$Target = "All",
    [string]$HomeRoot,
    [string]$DeepAgentsAgentName = "agent",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-HomeRoot {
    if ($HomeRoot) {
        return $HomeRoot
    }

    if ($env:USERPROFILE) {
        return $env:USERPROFILE
    }

    if ($HOME) {
        return $HOME
    }

    throw "Could not resolve the user home directory."
}

function Resolve-PrimaryUsername {
    param([string]$HomePath)

    if ($env:USERNAME) {
        return $env:USERNAME.Trim().ToLowerInvariant()
    }

    $leaf = Split-Path -Path $HomePath -Leaf
    if ($leaf) {
        return $leaf.Trim().ToLowerInvariant()
    }

    return ""
}

function Resolve-OutlookSelfAddress {
    param([string]$HomePath)

    if ($env:OUTLOOK_MAIL_SELF_ADDRESS) {
        return $env:OUTLOOK_MAIL_SELF_ADDRESS.Trim().ToLowerInvariant()
    }

    $username = Resolve-PrimaryUsername -HomePath $HomePath
    if (-not $username) {
        return ""
    }

    return "$username@lgdisplay.com"
}

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

function Copy-FileToTarget {
    param(
        [string]$Source,
        [string]$Target
    )

    Ensure-Directory -Path (Split-Path -Parent $Target)

    if ($DryRun) {
        Write-Host "[dry-run] copy $Source -> $Target"
        return
    }

    Copy-Item -LiteralPath $Source -Destination $Target -Force
}

function Install-ClinePack {
    param(
        [string]$RepoRoot,
        [string]$HomePath,
        [string]$DocumentsPath
    )

    $sourceRoot = Join-Path $RepoRoot "cline"
    $skillsSource = Join-Path $RepoRoot "skills"

    $managedHome = Join-Path $HomePath ".cline"
    $managedRules = Join-Path $managedHome "rules"
    $managedWorkflows = Join-Path $managedHome "workflows"
    $managedSkills = Join-Path $managedHome "skills"

    $runtimeRoot = Join-Path $DocumentsPath "Cline"
    $runtimeRules = Join-Path $runtimeRoot "Rules"
    $runtimeWorkflows = Join-Path $runtimeRoot "Workflows"

    Write-Host "Installing Cline pack"
    Write-Host "  Managed home: $managedHome"
    Write-Host "  Runtime rules: $runtimeRules"
    Write-Host "  Runtime workflows: $runtimeWorkflows"

    Copy-DirectoryContents -Source (Join-Path $sourceRoot "rules") -Target $managedRules
    Copy-DirectoryContents -Source (Join-Path $sourceRoot "workflows") -Target $managedWorkflows
    Copy-DirectoryContents -Source $skillsSource -Target $managedSkills

    Copy-DirectoryContents -Source (Join-Path $sourceRoot "rules") -Target $runtimeRules
    Copy-DirectoryContents -Source (Join-Path $sourceRoot "workflows") -Target $runtimeWorkflows
}

function Install-DeepAgentsPack {
    param(
        [string]$RepoRoot,
        [string]$HomePath,
        [string]$AgentName
    )

    $sourceRoot = Join-Path $RepoRoot "deepagents"
    $skillsSource = Join-Path $RepoRoot "skills"

    $managedHome = Join-Path $HomePath ".deepagents"
    $agentHome = Join-Path $managedHome $AgentName
    $agentSkills = Join-Path $agentHome "skills"

    Write-Host "Installing DeepAgents pack"
    Write-Host "  Managed home: $managedHome"
    Write-Host "  Agent home: $agentHome"

    Copy-FileToTarget -Source (Join-Path $sourceRoot "config.toml") -Target (Join-Path $managedHome "config.toml")
    Copy-FileToTarget -Source (Join-Path $sourceRoot "agent\AGENTS.md") -Target (Join-Path $agentHome "AGENTS.md")
    Copy-DirectoryContents -Source $skillsSource -Target $agentSkills
}

$repoRoot = $PSScriptRoot
$resolvedHome = Resolve-HomeRoot
$documentsRoot = [Environment]::GetFolderPath("MyDocuments")
if (-not $documentsRoot) {
    $documentsRoot = Join-Path $resolvedHome "Documents"
}

if ($Target -in @("All", "Cline")) {
    Install-ClinePack -RepoRoot $repoRoot -HomePath $resolvedHome -DocumentsPath $documentsRoot
}

if ($Target -in @("All", "DeepAgents")) {
    Install-DeepAgentsPack -RepoRoot $repoRoot -HomePath $resolvedHome -AgentName $DeepAgentsAgentName
}

Write-Host ""
Write-Host "Install complete."
Write-Host ""
$outlookSelfAddress = Resolve-OutlookSelfAddress -HomePath $resolvedHome
if ($outlookSelfAddress) {
    Write-Host "Outlook mail default self address: $outlookSelfAddress"
    if ($env:OUTLOOK_MAIL_SELF_ADDRESS) {
        Write-Host "  Source: OUTLOOK_MAIL_SELF_ADDRESS"
    }
    else {
        Write-Host "  Source: current OS username + @lgdisplay.com"
    }
}
else {
    Write-Host "Outlook mail default self address: <not detected>"
}
Write-Host "If this does not match your actual company mailbox address, set OUTLOOK_MAIL_SELF_ADDRESS before using outlook-mail."
Write-Host '  PowerShell example: $env:OUTLOOK_MAIL_SELF_ADDRESS="actual.user@lgdisplay.com"'
Write-Host '  CMD example: set OUTLOOK_MAIL_SELF_ADDRESS=actual.user@lgdisplay.com'
Write-Host "Restart or reload Cline and DeepAgents to pick up the updated files."
