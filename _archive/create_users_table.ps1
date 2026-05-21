# Create DynamoDB Users Table for SureBet Mobile App

Write-Host "Creating SureBetUsers table in DynamoDB..." -ForegroundColor Cyan

# Create the table
aws dynamodb create-table `
  --table-name SureBetUsers `
  --attribute-definitions `
    AttributeName=user_id,AttributeType=S `
    AttributeName=email,AttributeType=S `
  --key-schema `
    AttributeName=user_id,KeyType=HASH `
  --global-secondary-indexes `
    "IndexName=EmailIndex,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
  --provisioned-throughput `
    ReadCapacityUnits=5,WriteCapacityUnits=5 `
  --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Table created successfully!" -ForegroundColor Green
    Write-Host "`nWaiting for table to become active..." -ForegroundColor Yellow
    
    aws dynamodb wait table-exists --table-name SureBetUsers --region us-east-1
    
    Write-Host "✅ Table is now active and ready to use!" -ForegroundColor Green
    
    # Show table details
    Write-Host "`nTable Details:" -ForegroundColor Cyan
    aws dynamodb describe-table --table-name SureBetUsers --region us-east-1 --query "Table.[TableName,TableStatus,ItemCount]" --output table
    
} else {
    Write-Host "`n❌ Failed to create table. It may already exist." -ForegroundColor Red
    Write-Host "Checking if table exists..." -ForegroundColor Yellow
    
    aws dynamodb describe-table --table-name SureBetUsers --region us-east-1 --query "Table.[TableName,TableStatus]" --output table
}
