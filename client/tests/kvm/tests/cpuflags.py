import logging, re, random, os, time
from autotest_lib.client.common_lib import error, utils
from autotest_lib.client.virt import kvm_vm
from autotest_lib.client.virt import virt_utils, aexpect
from autotest_lib.client.common_lib.test import Subtest, subtest_nocleanup
from autotest_lib.client.common_lib.test import subtest_fatal


def run_cpuflags(test, params, env):
    """
    Boot guest with different cpu flags and check if guest works correctly.

    @param test: kvm test object.
    @param params: Dictionary with the test parameters.
    @param env: Dictionary with test environment.
    """
    qemu_binary = virt_utils.get_path('.', params.get("qemu_binary", "qemu"))

    cpuflags_path = os.path.join(test.virtdir, "deps")
    cpuflags_tar = "cpuflags-test.tar.bz2"
    cpuflags_src = os.path.join(test.virtdir, "deps", "test_cpu_flags")
    smp = int(params.get("smp", 1))

    all_host_supported_flags = params.get("all_host_supported_flags", "no")

    mig_timeout = float(params.get("mig_timeout", "3600"))
    mig_protocol = params.get("migration_protocol", "tcp")
    mig_speed = params.get("mig_speed", "1G")


    class HgFlags(object):
        def __init__(self, cpu_model, extra_flags=set([])):
            virtual_flags = set(map(virt_utils.Flag,
                                    params.get("guest_spec_flags", "").split()))
            self.hw_flags = set(map(virt_utils.Flag,
                                    params.get("host_spec_flags", "").split()))
            self.qemu_support_flags = get_all_qemu_flags()
            self.host_support_flags = set(map(virt_utils.Flag,
                                              virt_utils.get_cpu_flags()))
            self.quest_cpu_model_flags = (get_guest_host_cpuflags(cpu_model) -
                                          virtual_flags)

            self.supported_flags = (self.qemu_support_flags &
                                    self.host_support_flags)
            self.cpumodel_unsupport_flags = (self.supported_flags -
                                             self.quest_cpu_model_flags)

            self.host_unsupported_flags = (self.quest_cpu_model_flags -
                                           self.host_support_flags)

            self.all_possible_guest_flags = (self.quest_cpu_model_flags -
                                self.host_unsupported_flags)
            self.all_possible_guest_flags |= self.cpumodel_unsupport_flags

            self.guest_flags = (self.quest_cpu_model_flags -
                                self.host_unsupported_flags)
            self.guest_flags |= extra_flags

            self.host_all_unsupported_flags = set([])
            self.host_all_unsupported_flags |= self.qemu_support_flags
            self.host_all_unsupported_flags -= (self.host_support_flags |
                                                virtual_flags)


    def start_guest_with_cpuflags(cpuflags, smp=None):
        """
        Try to boot guest with special cpu flags and try login in to them.
        """
        params_b = params.copy()
        params_b["cpu_model"] = cpuflags
        if smp is not None:
            params_b["smp"] = smp

        vm_name = "vm1-cpuflags"
        vm = kvm_vm.VM(vm_name, params_b, test.bindir, env['address_cache'])
        env.register_vm(vm_name, vm)
        vm.create()
        vm.verify_alive()

        session = vm.wait_for_login()

        return (vm, session)


    def get_guest_system_cpuflags(vm_session):
        """
        Get guest system cpuflags.

        @param vm_session: session to checked vm.
        @return: [corespond flags]
        """
        flags_re = re.compile(r'^flags\s*:(.*)$', re.MULTILINE)
        out = vm_session.cmd_output("cat /proc/cpuinfo")

        flags = flags_re.search(out).groups()[0].split()
        return set(map(virt_utils.Flag, flags))


    def get_guest_host_cpuflags(cpumodel):
        """
        Get cpu flags correspond with cpumodel parameters.

        @param cpumodel: Cpumodel parameter sended to <qemu-kvm-cmd>.
        @return: [corespond flags]
        """
        cmd = qemu_binary + " -cpu ?dump"
        output = utils.run(cmd).stdout
        re.escape(cpumodel)
        pattern = (".+%s.*\n.*\n +feature_edx .+ \((.*)\)\n +feature_"
                   "ecx .+ \((.*)\)\n +extfeature_edx .+ \((.*)\)\n +"
                   "extfeature_ecx .+ \((.*)\)\n" % (cpumodel))
        flags = []
        model = re.search(pattern, output)
        if model == None:
            raise error.TestFail("Cannot find %s cpu model." % (cpumodel))
        for flag_group in model.groups():
            flags += flag_group.split()
        return set(map(virt_utils.Flag, flags))


    def get_all_qemu_flags():
        cmd = qemu_binary + " -cpu ?cpuid"
        output = utils.run(cmd).stdout

        flags_re = re.compile(r".*\n.*f_edx:(.*)\n.*f_ecx:(.*)\n.*extf_edx:"
                              "(.*)\n.*extf_ecx:(.*)")
        m = flags_re.search(output)
        flags = []
        for a in m.groups():
            flags += a.split()

        return set(map(virt_utils.Flag, flags))


    def get_flags_full_name(cpu_flag):
        """
        Get all name of Flag.

        @param cpu_flag: Flag
        @return: all name of Flag.
        """
        cpu_flag = virt_utils.Flag(cpu_flag)
        for f in get_all_qemu_flags():
            if f == cpu_flag:
                return virt_utils.Flag(f)
        return []


    def parse_qemu_cpucommand(cpumodel):
        """
        Parse qemu cpu params.

        @param cpumodel: Cpu model command.
        @return: All flags which guest must have.
        """
        flags = cpumodel.split(",")
        cpumodel = flags[0]

        qemu_model_flag = get_guest_host_cpuflags(cpumodel)
        host_support_flag = set(map(virt_utils.Flag,
                                    virt_utils.get_cpu_flags()))
        real_flags = qemu_model_flag & host_support_flag

        for f in flags[1:]:
            if f[0].startswith("+"):
                real_flags |= set([get_flags_full_name(f[1:])])
            if f[0].startswith("-"):
                real_flags -= set([get_flags_full_name(f[1:])])

        return real_flags


    def get_cpu_models():
        """
        Get all cpu models from qemu.

        @return: cpu models.
        """
        cmd = qemu_binary + " -cpu ?"
        output = utils.run(cmd).stdout

        cpu_re = re.compile("\w+\s+\[?(\w+)\]?")
        return cpu_re.findall(output)


    def check_cpuflags(cpumodel, vm_session):
        """
        Check if vm flags are same like flags select by cpumodel.

        @param cpumodel: params for -cpu param in qemu-kvm
        @param vm_session: session to vm to check flags.

        @return: ([excess], [missing]) flags
        """
        gf = get_guest_system_cpuflags(vm_session)
        rf = parse_qemu_cpucommand(cpumodel)

        logging.debug("Guest flags: %s", gf)
        logging.debug("Host flags: %s", rf)
        logging.debug("Flags on guest not defined by host: %s", (gf - rf))
        return rf - gf


    def disable_cpu(vm_session, cpu, disable=True):
        """
        Disable cpu in guest system.

        @param cpu: CPU id to disable.
        @param disable: if True disable cpu else enable cpu.
        """
        system_cpu_dir = "/sys/devices/system/cpu/"
        cpu_online = system_cpu_dir + "cpu%d/online" % (cpu)
        cpu_state = vm_session.cmd_output("cat %s" % cpu_online).strip()
        if disable and cpu_state == "1":
            vm_session.cmd("echo 0 > %s" % cpu_online)
            logging.debug("Guest cpu %d is disabled.", cpu)
        elif cpu_state == "0":
            vm_session.cmd("echo 1 > %s" % cpu_online)
            logging.debug("Guest cpu %d is enabled.", cpu)


    def install_cpuflags_test_on_vm(vm, dst_dir):
        """
        Install stress to vm.

        @param vm: virtual machine.
        @param dst_dir: Installation path.
        """
        session = vm.wait_for_login()
        vm.copy_files_to(cpuflags_src, dst_dir)
        session.cmd("cd %s; make EXTRA_FLAGS='';" %
                    os.path.join(dst_dir, "test_cpu_flags"))
        session.close()


    def check_cpuflags_work(vm, path, flags):
        """
        Check which flags work.

        @param vm: Virtual machine.
        @param path: Path of cpuflags_test
        @param flags: Flags to test.
        @return: Tuple (Working, not working, not tested) flags.
        """
        pass_Flags = []
        not_tested = []
        not_working = []
        session = vm.wait_for_login()
        for f in flags:
            try:
                for tc in virt_utils.kvm_map_flags_to_test[f]:
                    session.cmd("%s/cpuflags-test --%s" %
                                (os.path.join(path,"test_cpu_flags"), tc))
                pass_Flags.append(f)
            except aexpect.ShellCmdError:
                not_working.append(f)
            except KeyError:
                not_tested.append(f)
        return (set(map(virt_utils.Flag, pass_Flags)),
                set(map(virt_utils.Flag, not_working)),
                set(map(virt_utils.Flag, not_tested)))


    def run_stress(vm, timeout, guest_flags):
        """
        Run stress on vm for timeout time.
        """
        ret = False
        install_path = "/tmp"
        install_cpuflags_test_on_vm(vm, install_path)
        flags = check_cpuflags_work(vm, install_path, guest_flags)
        dd_session = vm.wait_for_login()
        stress_session = vm.wait_for_login()
        dd_session.sendline("dd if=/dev/[svh]da of=/tmp/stressblock"
                            " bs=10MB count=100 &")
        try:
            stress_session.cmd("%s/cpuflags-test --stress %s%s" %
                        (os.path.join(install_path, "test_cpu_flags"), smp,
                         virt_utils.kvm_flags_to_stresstests(flags[0])),
                        timeout=timeout)
        except aexpect.ShellTimeoutError:
            ret = True
        stress_session.close()
        dd_session.close()
        return ret


    def separe_cpu_model(cpu_model):
        try:
            (cpu_model, _) = cpu_model.split(":")
        except ValueError:
            cpu_model = cpu_model
        return cpu_model


    def test_qemu_interface():
        """
        1) <qemu-kvm-cmd> -cpu ?model
        2) <qemu-kvm-cmd> -cpu ?dump
        3) <qemu-kvm-cmd> -cpu ?cpuid
        """
        # 1) <qemu-kvm-cmd> -cpu ?model
        class test_qemu_cpu_model(Subtest):
            @subtest_fatal
            @subtest_nocleanup
            def test(self):
                cpu_models = params.get("cpu_models", "core2duo").split()
                cmd = qemu_binary + " -cpu ?model"
                result = utils.run(cmd)
                missing = []
                cpu_models = map(separe_cpu_model, cpu_models)
                for cpu_model in cpu_models:
                    if not cpu_model in result.stdout:
                        missing.append(cpu_model)
                if missing:
                    raise error.TestFail("CPU models %s are not in output "
                                         "'%s' of command \n%s" %
                                         (missing, cmd, result.stdout))

        # 2) <qemu-kvm-cmd> -cpu ?dump
        class test_qemu_dump(Subtest):
            @subtest_nocleanup
            def test(self):
                cpu_models = params.get("cpu_models", "core2duo").split()
                cmd = qemu_binary + " -cpu ?dump"
                result = utils.run(cmd)
                cpu_models = map(separe_cpu_model, cpu_models)
                missing = []
                for cpu_model in cpu_models:
                    if not cpu_model in result.stdout:
                        missing.append(cpu_model)
                if missing:
                    raise error.TestFail("CPU models %s are not in output "
                                         "'%s' of command \n%s" %
                                         (missing, cmd, result.stdout))

        # 3) <qemu-kvm-cmd> -cpu ?cpuid
        class test_qemu_cpuid(Subtest):
            @subtest_nocleanup
            def test(self):
                cmd = qemu_binary + " -cpu ?cpuid"
                result = utils.run(cmd)
                if result.stdout is "":
                    raise error.TestFail("There aren't any cpu Flag in output"
                                         " '%s' of command \n%s" %
                                         (cmd, result.stdout))

        test_qemu_cpu_model()
        test_qemu_dump()
        test_qemu_cpuid()

    class test_temp(Subtest):
        def clean(self):
            logging.info("cleanup")
            if (hasattr(self, "vm")):
                self.vm.destroy(gracefully=False)

    def test_boot_guest():
        """
        1) boot with cpu_model
        2) migrate with flags
        3) <qemu-kvm-cmd> -cpu model_name,+Flag
        """
        cpu_models = params.get("cpu_models","").split()
        if not cpu_models:
            cpu_models = get_cpu_models()
        logging.debug("CPU models found: %s", str(cpu_models))

        # 1) boot with cpu_model
        class test_boot_cpu_model(test_temp):
            def test(self, cpu_model):
                logging.debug("Run tests with cpu model %s", cpu_model)
                flags = HgFlags(cpu_model)
                (self.vm, session) = start_guest_with_cpuflags(cpu_model)
                not_enable_flags = (check_cpuflags(cpu_model, session) -
                                    flags.hw_flags)
                if not_enable_flags != set([]):
                    raise error.TestFail("Flags defined on host but not found "
                                         "on guest: %s" % (not_enable_flags))


        # 2) success boot with supported flags
        class test_boot_cpu_model_and_additional_flags(test_temp):
            def test(self, cpu_model, extra_flags):
                flags = HgFlags(cpu_model, extra_flags)

                logging.debug("Cpu mode flags %s.",
                              str(flags.quest_cpu_model_flags))
                cpuf_model = cpu_model

                if all_host_supported_flags == "yes":
                    for fadd in flags.cpumodel_unsupport_flags:
                        cpuf_model += ",+" + fadd
                else:
                    for fadd in extra_flags:
                        cpuf_model += ",+" + fadd

                for fdel in flags.host_unsupported_flags:
                    cpuf_model += ",-" + fdel

                if all_host_supported_flags == "yes":
                    guest_flags = flags.all_possible_guest_flags
                else:
                    guest_flags = flags.guest_flags

                (self.vm, session) = start_guest_with_cpuflags(cpuf_model)

                not_enable_flags = (check_cpuflags(cpuf_model, session) -
                                    flags.hw_flags)
                if not_enable_flags != set([]):
                    logging.info("Model unsupported flags: %s",
                                  str(flags.cpumodel_unsupport_flags))
                    logging.error("Flags defined on host but not on found "
                                  "on guest: %s", str(not_enable_flags))
                logging.info("Check main instruction sets.")

                install_path = "/tmp"
                install_cpuflags_test_on_vm(self.vm, install_path)

                Flags = check_cpuflags_work(self.vm, install_path,
                                            flags.all_possible_guest_flags)
                logging.info("Woking CPU flags: %s", str(Flags[0]))
                logging.info("Not working CPU flags: %s", str(Flags[1]))
                logging.warning("Flags works even if not deffined on guest cpu "
                                "flags: %s", str(Flags[0] - guest_flags))
                logging.warning("Not tested CPU flags: %s", str(Flags[2]))

                if Flags[1] & guest_flags:
                    raise error.TestFail("Some flags do not work: %s" %
                                         (str(Flags[1])))


        # 3) fail boot unsupported flags
        class test_fail_boot_with_host_unsupported_flags(Subtest):
            @subtest_nocleanup
            def test(self, cpu_model, extra_flags):
                #This is virtual cpu flags which are supported by
                #qemu but no with host cpu.
                flags = HgFlags(cpu_model, extra_flags)

                logging.debug("Unsupported flags %s.",
                              str(flags.host_all_unsupported_flags))
                cpuf_model = cpu_model + ",enforce"

                # Add unsupported flags.
                for fadd in flags.host_all_unsupported_flags:
                    cpuf_model += ",+" + fadd

                cmd = qemu_binary + " -cpu " + cpuf_model
                out = None
                try:
                    try:
                        out = utils.run(cmd, timeout=5, ignore_status=True).stderr
                    except error.CmdError:
                        logging.error("Host boot with unsupported flag")
                finally:
                    uns_re = re.compile("^warning:.*flag '(.+)'", re.MULTILINE)
                    warn_flags = set(map(virt_utils.Flag, uns_re.findall(out)))
                    fwarn_flags = flags.host_all_unsupported_flags - warn_flags
                    if fwarn_flags:
                        raise error.TestFail("Qemu did not warn the use of "
                                             "flags %s" % str(fwarn_flags))
        for cpu_model in cpu_models:
            try:
                (cpu_model, extra_flags) = cpu_model.split(":")
                extra_flags = set(map(virt_utils.Flag, extra_flags.split(",")))
            except ValueError:
                cpu_model = cpu_model
                extra_flags = set([])
            test_fail_boot_with_host_unsupported_flags(cpu_model, extra_flags)
            test_boot_cpu_model(cpu_model)
            test_boot_cpu_model_and_additional_flags(cpu_model, extra_flags)


    def test_stress_guest():
        """
        4) fail boot unsupported flags
        5) check guest flags under load cpu, system (dd)
        6) online/offline CPU
        """
        cpu_models = params.get("cpu_models","").split()
        if not cpu_models:
            cpu_models = get_cpu_models()
        logging.debug("CPU models found: %s", str(cpu_models))

        # 4) check guest flags under load cpu, stress and system (dd)
        class test_boot_guest_and_try_flags_under_load(test_temp):
            def test(self, cpu_model, extra_flags):
                logging.info("Check guest working cpuflags under load "
                             "cpu and stress and system (dd)")

                flags = HgFlags(cpu_model, extra_flags)

                logging.debug("Cpu mode flags %s.",
                              str(flags.quest_cpu_model_flags))
                logging.debug("Added flags %s.",
                              str(flags.cpumodel_unsupport_flags))
                cpuf_model = cpu_model

                # Add unsupported flags.
                for fadd in flags.cpumodel_unsupport_flags:
                    cpuf_model += ",+" + fadd

                for fdel in flags.host_unsupported_flags:
                    cpuf_model += ",-" + fdel

                (self.vm, _) = start_guest_with_cpuflags(cpuf_model, smp)

                if (not run_stress(self.vm, 60, flags.guest_flags)):
                    raise error.TestFail("Stress test ended before"
                                         " end of test.")

            def clean(self):
                logging.info("cleanup")
                self.vm.destroy(gracefully=False)


        # 5) Online/offline CPU
        class test_online_offline_guest_CPUs(test_temp):
            def test(self, cpu_model, extra_flags):
                logging.debug("Run tests with cpu model %s.", (cpu_model))
                flags = HgFlags(cpu_model, extra_flags)

                (self.vm, session) = start_guest_with_cpuflags(cpu_model, smp)

                def encap(timeout):
                    random.seed()
                    begin = time.time()
                    end = begin
                    if smp > 1:
                        while end - begin < 60:
                            cpu = random.randint(1, smp - 1)
                            if random.randint(0, 1):
                                disable_cpu(session, cpu, True)
                            else:
                                disable_cpu(session, cpu, False)
                            end = time.time()
                        return True
                    else:
                        logging.warning("For this test is necessary smp > 1.")
                        return False
                timeout = 60

                test_flags = flags.guest_flags
                if all_host_supported_flags == "yes":
                    test_flags = flags.all_possible_guest_flags

                result = virt_utils.parallel([(encap, [timeout]),
                                             (run_stress, [self.vm, timeout,
                                                          test_flags])])
                if not (result[0] and result[1]):
                    raise error.TestFail("Stress tests failed before"
                                         " end of testing.")


        # 6) migration test
        class test_migration_with_additional_flags(test_temp):
            def test(self, cpu_model, extra_flags):
                flags = HgFlags(cpu_model, extra_flags)

                logging.debug("Cpu mode flags %s.",
                              str(flags.quest_cpu_model_flags))
                logging.debug("Added flags %s.",
                              str(flags.cpumodel_unsupport_flags))
                cpuf_model = cpu_model

                # Add unsupported flags.
                for fadd in flags.cpumodel_unsupport_flags:
                    cpuf_model += ",+" + fadd

                for fdel in flags.host_unsupported_flags:
                    cpuf_model += ",-" + fdel

                (self.vm, _) = start_guest_with_cpuflags(cpuf_model, smp)

                install_path = "/tmp"
                install_cpuflags_test_on_vm(self.vm, install_path)
                flags = check_cpuflags_work(self.vm, install_path,
                                            flags.guest_flags)
                dd_session = self.vm.wait_for_login()
                stress_session = self.vm.wait_for_login()

                dd_session.sendline("nohup dd if=/dev/[svh]da of=/tmp/"
                                    "stressblock bs=10MB count=100 &")
                cmd = ("nohup %s/cpuflags-test --stress  %s%s &" %
                       (os.path.join(install_path, "test_cpu_flags"), smp,
                       virt_utils.kvm_flags_to_stresstests(flags[0])))
                stress_session.sendline(cmd)

                time.sleep(5)

                self.vm.monitor.migrate_set_speed(mig_speed)
                self.vm.migrate(mig_timeout, mig_protocol, offline=False)

                time.sleep(5)

                #If cpuflags-test hang up during migration test raise exception
                try:
                    stress_session.cmd('killall cpuflags-test')
                except aexpect.ShellCmdError:
                    raise error.TestFail("Cpuflags-test should work after"
                                         " migration.")


        for cpu_model in cpu_models:
            try:
                (cpu_model, extra_flags) = cpu_model.split(":")
                extra_flags = set(map(virt_utils.Flag, extra_flags.split(",")))
            except ValueError:
                cpu_model = cpu_model
                extra_flags = set([])
            test_boot_guest_and_try_flags_under_load(cpu_model, extra_flags)
            test_online_offline_guest_CPUs(cpu_model, extra_flags)
            test_migration_with_additional_flags(cpu_model, extra_flags)


    try:
        locals()[params.get("test_type")]()
    finally:
        logging.info("RESULTS:")
        for line in Subtest.get_text_result().splitlines():
            logging.info(line)

    if Subtest.has_failed():
        raise error.TestFail("Some subtests failed")
