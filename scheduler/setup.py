from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
scheduler_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'
autotest_dir = os.path.abspath(os.path.join(scheduler_dir, ".."))

setup(name='autotest',
      description='Autotest scheduler framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.scheduler': scheduler_dir },
      package_data={'autotest.scheduler': ['archive_results.control.srv']},
      packages=['autotest.scheduler' ],
      data_files=[('sbin', [scheduler_dir + '/monitor_db_babysitter'])]
)
