import sys
sys.path.append("alfajor")
import boto
from alfajor import aws_ec2

account = sys.argv[1]

ec2 = aws_ec2.EC2(debug = True, verbose = True, account = account)
ec2.create_backups()
