import boto3 

sqs = boto3.client('sqs') 
queue_url = 'https://sqs.us-east-1.amazonaws.com/269829599210/ds5220'


def send_message(message): 
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    print(response)
    return response['MessageId']

send_message('Hello, world!')