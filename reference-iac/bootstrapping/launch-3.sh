#!/bin/bash

# docker compose

aws ec2 run-instances \
  --image-id ami-0b6c6ebed2801a5cb \
  --count 1 \
  --instance-type t3.micro \
  --key-name ds5220awssshkey \
  --security-group-ids sg-027202f144b2a1ca8 \
  --user-data file://bootstrap-3.sh
