from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
client_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'
autotest_dir = os.path.abspath(os.path.join(client_dir, ".."))

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
pd_filelist=['virt/scripts/*.py', 'virt/*.sample', 'virt/passfd.c', 'config/*' ]
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'profilers')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'samples')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'tests')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'autoit')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'autotest_control')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'blkdebug')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'deps')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'steps')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'tests')))
pd_filelist.extend(get_data_files(os.path.join(client_dir, 'virt', 'unattended')))

setup(name='autotest',
      description='Autotest test framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.client': client_dir,
                   'autotest' : autotest_dir,
                  },
      package_data={'autotest.client' : pd_filelist },
      packages=['autotest.client.common_lib',
                'autotest.client.common_lib.hosts',
                'autotest.client.common_lib.test_utils',
                'autotest.client.bin',
                'autotest.client.bin.net',
                'autotest.client.tools',
                'autotest.client.profilers',
                'autotest.client.tests',
                'autotest.client.virt',
                'autotest.client',
                'autotest',
               ],
      scripts=[client_dir + '/bin/autotest',
               client_dir + '/bin/autotest_client',
               client_dir + '/bin/autotest-local',
               client_dir + '/bin/autotestd',
               client_dir + '/bin/autotestd_monitor',
              ],
      data_files=[('usr/share/autotest/client/tools', [client_dir + '/tools/autotest',
                                                       client_dir + '/tools/avgtime',
                                                       client_dir + '/tools/boottool',
                                                       client_dir + '/tools/diffprofile',
                                                       client_dir + '/tools/make_clean',
                                                       client_dir + '/tools/oprofile_diff',
                                                       client_dir + '/tools/setidle.c'
                                              ]),
                  #('etc/autotest', [ autotest_dir + '/global_config.ini',
                  #                   autotest_dir + '/shadow_config.ini',
                  #                 ]),
                 ],
)
