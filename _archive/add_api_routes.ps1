# Add missing API Gateway routes
# Adds /picks/yesterday and /picks/greyhounds routes

Write-Host "Adding missing API Gateway routes..." -ForegroundColor Cyan
Write-Host "=" * 60

$apiId = "e5na6ldp35"
$region = "eu-west-1"

# Get resources
$resources = aws apigateway get-resources --rest-api-id $apiId --region $region | ConvertFrom-Json

# Find /picks resource
$picksResource = $resources.items | Where-Object { $_.path -eq "/picks" }

if (-not $picksResource) {
    Write-Host "ERROR: Could not find /picks resource" -ForegroundColor Red
    exit 1
}

Write-Host "Found /picks resource: $($picksResource.id)" -ForegroundColor Green

# Function to create a new resource and methods
function Add-ApiResource {
    param(
        [string]$ParentId,
        [string]$PathPart,
        [string]$LambdaArn
    )
    
    Write-Host "`nCreating /$PathPart resource..." -ForegroundColor Yellow
    
    # Create resource
    $newResource = aws apigateway create-resource `
        --rest-api-id $apiId `
        --parent-id $ParentId `
        --path-part $PathPart `
        --region $region | ConvertFrom-Json
    
    $resourceId = $newResource.id
    Write-Host "  Resource ID: $resourceId" -ForegroundColor Green
    
    # Add GET method
    Write-Host "  Adding GET method..." -ForegroundColor Yellow
    aws apigateway put-method `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method GET `
        --authorization-type NONE `
        --region $region | Out-Null
    
    # Add Lambda integration
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method GET `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri $LambdaArn `
        --region $region | Out-Null
    
    # Add OPTIONS method for CORS
    Write-Host "  Adding OPTIONS method..." -ForegroundColor Yellow
    aws apigateway put-method `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $region | Out-Null
    
    # Add MOCK integration for OPTIONS
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' `
        --region $region | Out-Null
    
    # Add method response for OPTIONS
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
        --region $region | Out-Null
    
    # Add integration response for OPTIONS with CORS headers
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        --region $region | Out-Null
    
    Write-Host "  ✓ /$PathPart created successfully" -ForegroundColor Green
    return $resourceId
}

# Get Lambda function ARN
$lambdaArn = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:813281204422:function:betting/invocations"

# Check if yesterday resource already exists
$yesterdayExists = $resources.items | Where-Object { $_.pathPart -eq "yesterday" }
if (-not $yesterdayExists) {
    Add-ApiResource -ParentId $picksResource.id -PathPart "yesterday" -LambdaArn $lambdaArn
} else {
    Write-Host "`n/picks/yesterday already exists" -ForegroundColor Yellow
}

# Check if greyhounds resource already exists  
$greyhoundsExists = $resources.items | Where-Object { $_.pathPart -eq "greyhounds" }
if (-not $greyhoundsExists) {
    Add-ApiResource -ParentId $picksResource.id -PathPart "greyhounds" -LambdaArn $lambdaArn
} else {
    Write-Host "`n/picks/greyhounds already exists" -ForegroundColor Yellow
}

# Deploy changes
Write-Host "`nDeploying changes to 'prod' stage..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --stage-name prod `
    --description "Added /picks/yesterday and /picks/greyhounds routes" `
    --region $region | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
    Write-Host "`nNew endpoints available:" -ForegroundColor Cyan
    Write-Host "  GET /api/picks/yesterday" -ForegroundColor White
    Write-Host "  GET /api/picks/greyhounds" -ForegroundColor White
} else {
    Write-Host "✗ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ Complete!" -ForegroundColor Green
