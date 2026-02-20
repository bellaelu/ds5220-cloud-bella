import boto3 

sqs = boto3.client('sqs') 
queue_url = 'https://sqs.us-east-1.amazonaws.com/269829599210/ds5220'

response = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=[
        'All'
    ]
)

#print(response) 

print(f'Approximate messages: {response["Attributes"]["ApproximateNumberOfMessages"]}')
print(f'Delayed messages: {response["Attributes"]["ApproximateNumberOfMessagesDelayed"]}')
print(f'Not visible messages: {response["Attributes"]["ApproximateNumberOfMessagesNotVisible"]}')