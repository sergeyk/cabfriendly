#!/bin/bash

# use ami-574e1112
cd ~/.ec2
ec2-run-instances ami-574e1112 --key ec2-keypair --instance-type t1.micro


