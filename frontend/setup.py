from distutils.core import setup
from glob import glob
import os, sys

#mostly needed when called one level up
fe_dir = os.path.dirname(sys.modules[__name__].__file__) or '.'

#TODO handle the client directory
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
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'client')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'afe', 'doctests')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'afe', 'fixtures')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'afe', 'templates')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'static')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'templates')))
pd_filelist.extend(get_data_files(os.path.join(fe_dir, 'tko', 'preconfigs')))

setup(name='autotest',
      description='Autotest test framework',
      author='LMR',
      url='autotest.kernel.org',
      package_dir={'autotest.frontend': fe_dir },
      package_data={'autotest.frontend' : pd_filelist },
      packages=['autotest.frontend.afe',
                'autotest.frontend.afe.feeds',
                'autotest.frontend.afe.json_rpc',
                'autotest.frontend.db',
                'autotest.frontend.db.backends',
                'autotest.frontend.db.backends.afe',
                'autotest.frontend.db.backends.afe_sqlite',
                'autotest.frontend.migrations',
                'autotest.frontend.shared',
                'autotest.frontend.tko',
                'autotest.frontend',
               ],
       scripts=[fe_dir + '/autotest-manage-rpc-server'],
)
