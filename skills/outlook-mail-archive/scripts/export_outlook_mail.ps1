[CmdletBinding()]
param(
    [string]$FolderPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [datetime]$ReceivedSince,
    [datetime]$ReceivedUntil,
    [switch]$UnreadOnly,
    [switch]$IncludeSubfolders,
    [string]$SenderContains,
    [string]$SubjectContains,
    [ValidateSet("Markdown", "Text")]
    [string]$BodyFormat = "Markdown",
    [int]$MaxItems = 100,
    [bool]$SaveAttachments = $true,
    [bool]$SaveMsg = $true,
    [switch]$SkipExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "OutlookCommon.ps1")

Ensure-Directory -Path $OutputRoot

$namespace = New-OutlookNamespace
$rootFolder = Resolve-OutlookFolder -Namespace $namespace -FolderPath $FolderPath
$targetFolders = if ($IncludeSubfolders) {
    @(Get-OutlookFolderDescendants -Folder $rootFolder)
}
else {
    @($rootFolder)
}

$manifestRows = New-Object System.Collections.Generic.List[object]
$runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$manifestPath = Join-Path $OutputRoot "manifest-$runStamp.csv"

$scanned = 0
$exported = 0
$skipped = 0

if ($MaxItems -le 0) {
    [PSCustomObject]@{
        Folder = Normalize-OutlookFolderPath -Folder $rootFolder
        OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
        Scanned = 0
        Exported = 0
        Skipped = 0
        Manifest = $null
    }
    return
}

foreach ($folder in $targetFolders) {
    $folderPathValue = Normalize-OutlookFolderPath -Folder $folder
    $items = @($folder.Items)

    foreach ($item in $items) {
        if ($exported -ge $MaxItems) {
            break
        }

        $scanned += 1

        if (-not (Test-IsMailItem -Item $item)) {
            continue
        }

        $receivedTime = try { [datetime]$item.ReceivedTime } catch { $null }
        if ($null -eq $receivedTime) {
            continue
        }

        if ($PSBoundParameters.ContainsKey("ReceivedSince") -and $receivedTime -lt $ReceivedSince) {
            continue
        }

        if ($PSBoundParameters.ContainsKey("ReceivedUntil") -and $receivedTime -gt $ReceivedUntil) {
            continue
        }

        if ($UnreadOnly -and -not $item.UnRead) {
            continue
        }

        $subject = if ([string]::IsNullOrWhiteSpace($item.Subject)) { "(no subject)" } else { $item.Subject.Trim() }

        if (-not [string]::IsNullOrWhiteSpace($SubjectContains) -and $subject.IndexOf($SubjectContains, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
            continue
        }

        $senderAddress = Get-MailSenderAddress -MailItem $item
        $senderAddressValue = if ($null -eq $senderAddress) { "" } else { [string]$senderAddress }
        if (-not [string]::IsNullOrWhiteSpace($SenderContains) -and $senderAddressValue.IndexOf($SenderContains, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
            continue
        }

        $messageHashSource = if ($null -ne $item.EntryID -and -not [string]::IsNullOrWhiteSpace([string]$item.EntryID)) {
            [string]$item.EntryID
        }
        else {
            "$receivedTime|$subject|$senderAddressValue"
        }

        $messageHash = Get-StringHash -Value $messageHashSource
        $dateDirectory = Join-Path (Join-Path (Join-Path $OutputRoot $receivedTime.ToString("yyyy")) $receivedTime.ToString("MM")) $receivedTime.ToString("dd")
        Ensure-Directory -Path $dateDirectory

        $messageFolderName = ConvertTo-SafeFileName -Name ("{0}_{1}_{2}" -f $receivedTime.ToString("yyyyMMdd-HHmmss"), $subject, $messageHash) -MaxLength 120
        $messageDirectory = Join-Path $dateDirectory $messageFolderName

        if (Test-Path -LiteralPath $messageDirectory) {
            if ($SkipExisting) {
                $skipped += 1
                continue
            }

            $messageDirectory = Get-UniqueDirectoryPath -Path $messageDirectory
        }

        Ensure-Directory -Path $messageDirectory

        $bodyFileName = if ($BodyFormat -eq "Markdown") { "message.md" } else { "message.txt" }
        $bodyPath = Join-Path $messageDirectory $bodyFileName

        if ($BodyFormat -eq "Markdown") {
            $bodyContent = Convert-MailToMarkdown -MailItem $item -FolderPath $folderPathValue -SenderAddress $senderAddress
        }
        else {
            $bodyContent = $item.Body
        }

        Set-Content -LiteralPath $bodyPath -Value $bodyContent -Encoding UTF8

        $msgPath = $null
        if ($SaveMsg) {
            $msgPath = Join-Path $messageDirectory "original.msg"
            $msgPath = Get-UniqueFilePath -Path $msgPath
            $item.SaveAs($msgPath, 9)
        }

        $savedAttachments = New-Object System.Collections.Generic.List[string]
        if ($SaveAttachments -and $item.Attachments.Count -gt 0) {
            $attachmentsDirectory = Join-Path $messageDirectory "attachments"
            Ensure-Directory -Path $attachmentsDirectory

            for ($index = 1; $index -le $item.Attachments.Count; $index++) {
                $attachment = $item.Attachments.Item($index)
                $attachmentName = ConvertTo-SafeFileName -Name $attachment.FileName
                if ([string]::IsNullOrWhiteSpace($attachmentName)) {
                    $attachmentName = "attachment-$index.bin"
                }

                $attachmentPath = Get-UniqueFilePath -Path (Join-Path $attachmentsDirectory $attachmentName)
                $attachment.SaveAsFile($attachmentPath)
                $savedAttachments.Add($attachmentPath)
            }
        }

        $metadata = [ordered]@{
            subject = $subject
            sender = $senderAddress
            to = $item.To
            cc = $item.CC
            received_time = $receivedTime.ToString("o")
            folder_path = $folderPathValue
            entry_id = $item.EntryID
            hash = $messageHash
            unread = [bool]$item.UnRead
            importance = $item.Importance
            body_path = $bodyPath
            msg_path = $msgPath
            attachment_count = $savedAttachments.Count
            attachments = @($savedAttachments)
        }

        $metadataPath = Join-Path $messageDirectory "metadata.json"
        $metadata | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $metadataPath -Encoding UTF8

        $manifestRows.Add([PSCustomObject]@{
                ReceivedTime = $receivedTime.ToString("s")
                Subject = $subject
                Sender = $senderAddress
                FolderPath = $folderPathValue
                MessageDirectory = $messageDirectory
                BodyPath = $bodyPath
                MsgPath = $msgPath
                AttachmentCount = $savedAttachments.Count
                Hash = $messageHash
            })

        $exported += 1
    }

    if ($exported -ge $MaxItems) {
        break
    }
}

if ($manifestRows.Count -gt 0) {
    $manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8
}
else {
    $manifestPath = $null
}

[PSCustomObject]@{
    Folder = Normalize-OutlookFolderPath -Folder $rootFolder
    OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
    Scanned = $scanned
    Exported = $exported
    Skipped = $skipped
    Manifest = $manifestPath
}
