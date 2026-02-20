import boto3 

sqs = boto3.client('sqs') 

def create_queue(queue_name): 
    response = sqs.create_queue(QueueName=queue_name)
    print('Queue URL: ' + response['QueueUrl'])
    return response['QueueUrl'] 

create_queue('ds5220')

