#!/usr/bin/env python3
"""Increase Lambda timeout for pipeline handlers."""

import boto3

lc = boto3.client('lambda', region_name='eu-west-1')

# Update betbudai-morning timeout
lc.update_function_configuration(
    FunctionName='betbudai-morning',
    Timeout=600,
    Description='Morning pipeline orchestrator - 600s timeout for full optimization run'
)

# Update betbudai-evening timeout
lc.update_function_configuration(
    FunctionName='betbudai-evening',
    Timeout=600,
    Description='Evening pipeline orchestrator - 600s timeout for full analysis'
)

print('✓ Updated timeouts:')
print('  - betbudai-morning: 600s')
print('  - betbudai-evening: 600s')

# Verify
for name in ['betbudai-morning', 'betbudai-evening']:
    func = lc.get_function(FunctionName=name)
    timeout = func['Configuration']['Timeout']
    print(f'  ✓ {name}: {timeout}s timeout')
