from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
server_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'

def get_data_files(path):
    '''
    Given a path, return all the files in there to package
    '''
    flist=[]
    for root, _, files in sorted(os.walk(path)):
        for name in files:
            fullname = os.path.join(root, name)
            flist.append(fullname)
    return flist

#some stuff is too hard to package. just grab every file in these directories
#and call it a day.  we can clean up some other time
pd_filelist=[]
pd_filelist.extend(get_data_files(os.path.join(server_dir, 'control_segments')))
pd_filelist.extend(get_data_files(os.path.join(server_dir, 'hosts', 'monitors')))
pd_filelist.extend(get_data_files(os.path.join(server_dir, 'samples')))
pd_filelist.extend(get_data_files(os.path.join(server_dir, 'tests')))

setup(name='autotest',
      description='Autotest server',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.server': server_dir },
      package_data={'autotest.server' : pd_filelist },
      packages=['autotest.server.hosts',
                'autotest.server.hosts.monitors',
                'autotest.server',
               ],
      scripts=[server_dir + '/autoserv',
               server_dir + '/autotest-remote',
              ],
)
