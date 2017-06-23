import sys
import os

pwd = os.environ['PWD']
alfajor_path = "{0}".format(pwd)
alfajor_path2 = "{0}/..".format(pwd)

sys.path.append(alfajor_path)
sys.path.append(alfajor_path2)

import boto
from alfajor import aws_ec2

# make stdout unbuffered
unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
unbuffered.write('Unbuffered output')
sys.stdout = unbuffered

account = sys.argv[1]

ec2 = aws_ec2.EC2(debug = True, verbose = True, account = account)
ec2.create_backups()
