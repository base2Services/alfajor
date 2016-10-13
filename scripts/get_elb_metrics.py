import sys
sys.path.append("alfajor")
import boto
from alfajor import get_elb_metrics

account = sys.argv[1]

gem = get_elb_metrics.ElbMetrics(debug = True, verbose = True, account=account)
#    get_elb_stats("Test-ELB", 'Requests', 'AWS/ELB', 'Sum', 60, 'ap-southeast-2', 'Count')
gem.get_elb_stats(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
