import requests
import json

url = 'https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/results'
r = requests.get(url)
data = r.json()

print('SUCCESS:', data.get('success'))
print('\nOVERALL SUMMARY:')
print('  Total:', data['summary']['total_picks'], 'picks')
print('  Wins:', data['summary']['wins'])
print('  Losses:', data['summary']['losses'])
print('  Profit:', data['summary']['profit'])
print('  ROI:', str(data['summary']['roi']) + '%')

print('\nHORSES:')
print('  Picks:', len(data['horses']['picks']))
if data['horses']['summary']:
    print('  Wins:', data['horses']['summary']['wins'], '/ Losses:', data['horses']['summary']['losses'])
    print('  ROI:', str(data['horses']['summary']['roi']) + '%')
else:
    print('  No summary available')

print('\nGREYHOUNDS:')
print('  Picks:', len(data['greyhounds']['picks']))
if data['greyhounds']['summary']:
    print('  Wins:', data['greyhounds']['summary']['wins'], '/ Losses:', data['greyhounds']['summary']['losses'])
    print('  ROI:', str(data['greyhounds']['summary']['roi']) + '%')
else:
    print('  No summary available')
