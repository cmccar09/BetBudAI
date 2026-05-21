"""Fix CORS preflight on BettingAPI OPTIONS /{proxy+}"""
import boto3

agw      = boto3.client('apigateway', region_name='us-east-1')
api_id   = '7tdrotq8dl'
resource = 'mnjos9'

# 1. MOCK integration
agw.put_integration(
    restApiId=api_id, resourceId=resource, httpMethod='OPTIONS',
    type='MOCK',
    requestTemplates={'application/json': '{"statusCode": 200}'}
)
print('Integration: OK')

# 2. Method response 200 declaring the CORS headers
agw.put_method_response(
    restApiId=api_id, resourceId=resource, httpMethod='OPTIONS', statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': False,
        'method.response.header.Access-Control-Allow-Methods': False,
        'method.response.header.Access-Control-Allow-Origin':  False,
    },
    responseModels={'application/json': 'Empty'}
)
print('MethodResponse: OK')

# 3. Integration response — emit the actual header values
agw.put_integration_response(
    restApiId=api_id, resourceId=resource, httpMethod='OPTIONS', statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'",
        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
        'method.response.header.Access-Control-Allow-Origin':  "'*'",
    },
    responseTemplates={'application/json': ''}
)
print('IntegrationResponse: OK')

# 4. Deploy to prod stage
dep = agw.create_deployment(restApiId=api_id, stageName='prod',
                             description='Fix OPTIONS CORS preflight for /api/learning/apply')
print('Deployed:', dep['id'])
print('Done — preflight should now pass.')
