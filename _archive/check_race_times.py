"""Check current time and race status"""
from datetime import datetime
import pytz

uk = pytz.timezone('Europe/London')
now = datetime.now(uk)

print(f'Current UK time: {now.strftime("%H:%M")}')
print('\nScheduled races (10 UI picks):')

races = [
    ('14:07', 'Sedgefield', 'Huit Reflets'),
    ('14:58', 'Ludlow', 'Rodney'),
    ('15:33', 'Ludlow', 'Sallyville Lady'),
    ('15:35', 'Carlisle', 'Haarar'),
    ('15:35', 'Carlisle', 'Medieval Gold'),
    ('15:45', 'Kempton', 'Fiddlers Green'),
    ('16:28', 'Sedgefield', 'Getaway With You'),
    ('16:42', 'Ludlow', 'Barton Snow'),
    ('16:42', 'Ludlow', 'Jefferys Cross'),
    ('20:00', 'Wolverhampton', 'Grey Horizon')
]

for time, course, horse in races:
    hour = int(time.split(':')[0])
    minute = int(time.split(':')[1])
    
    if hour < now.hour or (hour == now.hour and minute <= now.minute):
        status = 'SHOULD BE FINISHED'
    else:
        status = 'Still to run'
    
    print(f'  {time} {course:15} {horse:20} {status}')
