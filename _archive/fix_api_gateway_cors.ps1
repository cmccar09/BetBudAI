# Fix API Gateway CORS Configuration
# Ensures all routes have proper CORS headers

Write-Host "Fixing API Gateway CORS Configuration..." -ForegroundColor Cyan
Write-Host "=" * 60

# This is a REST API (v1), not HTTP API (v2)
$apiId = "e5na6ldp35"
$region = "eu-west-1"

Write-Host "API ID: $apiId" -ForegroundColor Green
Write-Host "Region: $region" -ForegroundColor Green

# For REST API Gateway, CORS is configured per resource
# We need to enable CORS for each endpoint

Write-Host "`nGetting API resources..." -ForegroundColor Yellow
$resources = aws apigateway get-resources --rest-api-id $apiId --region $region | ConvertFrom-Json

Write-Host "Found $($resources.items.Count) resources" -ForegroundColor Green

# Find the /picks/yesterday resource
$yesterdayResource = $resources.items | Where-Object { $_.path -like "*yesterday*" }

if ($yesterdayResource) {
    Write-Host "`nFound /picks/yesterday resource:" -ForegroundColor Green
    Write-Host "  Resource ID: $($yesterdayResource.id)" -ForegroundColor White
    Write-Host "  Path: $($yesterdayResource.path)" -ForegroundColor White
    
    # Check if OPTIONS method exists
    $hasOptions = $yesterdayResource.resourceMethods.PSObject.Properties.Name -contains "OPTIONS"
    
    if (-not $hasOptions) {
        Write-Host "`nAdding OPTIONS method..." -ForegroundColor Yellow
        
        # Add OPTIONS method
        aws apigateway put-method `
            --rest-api-id $apiId `
            --resource-id $yesterdayResource.id `
            --http-method OPTIONS `
            --authorization-type NONE `
            --region $region | Out-Null
        
        # Add MOCK integration
        aws apigateway put-integration `
            --rest-api-id $apiId `
            --resource-id $yesterdayResource.id `
            --http-method OPTIONS `
            --type MOCK `
            --request-templates '{"application/json": "{\"statusCode\": 200}"}' `
            --region $region | Out-Null
        
        # Add method response
        aws apigateway put-method-response `
            --rest-api-id $apiId `
            --resource-id $yesterdayResource.id `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
            --region $region | Out-Null
        
        # Add integration response with CORS headers
        aws apigateway put-integration-response `
            --rest-api-id $apiId `
            --resource-id $yesterdayResource.id `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
            --region $region | Out-Null
        
        Write-Host "✓ OPTIONS method added" -ForegroundColor Green
    } else {
        Write-Host "`nOPTIONS method already exists" -ForegroundColor Yellow
    }
    
    # Update GET method to include CORS headers
    Write-Host "`nUpdating GET method response..." -ForegroundColor Yellow
    
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --resource-id $yesterdayResource.id `
        --http-method GET `
        --status-code 200 `
        --response-parameters "method.response.header.Access-Control-Allow-Origin=false" `
        --region $region 2>$null | Out-Null
    
    Write-Host "✓ GET method updated" -ForegroundColor Green
    
    # Deploy changes
    Write-Host "`nDeploying changes to 'prod' stage..." -ForegroundColor Yellow
    
    aws apigateway create-deployment `
        --rest-api-id $apiId `
        --stage-name prod `
        --region $region | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deployment successful!" -ForegroundColor Green
    } else {
        Write-Host "✗ Deployment failed" -ForegroundColor Red
    }
    
} else {
    Write-Host "`n! Could not find /picks/yesterday resource" -ForegroundColor Red
    Write-Host "Available paths:" -ForegroundColor Yellow
    $resources.items | ForEach-Object { Write-Host "  $($_.path)" -ForegroundColor Gray }
}

Write-Host "`n✓ Complete! Try the Check Results button again." -ForegroundColor Green
