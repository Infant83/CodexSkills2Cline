Set-StrictMode -Version Latest

function New-OutlookNamespace {
    $marshalType = [System.Runtime.InteropServices.Marshal]
    $getActiveObject = $marshalType.GetMethod("GetActiveObject", [Type[]]@([string]))

    if ($null -ne $getActiveObject) {
        try {
            $activeApp = $getActiveObject.Invoke($null, @("Outlook.Application"))
            if ($null -ne $activeApp) {
                return $activeApp.GetNamespace("MAPI")
            }
        }
        catch {
        }
    }

    $app = New-Object -ComObject Outlook.Application
    return $app.GetNamespace("MAPI")
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function ConvertTo-SafeFileName {
    param(
        [AllowNull()]
        [string]$Name,
        [int]$MaxLength = 100
    )

    if ([string]::IsNullOrWhiteSpace($Name)) {
        return "untitled"
    }

    $invalidChars = [System.IO.Path]::GetInvalidFileNameChars()
    $safe = $Name.Trim()

    foreach ($char in $invalidChars) {
        $safe = $safe.Replace([string]$char, "_")
    }

    $safe = [System.Text.RegularExpressions.Regex]::Replace($safe, "\s+", " ").Trim(" ", ".", "_")

    if ([string]::IsNullOrWhiteSpace($safe)) {
        $safe = "untitled"
    }

    if ($safe.Length -gt $MaxLength) {
        $safe = $safe.Substring(0, $MaxLength).Trim(" ", ".", "_")
    }

    if ([string]::IsNullOrWhiteSpace($safe)) {
        return "untitled"
    }

    return $safe
}

function Get-StringHash {
    param(
        [AllowNull()]
        [string]$Value
    )

    $effectiveValue = if ($null -eq $Value) { "" } else { $Value }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($effectiveValue)
    $sha = [System.Security.Cryptography.SHA256]::Create()

    try {
        $hash = $sha.ComputeHash($bytes)
    }
    finally {
        $sha.Dispose()
    }

    return ([BitConverter]::ToString($hash)).Replace("-", "").Substring(0, 12).ToLowerInvariant()
}

function Get-UniqueFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $Path
    }

    $directory = Split-Path -Parent $Path
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    $extension = [System.IO.Path]::GetExtension($Path)
    $index = 1

    while ($true) {
        $candidate = Join-Path $directory ("{0}-{1}{2}" -f $stem, $index, $extension)
        if (-not (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }

        $index += 1
    }
}

function Get-UniqueDirectoryPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $Path
    }

    $parent = Split-Path -Parent $Path
    $leaf = Split-Path -Leaf $Path
    $index = 1

    while ($true) {
        $candidate = Join-Path $parent ("{0}-{1}" -f $leaf, $index)
        if (-not (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }

        $index += 1
    }
}

function Get-MailSenderAddress {
    param(
        [Parameter(Mandatory = $true)]
        [object]$MailItem
    )

    try {
        if ($MailItem.SenderEmailType -eq "EX" -and $null -ne $MailItem.Sender) {
            $exchangeUser = $MailItem.Sender.GetExchangeUser()
            if ($null -ne $exchangeUser -and -not [string]::IsNullOrWhiteSpace($exchangeUser.PrimarySmtpAddress)) {
                return $exchangeUser.PrimarySmtpAddress
            }
        }
    }
    catch {
    }

    if (-not [string]::IsNullOrWhiteSpace($MailItem.SenderEmailAddress)) {
        return $MailItem.SenderEmailAddress
    }

    return $MailItem.SenderName
}

function Get-DefaultFolderMap {
    return @{
        "deleted" = 3
        "deleteditems" = 3
        "drafts" = 16
        "inbox" = 6
        "outbox" = 4
        "sent" = 5
        "sentitems" = 5
        "trash" = 3
        "받은편지함" = 6
        "보낸편지함" = 5
        "삭제된항목" = 3
        "삭제된 항목" = 3
        "임시보관함" = 16
    }
}

