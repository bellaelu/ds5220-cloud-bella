# Build Custom EC2 Instance with JupyterLab

Objectives:

1. Launch Ubuntu 24.04 EC2 instance
2. Create security group: ports 8888 and 22
3. Create S3 bucket
4. Instance Role allows all actions on bucket, and `ListAllMyBuckets`
5. Add secondary EBS volume (13GB) to instance
6. Bootstrap instance
    - Install Docker via `snap`
    - Format/mount secondary volume
    - Run JupyterLab
7. Test! `http://IPADDRESS:8888/lab?token=my-token`

> [**Template**](./ec2-with-jupyter-and-bucket.yaml)