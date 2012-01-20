from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
mirror_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'
autotest_dir = os.path.abspath(os.path.join(mirror_dir, ".."))

setup(name='autotest',
      description='Autotest mirror framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.mirror': mirror_dir },
      packages=['autotest.mirror' ],
      data_files=[('usr/share/autotest/mirror', [ mirror_dir + '/mirror' ])],
)
