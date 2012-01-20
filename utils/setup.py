from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
utils_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'

#TODO handle the init scripts

setup(name='autotest',
      description='Autotest utils Framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.utils': utils_dir },
      package_data={'autotest.utils' : ['named_semaphore/*',
                                        'modelviz/*',
                                       ],
                   },
      packages=['autotest.utils' ],
      data_files=[('usr/share/autotest/utils', [ utils_dir + '/autotestd.service',
                                                 utils_dir + '/autotest.init',
                                                 utils_dir + '/autotest-rh.init',
                                                 utils_dir + '/release'
                                               ])
                 ],
)
