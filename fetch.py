import boto3 

sqs = boto3.client('sqs') 
queue_url = 'https://sqs.us-east-1.amazonaws.com/269829599210/ds5220'

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

def delete_message(receipt_handle): 
    response = sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print(response) 
    return response['ResponseMetadata']['RequestId']

print(response['Messages'])
delete_message(response['Messages'][0]['ReceiptHandle'])




