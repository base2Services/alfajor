import boto.sns
from alfajor import config
from alfajor import aws_base
from aws_base import AWS_BASE

class SNS(AWS_BASE):
  sns_conn = None

  def init(self):
    self.set_conn(boto.sns.connect_to_region(**self.get_connection_settings()))

  def send_message(self, message, subject, arn = None):
    if arn == None:
      arn = self.get_config().get_default_sns_arn()
    return self.get_conn().publish(arn, message, subject)

  def get_topics(self):
    return self.get_conn().get_all_topics()

  def show_topics(self):
    topics = self.get_conn().get_all_topics()
    mytopics = topics["ListTopicsResponse"]["ListTopicsResult"]["Topics"]
    print mytopics

