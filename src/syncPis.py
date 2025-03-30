import os
from tools.piSync import syncPis

syncPis("reef_post_hist.npy","histograms/reef_post_hist.npy",os.path.join("assets","histograms"))