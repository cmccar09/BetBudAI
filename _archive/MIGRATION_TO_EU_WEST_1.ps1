# AWS Region Migration Summary
# SureBet Project migrated from us-east-1 to eu-west-1

Write-Host "`n=== AWS REGION MIGRATION COMPLETE ===" -ForegroundColor Green
Write-Host "Migrated from: us-east-1 → eu-west-1`n" -ForegroundColor Cyan

Write-Host "📝 NEXT STEPS REQUIRED:`n" -ForegroundColor Yellow

Write-Host "1. DynamoDB Tables" -ForegroundColor White
Write-Host "   ⚠️  Tables need to be recreated or replicated to eu-west-1:"
Write-Host "   - SureBetBets (main picks table)"
Write-Host "   - SureBetUsers (user management)"
Write-Host ""
Write-Host "   Option A - Create new tables (recommended for fresh start):"
Write-Host "     .\create_users_table.ps1  # Updated to use eu-west-1"
Write-Host "     # Also create SureBetBets table with same schema"
Write-Host ""
Write-Host "   Option B - Export from us-east-1 and import to eu-west-1:"
Write-Host "     aws dynamodb create-backup --table-name SureBetBets --backup-name surebet-migration --region us-east-1"
Write-Host "     # Then restore to eu-west-1 (requires AWS console or API)"
Write-Host ""

Write-Host "2. AWS SES Email Verification" -ForegroundColor White
Write-Host "   ⚠️  Email addresses must be re-verified in eu-west-1:"
Write-Host "     .\verify_email_recipients.ps1  # Updated to use eu-west-1"
Write-Host "   Recipients:"
Write-Host "     - charles.mccarthy@gmail.com"
Write-Host "     - dryanfitness@gmail.com"
Write-Host ""

Write-Host "3. Secrets Manager" -ForegroundColor White
Write-Host "   ⚠️  Betfair certificates need to be uploaded to eu-west-1:"
Write-Host "     .\upload_betfair_certs_to_aws.ps1  # Updated to use eu-west-1"
Write-Host ""

Write-Host "4. Lambda Functions" -ForegroundColor White
Write-Host "   ⚠️  Lambda functions need to be redeployed to eu-west-1:"
Write-Host "     .\deploy_workflow_lambda.ps1  # Already set to eu-west-1"
Write-Host "     .\deploy_api.ps1              # Already set to eu-west-1"
Write-Host "   Note: Lambda URLs will change - update frontend config if needed"
Write-Host ""

Write-Host "5. Bedrock/AI Services" -ForegroundColor White
Write-Host "   ℹ️  Bedrock region updated to eu-west-1"
Write-Host "   Verify Claude models are available in eu-west-1 region"
Write-Host ""

Write-Host "📋 FILES UPDATED:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python Scripts (18 files):"
Write-Host "  - clear_old_picks.py"
Write-Host "  - send_yesterday_top5_report.py"
Write-Host "  - update_yesterday_results.py"
Write-Host "  - manual_mark_results.py"
Write-Host "  - fetch_hourly_results.py"
Write-Host "  - update_results_from_betfair.py"
Write-Host "  - send_daily_summary.py"
Write-Host "  - save_selections_to_dynamodb.py"
Write-Host "  - run_prompt_with_betfair.py"
Write-Host "  - run_saved_prompt.py"
Write-Host "  - paddy_power_betting.py"
Write-Host "  - lambda_function_eu_west.py"
Write-Host "  - lambda_api_picks.py"
Write-Host "  - lambda-workflow-package/lambda_function.py"
Write-Host "  - lambda-check/lambda_function.py"
Write-Host "  - lambda-check/paddy_power_betting.py"
Write-Host "  - lambda-package/paddy_power_betting.py"
Write-Host "  - lambda-package/lambda_function.py"
Write-Host ""
Write-Host "PowerShell Scripts (12 files):"
Write-Host "  - verify_email_recipients.ps1"
Write-Host "  - upload_betfair_certs_to_aws.ps1"
Write-Host "  - redeploy_lambda.ps1"
Write-Host "  - quick_deploy_workflow.ps1"
Write-Host "  - generate_todays_picks.ps1"
Write-Host "  - deploy_stripe_lambdas.ps1"
Write-Host "  - deploy_updated_frontend.ps1"
Write-Host "  - deploy_workflow_lambda.ps1"
Write-Host "  - deploy_updated_lambda.ps1"
Write-Host "  - configure_lambda_betfair_creds.ps1"
Write-Host "  - create_users_table.ps1"
Write-Host "  - clear_old_data.ps1"
Write-Host "  - deploy_api.ps1"
Write-Host ""

Write-Host "⚡ QUICK START MIGRATION:" -ForegroundColor Green
Write-Host ""
Write-Host "# 1. Create DynamoDB tables"
Write-Host ".\create_users_table.ps1"
Write-Host ""
Write-Host "# 2. Verify email addresses for SES"
Write-Host ".\verify_email_recipients.ps1"
Write-Host ""
Write-Host "# 3. Upload Betfair certs to Secrets Manager"
Write-Host ".\upload_betfair_certs_to_aws.ps1"
Write-Host ""
Write-Host "# 4. Test the hourly results fetcher"
Write-Host "python fetch_hourly_results.py"
Write-Host ""
Write-Host "✅ All code has been updated to use eu-west-1!"
Write-Host ""