function Resolve-OutlookFolder {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Namespace,
        [string]$FolderPath
    )

    if ([string]::IsNullOrWhiteSpace($FolderPath)) {
        return $Namespace.GetDefaultFolder(6)
    }

    $normalized = $FolderPath.Trim().Trim("\", "/")
    $aliasKey = $normalized.ToLowerInvariant()
    $defaultFolderMap = Get-DefaultFolderMap

    if ($defaultFolderMap.ContainsKey($aliasKey)) {
        return $Namespace.GetDefaultFolder($defaultFolderMap[$aliasKey])
    }

    $segments = @($normalized -split "[\\/]+" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($segments.Count -eq 0) {
        return $Namespace.GetDefaultFolder(6)
    }

    $stores = @($Namespace.Stores)
    $store = $stores | Where-Object { $_.DisplayName -eq $segments[0] } | Select-Object -First 1

    if ($null -ne $store) {
        $folder = $store.GetRootFolder()
        $segmentStart = 1
    }
    else {
        $folder = $Namespace.DefaultStore.GetRootFolder()
        $segmentStart = 0
    }

    for ($i = $segmentStart; $i -lt $segments.Count; $i++) {
        $segment = $segments[$i]
        $child = @($folder.Folders) | Where-Object { $_.Name -eq $segment } | Select-Object -First 1

        if ($null -eq $child) {
            throw "Could not resolve Outlook folder path '$FolderPath' at segment '$segment'."
        }

        $folder = $child
    }

    return $folder
}

function Normalize-OutlookFolderPath {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Folder
    )

    return ($Folder.FolderPath -replace "^\\\\", "")
}

function Get-OutlookFolderInventory {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Folder,
        [Parameter(Mandatory = $true)]
        [string]$StoreName,
        [int]$Depth = 0,
        [int]$MaxDepth = 99,
        [switch]$IncludeItemCount
    )

    $rows = New-Object System.Collections.Generic.List[object]

    $itemCount = $null
    if ($IncludeItemCount) {
        try {
            $itemCount = $Folder.Items.Count
        }
        catch {
        }
    }

    $rows.Add([PSCustomObject]@{
            Store = $StoreName
            Name = $Folder.Name
            FolderPath = Normalize-OutlookFolderPath -Folder $Folder
            Depth = $Depth
            ItemCount = $itemCount
        })

    if ($Depth -ge $MaxDepth) {
        return $rows
    }

    foreach ($child in @($Folder.Folders)) {
        foreach ($row in (Get-OutlookFolderInventory -Folder $child -StoreName $StoreName -Depth ($Depth + 1) -MaxDepth $MaxDepth -IncludeItemCount:$IncludeItemCount)) {
            $rows.Add($row)
        }
    }

    return $rows
}

function Get-OutlookFolderDescendants {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Folder
    )

    $rows = New-Object System.Collections.Generic.List[object]
    $rows.Add($Folder)

    foreach ($child in @($Folder.Folders)) {
        foreach ($descendant in (Get-OutlookFolderDescendants -Folder $child)) {
            $rows.Add($descendant)
        }
    }

    return $rows
}

function Test-IsMailItem {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Item
    )

    try {
        if ($Item.Class -ne 43) {
            return $false
        }

        return $Item.MessageClass -like "IPM.Note*"
    }
    catch {
        return $false
    }
}

function Convert-MailToMarkdown {
    param(
        [Parameter(Mandatory = $true)]
        [object]$MailItem,
        [Parameter(Mandatory = $true)]
        [string]$FolderPath,
        [Parameter(Mandatory = $true)]
        [string]$SenderAddress
    )

    $subject = if ([string]::IsNullOrWhiteSpace($MailItem.Subject)) { "(no subject)" } else { $MailItem.Subject.Trim() }
    $received = try { ([datetime]$MailItem.ReceivedTime).ToString("yyyy-MM-dd HH:mm:ss") } catch { "" }
    $bodyText = if ($null -eq $MailItem.Body) { "" } else { [string]$MailItem.Body }

    $lines = @(
        "# $subject",
        "",
        "- Received: $received",
        "- From: $SenderAddress",
        "- To: $($MailItem.To)",
        "- CC: $($MailItem.CC)",
        "- Folder: $FolderPath",
        "- Outlook Entry ID: $($MailItem.EntryID)",
        "",
        "## Body",
        "",
        $bodyText
    )

    return ($lines -join [Environment]::NewLine)
}
