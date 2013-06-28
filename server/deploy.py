#!/usr/bin/env python
"""
Log into each of our instances and do a git pull.
"""
from boto.ec2 import *
import os

# Get a list of all running instances
keys = [
    'TODO',
    'TODO']
region = get_region('us-west-1')
conn = EC2Connection(*keys,region=region)
reservations = conn.get_all_instances()
instances = [reservation.instances[0] for reservation in reservations]
running_instances = [instance for instance in instances if instance.state=='running']

# Connect to each running instance and do a git pull
script_path = os.path.dirname(os.path.realpath(__file__))
path_to_keypair = os.path.join(script_path,'ec2-keypair')
for instance in running_instances:
  cmd = "ssh -i %s bitnami@%s 'uname -a && cd RideFriendly && git pull origin master'"%(
    path_to_keypair, instance.dns_name)
  print(cmd)
  os.system(cmd)
