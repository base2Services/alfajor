import sys
import os

pwd = os.environ['PWD']
alfajor_path = "{0}".format(pwd) # if running from alfajor root
alfajor_path2 = "{0}/..".format(pwd) #if running from scripts folder
alfajor_path3 = "{0}/alfajor".format(pwd) #if running from folder above alfajor

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
