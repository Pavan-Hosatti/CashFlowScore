import http.client
import json

boundary = '----CashFlowScoreBoundary'
body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="file"; filename="sample.csv"\r\n'
    'Content-Type: text/csv\r\n\r\n'
    'business_name,inflow_amount,gst_delay_days,bounce_count\r\n'
    'Demo,430000,1,0\r\n'
    'Demo2,180000,5,2\r\n'
    '--' + boundary + '--\r\n'
).encode('utf-8')

conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=10)
headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
conn.request('POST', '/score-batch', body=body, headers=headers)
resp = conn.getresponse()
print(resp.status)
print(resp.read().decode('utf-8'))
