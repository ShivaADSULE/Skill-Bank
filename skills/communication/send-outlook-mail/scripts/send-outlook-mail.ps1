<#
.SYNOPSIS
    Sends an email via the locally installed Microsoft Outlook desktop application
    using COM automation.

.DESCRIPTION
    All parameters are optional at the command line. Missing required values
    (To, Subject, Body) are resolved in priority order:
        1. Parameter passed by the caller
        2. Environment variable  (OUTLOOK_MAIL_TO, OUTLOOK_MAIL_SUBJECT, etc.)
        3. Interactive prompt

.PARAMETER To
    Recipient email address(es). Separate multiple addresses with a semicolon.

.PARAMETER Subject
    Subject line of the email.

.PARAMETER Body
    Body content of the email (plain text or HTML).

.PARAMETER Cc
    CC recipient(s). Separate multiple addresses with a semicolon.

.PARAMETER Bcc
    BCC recipient(s). Separate multiple addresses with a semicolon.

.PARAMETER Attachments
    One or more file paths to attach. Separate multiple paths with a comma.

.PARAMETER BodyFormat
    'plain' (default) or 'html'.

.PARAMETER SenderAlias
    Send the email from a specific alias / secondary account configured in Outlook.

.EXAMPLE
    .\Send-OutlookMail.ps1 -To "alice@example.com" -Subject "Hello" -Body "Hi there!"

.EXAMPLE
    .\Send-OutlookMail.ps1
    # Will prompt for any required fields that are not set via environment variables.
#>

[CmdletBinding()]
param (
    [string]$To            = "",
    [string]$Subject       = "",
    [string]$Body          = "",
    [string]$Cc            = "",
    [string]$Bcc           = "",
    [string]$Attachments   = "",
    [string]$BodyFormat    = "",
    [string]$SenderAlias   = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helper: resolve a value from param → env var → interactive prompt
# ---------------------------------------------------------------------------
function Resolve-MailParam {
    param (
        [string]$Value,
        [string]$EnvVarName,
        [string]$PromptLabel,
        [bool]  $Required = $true,
        [string]$DefaultDisplay = ""
    )

    # 1. Explicit parameter provided?
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        return $Value
    }

    # 2. Environment variable set?
    $envVal = [System.Environment]::GetEnvironmentVariable($EnvVarName)
    if (-not [string]::IsNullOrWhiteSpace($envVal)) {
        Write-Host "  [env] $PromptLabel loaded from `$$EnvVarName" -ForegroundColor DarkGray
        return $envVal
    }

    # 3. Not required — return empty
    if (-not $Required) {
        return ""
    }

    # 4. Ask the user interactively
    $hint = if ($DefaultDisplay) { " [$DefaultDisplay]" } else { "" }
    $inText = Read-Host "  Enter $PromptLabel$hint"
    if ([string]::IsNullOrWhiteSpace($inText)) {
        if ($DefaultDisplay) { return $DefaultDisplay }
        throw "Required field '$PromptLabel' was not provided."
    }
    return $inText.Trim()
}

# ---------------------------------------------------------------------------
# Resolve all parameters
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Outlook Mail Sender ===" -ForegroundColor Cyan
Write-Host "Resolving mail parameters..." -ForegroundColor Cyan
Write-Host ""

$To          = Resolve-MailParam -Value $To          -EnvVarName "OUTLOOK_MAIL_TO"          -PromptLabel "To (recipient address)"  -Required $true
$Subject     = Resolve-MailParam -Value $Subject      -EnvVarName "OUTLOOK_MAIL_SUBJECT"      -PromptLabel "Subject"                  -Required $true
$Body        = Resolve-MailParam -Value $Body         -EnvVarName "OUTLOOK_MAIL_BODY"         -PromptLabel "Body"                     -Required $true
$Cc          = Resolve-MailParam -Value $Cc           -EnvVarName "OUTLOOK_MAIL_CC"           -PromptLabel "Cc (optional)"            -Required $false
$Bcc         = Resolve-MailParam -Value $Bcc          -EnvVarName "OUTLOOK_MAIL_BCC"          -PromptLabel "Bcc (optional)"           -Required $false
$SenderAlias = Resolve-MailParam -Value $SenderAlias  -EnvVarName "OUTLOOK_SENDER_ALIAS"      -PromptLabel "Sender alias (optional)"  -Required $false
$BodyFormat  = Resolve-MailParam -Value $BodyFormat   -EnvVarName "OUTLOOK_MAIL_BODY_FORMAT"  -PromptLabel "Body format (plain/html)" -Required $false -DefaultDisplay "plain"
if ([string]::IsNullOrWhiteSpace($BodyFormat)) { $BodyFormat = "html" }



