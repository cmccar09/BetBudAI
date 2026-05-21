# Verify email addresses in AWS SES
# Run this once to verify the recipient email addresses

$emails = @(
    "charles.mccarthy@gmail.com",
    "dryanfitness@gmail.com"
)

Write-Host "Verifying email addresses in AWS SES..." -ForegroundColor Cyan
Write-Host ""

foreach ($email in $emails) {
    try {
        aws ses verify-email-identity --email-address $email --region eu-west-1
        Write-Host "✅ Verification email sent to: $email" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to send verification to: $email" -ForegroundColor Red
        Write-Host "   Error: $_" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Check the inbox for each email address"
Write-Host "2. Click the verification link in the AWS SES email"
Write-Host "3. Once verified, the daily reports will be sent successfully"
Write-Host ""
Write-Host "To check verification status:"
Write-Host "  aws ses list-verified-email-addresses --region eu-west-1"
Write-Host ""
