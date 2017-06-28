import sys
import os

pwd = os.environ['PWD']
alfajor_path = "{0}".format(pwd) # if running from alfajor root
alfajor_path2 = "{0}/..".format(pwd) #if running from scripts folder
alfajor_path3 = "{0}/alfajor".format(pwd) #if running from folder above alfajor

sys.path.append(alfajor_path)
sys.path.append(alfajor_path2)
sys.path.append(alfajor_path3)


from alfajor import stale_snapshot_cleanup

sd = stale_snapshot_cleanup.SnapShotCleanup(debug = True, verbose = True)
sd.cleanup_stale_snapshots()
