from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
db_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'
autotest_dir = os.path.abspath(os.path.join(db_dir, ".."))

setup(name='autotest',
      description='Autotest database framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.database': db_dir },
      package_data={'autotest.database' : ['*.sql' ] },
      packages=['autotest.database' ],
      scripts=[db_dir + '/autotest-upgrade-db'],
)
