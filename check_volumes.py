import boto
from alfajor import aws_ec2

ec2 = aws_ec2.EC2(debug = True, verbose = True)
print ec2

ec2.list_all_volumes()

#if ec2.list_unattached_volumes() == 0:
#  print "no volumes were found"

#ec.set pprint
#ec2.list_instances()
#ec2.list_tagged_instances("MakeSnapshot", "true")
#ec2.create_backups()
