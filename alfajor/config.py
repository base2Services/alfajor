import yaml

class Config():
#TODO: proxy and sts 
  def __init__(self, **kwargs):
    self.config_file = kwargs.get('config_file', 'aws_config.yml')
    self.account = kwargs.get('account', 'default')
    with open(self.config_file, 'r') as f:
      data = yaml.load(f)
    self.config = data['aws'][self.account]

  def print_config(self):
    print self.config

  def __str__(self):
    return self.config
  
  def get_config(self):
    return self.config

  def get_connection_dictionary(self):
    aws_dict = {"region_name": self.config["region"], 
            "aws_access_key_id": self.config["aws_access_key_id"], 
            "aws_secret_access_key": self.config["aws_secret_access_key"]}
    return aws_dict

  def get_default_sns_arn(self):
    return self.config["sns_arn"]

