param(
    [string]$StoreName,
    [int]$MaxDepth = 2,
    [switch]$IncludeItemCount,
    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "OutlookCommon.ps1")

$namespace = New-OutlookNamespace
$stores = @($namespace.Stores)

if (-not [string]::IsNullOrWhiteSpace($StoreName)) {
    $stores = @($stores | Where-Object { $_.DisplayName -eq $StoreName })
    if ($stores.Count -eq 0) {
        throw "No Outlook store matched '$StoreName'."
    }
}

$rows = New-Object System.Collections.Generic.List[object]

foreach ($store in $stores) {
    $rootFolder = $store.GetRootFolder()
    foreach ($row in (Get-OutlookFolderInventory -Folder $rootFolder -StoreName $store.DisplayName -Depth 0 -MaxDepth $MaxDepth -IncludeItemCount:$IncludeItemCount)) {
        $rows.Add($row)
    }
}

if ($AsJson) {
    $rows | ConvertTo-Json -Depth 5
}
else {
    $rows |
        Sort-Object Store, FolderPath |
        Format-Table Store, FolderPath, Depth, ItemCount -AutoSize
}
