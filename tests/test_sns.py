import boto.sns
from alfajor import aws_sns
import uuid

sns = aws_sns.SNS()
print sns
#exit()

message = "test"
subject = "test " + uuid.uuid4().urn[-12:]

print sns.send_message(message, subject)
#sns.send_message(message, subject, arn)

print sns.get_topics()

sns.show_topics()
