from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
cli_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'
autotest_dir = os.path.abspath(os.path.join(cli_dir, ".."))

setup(name='autotest',
      description='Autotest cli framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.cli': cli_dir },
      package_data={'autotest.cli' : ['contrib/*' ] },
      packages=['autotest.cli' ],
      scripts=[cli_dir + '/atest',
               cli_dir + '/autotest-rpc-client',
               cli_dir + '/atest_migrate_host',
              ],
      data_files=[('usr/share/autotest/cli', [ cli_dir + '/compose_query',
                                               cli_dir + '/query_keyvals',
                                               cli_dir + '/query_results',
                                             ]),
                 ],
)
