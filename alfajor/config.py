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
    return self.compile_connection(self.config)

  def compile_connection(self, config):
    aws_dict = {"region_name": config["region"]}
    if self.check_value("assumed_role", config) and self.check_value("use_assumed_role", config["assumed_role"]) and config["assumed_role"]["use_assumed_role"]:
      print config
      aws_dict["assumed_role"] = True
      if not self.check_value("assumed_role_arn", config["assumed_role"]):
        raise ValueError("assumed_role yes but no arn")
      aws_dict["assumed_role_arn"] = config["assumed_role"]["assumed_role_arn"]
    elif self.check_value("aws_access_key_id", config):
      if not self.check_value("aws_secret_access_key", config):
       raise ValueError('No tag provided for backup and snapshot:instance_tag set')
      aws_dict["aws_access_key_id"] = config["aws_access_key_id"]
      aws_dict["aws_secret_access_key"] = config["aws_secret_access_key"]
    #TODO: proxy
    return aws_dict

  def get_default_sns_arn(self):
    return self.config["sns_arn"]

  def check_value(self, k, d):
    found = False
    if k in d and (d[k] != "" and d[k] is not None):
      found = True
    return found
