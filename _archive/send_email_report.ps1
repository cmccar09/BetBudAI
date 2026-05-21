# Send Failure Report Email via Gmail
# Sends HTML report to charles.mccarthy@gmail.com

$To = "charles.mccarthy@gmail.com"
$From = "betting.system@automated.local"
$Subject = "🚨 BETTING SYSTEM FAILURE REPORT - February 22, 2026"

# Read the HTML report
$Body = Get-Content "system_failure_report.html" -Raw -Encoding UTF8

Write-Host "="*80
Write-Host "SENDING EMAIL REPORT"
Write-Host "="*80
Write-Host ""
Write-Host "To: $To"
Write-Host "Subject: $Subject"
Write-Host "Body Size: $($Body.Length) characters"
Write-Host ""

# Try to send via Gmail SMTP
try {
    Write-Host "Note: Gmail SMTP requires an App Password, not your regular password."
    Write-Host "To create an App Password:"
    Write-Host "  1. Go to myaccount.google.com"
    Write-Host "  2. Security → 2-Step Verification → App passwords"
    Write-Host "  3. Generate password for 'Mail'"
    Write-Host ""
    Write-Host "Enter your Gmail credentials when prompted..."
    Write-Host ""
    
    $Credential = Get-Credential -Message "Enter charles.mccarthy@gmail.com and App Password"
    
    $MailParams = @{
        To = $To
        From = $From
        Subject = $Subject
        Body = $Body
        BodyAsHtml = $true
        SmtpServer = "smtp.gmail.com"
        Port = 587
        UseSsl = $true
        Credential = $Credential
    }
    
    Send-MailMessage @MailParams
    
    Write-Host ""
    Write-Host "✓ EMAIL SENT SUCCESSFULLY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The failure report has been emailed to $To"
    Write-Host "="*80
    
} catch {
    Write-Host ""
    Write-Host "✗ Failed to send email: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "ALTERNATIVE: Manual sending"
    Write-Host "="*80
    Write-Host ""
    Write-Host "The report has been opened in your browser."
    Write-Host "You can copy it from there and paste into a Gmail compose window."
    Write-Host ""
    Write-Host "Or, open this file in your email client:"
    Write-Host "  $(Resolve-Path 'failure_report_email.eml')"
    Write-Host ""
    Write-Host "="*80
}
