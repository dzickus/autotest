import os, sys
from optparse import OptionParser
try:
    import autotest.common as common
    rootdir = os.path.abspath(os.path.dirname(common.__file__))
    autodir = os.path.join(rootdir, 'client')
    autodirbin = os.path.join(rootdir, 'client', 'bin')
except ImportError:
    import common
    autodirbin = os.path.dirname(os.path.realpath(sys.argv[0]))
    autodir = os.path.dirname(autodirbin)
    sys.path.insert(0, autodirbin)

from autotest_lib.client.bin import job
from autotest_lib.client.common_lib import global_config
from autotest_lib.client.bin import cmdparser

autodirtest = os.path.join(autodir, "tests")

os.environ['AUTODIR'] = autodir
os.environ['AUTODIRBIN'] = autodirbin
os.environ['AUTODIRTEST'] = autodirtest
os.environ['PYTHONPATH'] = autodirbin

cmd_parser = cmdparser.CommandParser() # Allow access to instance in parser

commandinfo = "[command] (optional)\tOne of: " + str(cmd_parser.cmdlist)
if sys.version_info[0:2] < (2,6):
    parser = OptionParser(usage='Usage: %prog [options] [command] <control-file>',
                          description=commandinfo)
else:
    parser = OptionParser(usage='Usage: %prog [options] [command] <control-file>',
                          epilog=commandinfo)

parser.add_option("-a", "--args", dest='args',
                        help="additional args to pass to control file")

parser.add_option("-c", "--continue", dest="cont", action="store_true",
                        default=False, help="continue previously started job")

parser.add_option("-t", "--tag", dest="tag", type="string", default="default",
                        help="set the job tag")

parser.add_option("-H", "--harness", dest="harness", type="string", default='',
                        help="set the harness type")

parser.add_option("-P", "--harness_args", dest="harness_args", type="string", default='',
                        help="arguments delivered to harness")

parser.add_option("-U", "--user", dest="user", type="string",
                        default='', help="set the job username")

parser.add_option("-l", "--external_logging", dest="log", action="store_true",
                        default=False, help="enable external logging")

parser.add_option('--verbose', dest='verbose', action='store_true',
                  help='Include DEBUG messages in console output')

parser.add_option('--quiet', dest='verbose', action='store_false',
                  help='Not include DEBUG messages in console output')

parser.add_option('--hostname', dest='hostname', type='string',
                  default=None, action='store',
                  help='Take this as the hostname of this machine '
                       '(given by autoserv)')

parser.add_option('--output_dir', dest='output_dir',
                  type='string', default="", action='store',
                  help='Specify an alternate path to store test result logs')

parser.add_option('--client_test_setup', dest='client_test_setup',
                  type='string', default=None, action='store',
                  help='a comma seperated list of client tests to prebuild on '
                       'the server. Use all to prebuild all of them.')

parser.add_option('--tap', dest='tap_report', action='store_true',
                  default=None, help='Output TAP (Test anything '
                  'protocol) reports')

def usage():
    parser.print_help()
    sys.exit(1)

def main():
    options, args = parser.parse_args()

    args = cmd_parser.parse_args(args)

    # Check for a control file if not in prebuild mode.
    if len(args) != 1 and options.client_test_setup is None:
        print "Missing control file!"
        usage()

    drop_caches = global_config.global_config.get_config_value('CLIENT',
                                                               'drop_caches',
                                                               type=bool,
                                                               default=True)

    if options.client_test_setup:
        from autotest_lib.client.bin import setup_job
        exit_code = 0
        try:
            setup_job.setup_tests(options)
        except Exception:
            exit_code = 1
        sys.exit(exit_code)

    # JOB: run the specified job control file.
    job.runjob(os.path.realpath(args[0]), drop_caches, options)
