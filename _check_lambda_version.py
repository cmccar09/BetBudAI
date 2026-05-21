import boto3
client = boto3.client('lambda', region_name='eu-west-1')

# Check aliases
try:
    aliases = client.list_aliases(FunctionName='BettingPicksAPI')
    for a in aliases['Aliases']:
        print(f"Alias: {a['Name']} -> v{a['FunctionVersion']}")
except Exception as e:
    print(f"Aliases error: {e}")

# Check function URL config
try:
    url_cfg = client.get_function_url_config(FunctionName='BettingPicksAPI')
    print(f"URL: {url_cfg.get('FunctionUrl')}")
except Exception as e:
    print(f"URL config error: {e}")

# Check current $LATEST
fn = client.get_function(FunctionName='BettingPicksAPI')
print(f"Last modified: {fn['Configuration']['LastModified']}")
print(f"Version: {fn['Configuration']['Version']}")
print(f"CodeSha256: {fn['Configuration']['CodeSha256']}")
