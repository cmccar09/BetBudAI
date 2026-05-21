#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy complete betting workflow to AWS Lambda with EventBridge triggers
.DESCRIPTION
    Deploys Lambda function that runs every 2 hours (10am-8pm) to:
    - Fetch Betfair odds
    - Generate picks using Claude/Bedrock
    - Store in DynamoDB
    - Optionally auto-place bets
#>

param(
    [string]$Region = "eu-west-1",
    [switch]$UpdateSchedule
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deploy Betting Workflow to AWS Lambda" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$functionName = "BettingWorkflowScheduled"
$roleName = "BettingWorkflowLambdaRole"
$packageDir = "$PSScriptRoot\lambda-workflow-package"
$zipFile = "$PSScriptRoot\betting-workflow.zip"

# Step 1: Create IAM role with full permissions
Write-Host "Step 1: Setting up IAM role..." -ForegroundColor Yellow

$existingRole = aws iam get-role --role-name $roleName --region $Region 2>$null | ConvertFrom-Json
if (-not $existingRole) {
    Write-Host "  Creating IAM role..." -ForegroundColor Gray
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = @("lambda.amazonaws.com", "bedrock.amazonaws.com")
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    Set-Content -Path "trust-policy-lambda.json" -Value $trustPolicy
    
    aws iam create-role `
        --role-name $roleName `
        --assume-role-policy-document file://trust-policy-lambda.json `
        --region $Region
    
    Write-Host "  Attaching policies..." -ForegroundColor Gray
    
    # Basic Lambda execution
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    # DynamoDB full access for storing picks
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
    
    # Bedrock access for Claude
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
    
    Write-Host "  Waiting 10 seconds for IAM propagation..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    $existingRole = aws iam get-role --role-name $roleName --region $Region | ConvertFrom-Json
}

$roleArn = $existingRole.Role.Arn
Write-Host "  Role ARN: $roleArn" -ForegroundColor Green

# Step 2: Prepare Lambda package
Write-Host "`nStep 2: Creating Lambda deployment package..." -ForegroundColor Yellow

# Clean and create package directory
if (Test-Path $packageDir) {
    Remove-Item -Path $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

Write-Host "  Copying workflow files..." -ForegroundColor Gray

# Copy main Lambda function
Copy-Item -Path "$PSScriptRoot\lambda_workflow_handler.py" -Destination "$packageDir\lambda_function.py" -ErrorAction SilentlyContinue
if (-not (Test-Path "$packageDir\lambda_function.py")) {
    # If new file doesn't exist, use existing one
    Copy-Item -Path "$PSScriptRoot\lambda_function_eu_west.py" -Destination "$packageDir\lambda_function.py"
}

# Copy Betfair credentials template (Lambda will use env vars)
Copy-Item -Path "$PSScriptRoot\betfair-creds.json" -Destination "$packageDir\betfair-creds.json" -ErrorAction SilentlyContinue

# Copy prompt.txt for strategy
Copy-Item -Path "$PSScriptRoot\prompt.txt" -Destination "$packageDir\prompt.txt" -ErrorAction SilentlyContinue

# Install Python dependencies
Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
& python -m pip install --target $packageDir --upgrade boto3 requests anthropic 2>&1 | Out-Null

# Create ZIP
Write-Host "  Creating ZIP file..." -ForegroundColor Gray
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

# Use PowerShell compression
Compress-Archive -Path "$packageDir\*" -DestinationPath $zipFile -Force

$zipSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  Package size: $($zipSize.ToString('0.00')) MB" -ForegroundColor Green

# Step 3: Create or update Lambda function
Write-Host "`nStep 3: Deploying Lambda function..." -ForegroundColor Yellow

$existingFunction = aws lambda get-function --function-name $functionName --region $Region 2>$null
if (-not $existingFunction) {
    Write-Host "  Creating new Lambda function..." -ForegroundColor Gray
    
    aws lambda create-function `
        --function-name $functionName `
        --runtime python3.11 `
        --role $roleArn `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://$zipFile `
        --timeout 900 `
        --memory-size 512 `
        --region $Region `
        --environment "Variables={
            BETFAIR_USERNAME=$env:BETFAIR_USERNAME,
            BETFAIR_PASSWORD=$env:BETFAIR_PASSWORD,
            BETFAIR_APP_KEY=$env:BETFAIR_APP_KEY,
            SUREBET_DDB_TABLE=SureBetBets,
            ENABLE_AUTO_BETTING=false
        }"
    
    Write-Host "  Function created!" -ForegroundColor Green
} else {
    Write-Host "  Updating existing function..." -ForegroundColor Gray
    
    aws lambda update-function-code `
        --function-name $functionName `
        --zip-file fileb://$zipFile `
        --region $Region
    
    Start-Sleep -Seconds 2
    
    aws lambda update-function-configuration `
        --function-name $functionName `
        --timeout 900 `
        --memory-size 512 `
        --region $Region
    
    Write-Host "  Function updated!" -ForegroundColor Green
}

# Step 4: Set up EventBridge (CloudWatch Events) rules
Write-Host "`nStep 4: Setting up EventBridge scheduled triggers..." -ForegroundColor Yellow

# Times: 10am, 12pm, 2pm, 4pm, 6pm, 8pm, 10pm (UTC times for IST/GMT)
$scheduleTimes = @(
    @{Name="BettingWorkflow10AM"; Cron="cron(0 10 * * ? *)"; Desc="10:00 AM daily"},
    @{Name="BettingWorkflow12PM"; Cron="cron(0 12 * * ? *)"; Desc="12:00 PM daily"},
    @{Name="BettingWorkflow2PM";  Cron="cron(0 14 * * ? *)"; Desc="2:00 PM daily"},
    @{Name="BettingWorkflow4PM";  Cron="cron(0 16 * * ? *)"; Desc="4:00 PM daily"},
    @{Name="BettingWorkflow6PM";  Cron="cron(0 18 * * ? *)"; Desc="6:00 PM daily"},
    @{Name="BettingWorkflow8PM";  Cron="cron(0 20 * * ? *)"; Desc="8:00 PM daily (results)"},
    @{Name="BettingWorkflow10PM"; Cron="cron(0 22 * * ? *)"; Desc="10:00 PM daily (results)"}
)

foreach ($schedule in $scheduleTimes) {
    $ruleName = $schedule.Name
    
    Write-Host "  Creating rule: $ruleName ($($schedule.Desc))..." -ForegroundColor Gray
    
    # Create or update EventBridge rule
    aws events put-rule `
        --name $ruleName `
        --schedule-expression $schedule.Cron `
        --state ENABLED `
        --description $schedule.Desc `
        --region $Region | Out-Null
    
    # Add Lambda permission to be invoked by EventBridge
    aws lambda add-permission `
        --function-name $functionName `
        --statement-id "$ruleName-Permission" `
        --action "lambda:InvokeFunction" `
        --principal events.amazonaws.com `
        --source-arn "arn:aws:events:${Region}:$(aws sts get-caller-identity --query Account --output text):rule/$ruleName" `
        --region $Region 2>$null | Out-Null
    
    # Add Lambda as target
    $targets = @(
        @{
            Id = "1"
            Arn = "arn:aws:lambda:${Region}:$(aws sts get-caller-identity --query Account --output text):function/$functionName"
        }
    ) | ConvertTo-Json -Compress
    
    Set-Content -Path "targets-temp.json" -Value "[$targets]"
    
    aws events put-targets `
        --rule $ruleName `
        --targets file://targets-temp.json `
        --region $Region | Out-Null
    
    Remove-Item "targets-temp.json" -ErrorAction SilentlyContinue
}

Write-Host "  All EventBridge rules created!" -ForegroundColor Green

# Step 5: Test the function
Write-Host "`nStep 5: Testing Lambda function..." -ForegroundColor Yellow

Write-Host "  Invoking function manually..." -ForegroundColor Gray
aws lambda invoke `
    --function-name $functionName `
    --region $Region `
    --log-type Tail `
    response.json

if (Test-Path "response.json") {
    $response = Get-Content "response.json" | ConvertFrom-Json
    Write-Host "`n  Response:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor White
} else {
    Write-Host "  No response file generated" -ForegroundColor Yellow
}

# Cleanup
Remove-Item "trust-policy-lambda.json" -ErrorAction SilentlyContinue
Remove-Item "response.json" -ErrorAction SilentlyContinue

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Lambda Function: $functionName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Schedule: Every 2 hours (10am-10pm)" -ForegroundColor White
Write-Host "`nThe workflow will now run automatically:" -ForegroundColor Yellow
Write-Host "  - Fetch Betfair odds" -ForegroundColor White
Write-Host "  - Generate picks using Claude via Bedrock" -ForegroundColor White
Write-Host "  - Store picks in DynamoDB (SureBetBets table)" -ForegroundColor White
Write-Host "  - Frontend reads from DynamoDB" -ForegroundColor White

Write-Host "`nTo monitor:" -ForegroundColor Yellow
Write-Host "  CloudWatch Logs: /aws/lambda/$functionName" -ForegroundColor Gray
Write-Host "  DynamoDB Table: SureBetBets" -ForegroundColor Gray
Write-Host "  Frontend: Your Amplify URL" -ForegroundColor Gray

Write-Host "`nTo manually trigger:" -ForegroundColor Yellow
Write-Host "  aws lambda invoke --function-name $functionName --region $Region output.json" -ForegroundColor Gray

Write-Host "`n"
