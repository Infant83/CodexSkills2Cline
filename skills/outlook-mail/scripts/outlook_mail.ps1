param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$pythonCommand = $null
$pythonArgs = @()

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
    $pythonArgs += "-3"
}
else {
    throw "Python was not found. Install Python and pywin32 first: python -m pip install pywin32"
}

$scriptPath = Join-Path $PSScriptRoot "outlook_mail.py"
& $pythonCommand @pythonArgs $scriptPath @Arguments
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    exit $exitCode
}
