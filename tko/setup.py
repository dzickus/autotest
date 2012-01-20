from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
tko_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'

#TODO add some toplevel non-python files

setup(name='autotest',
      description='Autotest tko Framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.tko': tko_dir },
      package_data={'autotest.tko' : ['*.cgi',
                                     ],
                   },
      packages=['autotest.tko.migrations',
                'autotest.tko.parsers',
                'autotest.tko.parsers.test',
                'autotest.tko.parsers.test.templates',
                'autotest.tko',
               ],
      data_files=[('usr/share/autotest/tko', [ tko_dir + '/blank.gif',
                                               tko_dir + '/create_db-postgres',
                                               tko_dir + '/delete_job_results',
                                               tko_dir + '/draw_graphs',
                                               tko_dir + '/machine_load',
                                               tko_dir + '/parse',
                                               tko_dir + '/plotgraph',
                                               tko_dir + '/retrieve_jobs',
                                               tko_dir + '/tko.proto',
                                             ]),
                 ]
)