# ---------------------------------------------------------------------------
# Summary confirmation
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "--- Mail summary ---" -ForegroundColor Yellow
Write-Host "  To          : $To"
Write-Host "  Cc          : $(if ($Cc) { $Cc } else { '(none)' })"
Write-Host "  Bcc         : $(if ($Bcc) { $Bcc } else { '(none)' })"
Write-Host "  Subject     : $Subject"
Write-Host "  BodyFormat  : $BodyFormat"
Write-Host "  Attachments : $(if ($Attachments) { $Attachments } else { '(none)' })"
Write-Host "  SenderAlias : $(if ($SenderAlias) { $SenderAlias } else { '(default account)' })"
Write-Host "  Body        : $($Body.Substring(0, [Math]::Min(80, $Body.Length)))$(if ($Body.Length -gt 80) {'...'})"
Write-Host ""

# ---------------------------------------------------------------------------
# Create Outlook COM object and compose mail
# ---------------------------------------------------------------------------
Write-Host "Connecting to Outlook..." -ForegroundColor Cyan

try {
    $outlook = New-Object -ComObject Outlook.Application
} catch {
    Write-Error "Failed to create Outlook COM object. Is Microsoft Outlook installed and configured?`nDetails: $_"
    exit 1
}

$mail = $outlook.CreateItem(0)  # 0 = olMailItem

# Recipients
$mail.To = $To
if (-not [string]::IsNullOrWhiteSpace($Cc))  { $mail.CC  = $Cc  }
if (-not [string]::IsNullOrWhiteSpace($Bcc)) { $mail.BCC = $Bcc }

# Subject & body
$mail.Subject = $Subject

if ($BodyFormat -eq "html") {
    $mail.HTMLBody = $Body
} else {
    $mail.Body = $Body
}

# Sender alias (Send As / Send On Behalf)
if (-not [string]::IsNullOrWhiteSpace($SenderAlias)) {
    try {
        # Look for a matching account in Outlook's accounts list
        $accounts = $outlook.Session.Accounts
        $matchedAccount = $null
        foreach ($account in $accounts) {
            if ($account.SmtpAddress -ieq $SenderAlias -or $account.DisplayName -ieq $SenderAlias) {
                $matchedAccount = $account
                break
            }
        }

        if ($matchedAccount) {
            # SendUsingAccount is a property on MailItem that controls which account sends
            $mail.SendUsingAccount = $matchedAccount
        } else {
            Write-Warning "Sender alias '$SenderAlias' not found among Outlook accounts. Sending from default account."
        }
    } catch {
        Write-Warning "Could not set sender alias: $_"
    }
}

# Attachments
if (-not [string]::IsNullOrWhiteSpace($Attachments)) {
    $paths = $Attachments -split ","
    foreach ($path in $paths) {
        $path = $path.Trim()
        if (Test-Path $path) {
            $mail.Attachments.Add($path) | Out-Null
            Write-Host "  Attached: $path" -ForegroundColor DarkGray
        } else {
            Write-Warning "Attachment not found and will be skipped: $path"
        }
    }
}

# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------
Write-Host "Sending mail..." -ForegroundColor Cyan
try {
    $mail.Send()
    Write-Host ""
    Write-Host "Email sent successfully to: $To" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Error "Failed to send email.`nDetails: $_"
    exit 1
} finally {
    # Release COM objects
    if ($null -ne $mail)    { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($mail)    | Out-Null }
    if ($null -ne $outlook) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($outlook) | Out-Null }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

exit 0
