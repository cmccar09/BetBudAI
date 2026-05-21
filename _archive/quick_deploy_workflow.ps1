# Quick deployment of workflow Lambda
Write-Host "Deploying betting-workflow Lambda..." -ForegroundColor Cyan

# Just the handler file
Compress-Archive -Path lambda_workflow_handler.py -DestinationPath workflow_deploy.zip -Force

# Deploy
aws lambda update-function-code `
    --function-name betting-workflow `
    --zip-file fileb://workflow_deploy.zip `
    --region eu-west-1

Write-Host "Deployed!" -ForegroundColor Green
