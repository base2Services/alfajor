import sys
sys.path.append("alfajor")
from alfajor import get_cloudfront_metrics

gcfm = get_cloudfront_metrics.CloudFrontMetrics(debug = True, verbose = True)
#    get_elb_stats("Test-ELB", 'Requests', 'AWS/CloudFront', 'Sum', 60, 'ap-southeast-2', 'Count')
gcfm.get_cloudfront_stats(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])