import sys
sys.path.append("alfajor")
import boto
from alfajor import aws_ec2

account = "default"
if len(sys.argv) < 2:
      account = sys.argv[1]

volumekeeptag = "KeepThisVolume"
if len(sys.argv) < 3:
      volumekeeptag = sys.argv[2]


ec2 = aws_ec2.EC2(debug = True, verbose = True, account = account, volumekeeptag=volumekeeptag)
#ec2.delete_unattached_volumes()
ec2.delete_unattached_volumes_with_keeptag(volumekeeptag)
