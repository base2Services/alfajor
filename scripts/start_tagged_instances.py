import sys
sys.path.append("alfajor")
import boto
from alfajor import aws_ec2

account = "default"
if len(sys.argv) < 2:
      account = sys.argv[1]

insttag = "tag"
if len(sys.argv) < 3:
      insttag = sys.argv[2]

env = "env"
if len(sys.argv) < 4:
      env = sys.argv[3]

tier = "tier"
if len(sys.argv) < 5:
      tier = sys.argv[4]


ec2 = aws_ec2.EC2(debug = True, verbose = True, account = account)
ec2.start_instance_with_tag(insttag, env, tier)