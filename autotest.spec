%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

## filter_from_requires |client/tools/boottool$|d
%{?filter_setup:
%filter_requires_in %{python_sitelib}/autotest/client/tools/boottool$
%filter_setup
}

%bcond_with gwt

Name: autotest
Version: 0.13.1
Release: 1%{?dist}
Summary: Framework for fully automated testing
Group: Applications/System
License: GPLv2 and BSD and LGPLv2.1+
# All content is GPLv2 unless otherwise stated.
# Part of frontend/afe/feeds/feed.py is BSD licensed code from Django
# frontend/afe/json_rpc is a heavily modified fork of the dead
# http://json-rpc.org/wiki/python-json-rpc which is LGPLv2.1+
URL: http://autotest.github.com/
BuildArch: noarch
# The source is pulled from upstream git branch. Use the following commands to generate the tarball:
#  git clone git://github.com/autotest/autotest.git autotest-notests-%{version}
#  cd autotest-notests-%{version} && git checkout ${version} && cd ..
#  tar -cjvf autotest-notests-%{version}.tar.bz2  --exclude=tests --exclude=.git --exclude=.gitignore autotest-notests-%{version}
Source0: %{name}.tar.bz2
# or use direct link
#Source0: https://github.com/downloads/%{name}/%{name}/%{name}-notests-%{version}.tar.bz2
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
# Not sent upstream, specific to Fedora and/or FHS guidelines
Patch1: 0001-Autotest-namespace-setup-Allow-searching-on-sys.path.patch
Patch2: 0002-Convert-entry-points-to-use-system-wide-autotest-lib.patch
Patch3: 0003-Global-config-Make-autotest-look-for-the-global-conf.patch
Patch4: 0004-Make-it-possible-to-specify-a-server-log-dir-on-glob.patch
Patch5: 0005-Make-it-possible-to-use-another-directory-for-pid-fi.patch
Patch6: 0006-Use-system-gwt-install.patch
Patch7: 0007-Main-apache-configuration-adjustments-for-Fedora-bas.patch
Patch8: 0008-Add-README-for-deployment-on-Fedora.patch
Patch9: 0009-Stop-the-build_externals-script-from-being-called-at.patch
Patch10: 0010-Convert-entry-points-to-use-system-wide-autotest-lib.patch
Patch11: 0011-Change-paths-according-to-the-new-Fedora-packaging.patch
Patch12: 0012-Use-the-conmux-package-instead-of-the-one-provided-b.patch
Patch13: 0013-Replace-old-autotest-dir-with-the-new-one-in-init-sc.patch
Patch14: 0014-Replace-results-path-with-the-new-one-in-apache-conf.patch
Patch15: 0015-install-Initial-cut-at-installing-files-using-setup..patch

# The old client package was a subpackage and has been replaced by the base
# package
Obsoletes: %{name}-client

Requires: python >= 2.4
BuildRequires: python >= 2.4
%if %{with gwt}
BuildRequires: gwt-devel >= 2.3.0
BuildRequires: java-openjdk
%endif
# EL5 doesn't have a 'git-core'
%if 0%{?rhel} == 5
BuildRequires: git
%endif
%if 0%{?fedora} >= 9
BuildRequires: git-core
%endif
# Packages needed during %post and %pre processing
Requires(post): openssh
Requires(pre): shadow-utils
# Ensure scp, rsync and sshd are available
Requires: openssh-clients
Requires: openssh-server
Requires: rsync


%description
Autotest is a framework for fully automated testing. It is designed primarily
to test the Linux kernel, though it is useful for many other functions such as
qualifying new hardware. It's an open-source project under the GPL and is used
and developed by a number of organizations, including Google, IBM, and many
others.

The autotest package provides the client harness capable of running autotest
jobs on a single system.


%package server
Summary: Server test harness and front-end for autotest
Group: Applications/System
Requires: %{name} = %{version}-%{release}
Requires: Django >= 1.1
Requires: gnuplot
Requires: httpd
Requires: mod_python
Requires: MySQL-python
Requires: numpy
Requires: python-atfork
Requires: python-crypto
Requires: python-imaging
Requires: python-matplotlib
Requires: python-paramiko
Requires: python-simplejson
Requires: python-setuptools
Requires: python-httplib2
Requires: gzip, bzip2, unzip
%if 0%{?fedora} >= 10 || 0%{?rhel} >= 6
Requires(post): policycoreutils-python
%else
Requires(post): policycoreutils
%endif
# This is for /sbin/service
Requires(preun): initscripts
Requires(postun): initscripts
# This is for /sbin/chkconfig
Requires(post): chkconfig
Requires(preun): chkconfig
# Include systemd-units for Fedora 15 and newer
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
BuildRequires: systemd-units
%endif


%description server
Autotest is a framework for fully automated testing. It is designed primarily
to test the Linux kernel, though it is useful for many other functions such as
qualifying new hardware. It's an open-source project under the GPL and is used
and developed by a number of organizations, including Google, IBM, and many
others.

The autotest-server package provides the server harness capable of running
autotest jobs on a single system.


%prep
#%setup -q -n %{name}-notests-%{version}
%setup -q -n %{name}

# Since the patchset is kind of big, it is reasonable to use git to apply them,
# once those patches are upstream, git will be no longer used to apply them

# Use git to apply patches, so that permission changes work
git init
# Setup a committer
if [ -z "$GIT_COMMITTER_NAME" ]; then
    git config user.email "test@lists.fedoraproject.org"
    git config user.name "Fedora Quality Assurance"
fi
git add .
git commit -a -q -m 'Initial commit for %{version}'
# The below works in Fedora, but not yet in EL5
#git am -p1 %{patches}
# EL 5 version, stolen from Xorg, hold your nose
git am -p1 $(awk '/^Patch.*:/ { print "%{_sourcedir}/"$2 }' %{_specdir}/%{name}.spec)


%build
python setup.py build
# GWT is not packaged in Fedora, build web frontend that uses it only when --with gwt
%if %{with gwt}
python utils/compile_gwt_clients.py -c 'autotest.EmbeddedSpreadsheetClient autotest.AfeClient autotest.TkoClient autotest.EmbeddedTkoClient'
%endif


%install
rm -rf %{buildroot}
python setup.py install --root %{buildroot} --skip-build

#setup the Fedora site specific stuff
mkdir -p %{buildroot}%{_sharedstatedir}/autotest/.ssh
touch %{buildroot}%{_sharedstatedir}/autotest/.ssh/id_rsa
touch %{buildroot}%{_sharedstatedir}/autotest/.ssh/id_rsa.pub
mkdir -p %{buildroot}%{_localstatedir}/www/autotest
mkdir -p %{buildroot}%{_localstatedir}/log/autotest
mkdir -p %{buildroot}%{_localstatedir}/run/autotest
mkdir -p %{buildroot}%{_sharedstatedir}/autotest/packages
mkdir -p %{buildroot}%{_sharedstatedir}/autotest/results
mkdir -p %{buildroot}%{_sysconfdir}/httpd/autotest.d
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d
cp -a apache/conf/* %{buildroot}%{_sysconfdir}/httpd/autotest.d/
rm %{buildroot}%{_sysconfdir}/httpd/autotest.d/apache-conf
rm %{buildroot}%{_sysconfdir}/httpd/autotest.d/site-directives
rm %{buildroot}%{_sysconfdir}/httpd/autotest.d/all-directives
cp -a apache/apache-conf %{buildroot}%{_sysconfdir}/httpd/conf.d/autotest.conf
mkdir -p %{buildroot}%{_sysconfdir}/autotest
cp -a global_config.ini shadow_config.ini %{buildroot}%{_sysconfdir}/autotest/
mkdir -p %{buildroot}%{_sysconfdir}/rc.d/init.d
cp -a utils/autotest-rh.init %{buildroot}%{_sysconfdir}/rc.d/init.d/autotestd
rm %{buildroot}%{python_sitelib}/autotest-0.0.0-py2.6.egg-info

#hack time
mv %{buildroot}/usr/usr/share %{buildroot}/usr/share

%clean
rm -rf %{buildroot}


%pre
getent group autotest >/dev/null || groupadd -r autotest
getent passwd autotest >/dev/null || \
useradd -r -g autotest -d %{_sharedstatedir}/autotest -s /bin/bash \
-c "User account for the autotest harness" autotest
exit 0


%post
# install
if [ "$1" -eq 1 ] ; then
    su -c "ssh-keygen -q -t rsa -N '' -f %{_sharedstatedir}/autotest/.ssh/id_rsa" - autotest || exit 0
fi


%post server
# install
if [ "$1" -ge 1 ]; then
    semanage fcontext -a -t bin_t '%{python_sitelib}/autotest/tko(/.*cgi)?'
    restorecon %{python_sitelib}/autotest/tko/*
    /sbin/chkconfig --add autotestd >/dev/null 2>&1 || :
fi


%postun server
if [ "$1" -ge 1 ]; then
    /sbin/service autotestd condrestart >/dev/null 2>&1 || :
fi


%preun server
# uninstall
if [ $1 -eq 0 ]; then
    /sbin/service autotestd stop >/dev/null 2>&1
    /sbin/chkconfig --del autotestd >/dev/null 2>&1 || :
    /bin/systemctl disable autotestd.service >/dev/null 2>&1 || :
fi


%files
%defattr(-,autotest,autotest,-)
%doc %attr(-,root,root) DCO LGPL_LICENSE LICENSE CODING_STYLE README.rst README.fedora documentation/*
%dir %{python_sitelib}/autotest
%dir %{_sharedstatedir}/autotest
%dir %{_sharedstatedir}/autotest/.ssh
%dir /usr/share/autotest
%ghost %{_sharedstatedir}/autotest/.ssh/*
%{python_sitelib}/autotest/client
%{python_sitelib}/autotest/__init__.py*
%{python_sitelib}/autotest/common.py*
/usr/share/autotest/client/*
%{_bindir}/autotest
%{_bindir}/autotest-local
%{_bindir}/autotest_client

%files server
%defattr(-,autotest,autotest,-)
%dir %{_sysconfdir}/httpd/autotest.d
%dir %{_sysconfdir}/autotest
%{python_sitelib}/autotest/cli
%{python_sitelib}/autotest/database
%{python_sitelib}/autotest/frontend
%{python_sitelib}/autotest/mirror
%{python_sitelib}/autotest/scheduler
%{python_sitelib}/autotest/server
%{python_sitelib}/autotest/utils
%{python_sitelib}/autotest/tko
/usr/share/autotest/cli
/usr/share/autotest/mirror
/usr/share/autotest/tko
/usr/share/autotest/utils
%{_localstatedir}/www/autotest
%{_localstatedir}/log/autotest
%{_localstatedir}/run/autotest
%{_sharedstatedir}/autotest/packages
%{_sharedstatedir}/autotest/results
%{_bindir}/atest
%{_bindir}/atest_migrate_host
%{_bindir}/autoserv
%{_bindir}/autotestd
%{_bindir}/autotestd_monitor
%{_bindir}/autotest-remote
%{_bindir}/autotest-manage-rpc-server
%{_bindir}/autotest-rpc-client
%{_bindir}/autotest-upgrade-db
%{_sbindir}/monitor_db_babysitter
# Only include the following if support for build_externals is enabled (see
# patch5)
# %{python_sitelib}/autotest/ExternalSource
# %{python_sitelib}/autotest/site-packages

# Include systemd service file on Fedora 15 and newer
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%{_unitdir}/autotestd.service
%else
%{_sysconfdir}/rc.d/init.d/autotestd
%endif
%config(noreplace) %{_sysconfdir}/autotest/global_config.ini
%config(noreplace) %{_sysconfdir}/autotest/shadow_config.ini
%config(noreplace) %attr(-,root,root) %{_sysconfdir}/httpd/autotest.d/*
%config(noreplace) %attr(-,root,root) %{_sysconfdir}/httpd/conf.d/autotest.conf


%changelog
* Fri Dec 16 2011 Martin Krizek <mkrizek@redhat.com> - 0.13.1-1
- Update to 0.13.1 release
- Add gwt conditional build
- Change Group
- Change logs/pids path
- Change config files path
- Change results path
- Change apache root path
- Change autotest homedir
- Change source git repo to upstream
- cli/,client/,database/,frontend/,mirror/,scheduler/,server/,utils/,tko/ moved to site-packages
- packages/ moved to /var/lib/autotest
- README files renamed to README.$foo
- Remove conmux directory (the conmux package is used)

* Wed Jul 06 2011 James Laska <jlaska@redhat.com> - 0.13.0-3
- Updated build_externals disable patch

* Thu Jun 30 2011 James Laska <jlaska@redhat.com> - 0.13.0-2
- Updated s/local/share/ patch

* Thu Jun 23 2011 James Laska <jlaska@redhat.com> - 0.13.0-1
- Update to 0.13.0 release

* Mon Jun 13 2011 James Laska <jlaska@redhat.com> - 0.13.0-0.3.20110607
- Correct policycoreutils-python requires

* Tue Jun 07 2011 James Laska <jlaska@redhat.com> - 0.13.0-0.2.20110607
- Adjust autotestd.service to ensure proper Group= is used
- Additional autotest-server requirements added

* Tue May 31 2011 James Laska <jlaska@redhat.com> - 0.13.0-0.1.20110531
- Package pre-0.13.0 release
- Updated and reduced local patchset
- Remove client/deps and client/profilers/* from package
- Include autotestd.service systemd file
- frontend/settings.py - Disable frontend.planner until complete

* Wed Apr 13 2011 James Laska <jlaska@redhat.com> - 0.12.0-4
- Add filter_requires_in for boottool (perl-Linux-Bootloader)
- Patch for proper systemd support (changeset 5300)

* Tue Jan 25 2011 James Laska <jlaska@redhat.com> - 0.12.0-3
- Add %requires for rsync, openssh-{clients,server}
- Add BuildRequires on python

* Thu Jan 20 2011 James Laska <jlaska@redhat.com> - 0.12.0-2
- Change %requires to java-openjdk

* Tue Jun 22 2010 James Laska <jlaska@redhat.com> - 0.12.0-1
- New upstream release autotest-0.12.0
- Updated patchset
- Combine autotest and autotest-client
- Rename initscript to autotestd
- Add conmux directory, required even if conmux isn't used

* Thu Nov 19 2009 James Laska <jlaska@redhat.com> - 0.11.0-4
- Updated Patch4 (0004-Change-usr-local-to-usr-share.patch) so that
  global_config.ini also uses /usr/share/autotest

* Fri Nov 13 2009 James Laska <jlaska@redhat.com> - 0.11.0-3
- Moved autotest user creation into autotest-client package

* Tue Oct 30 2009 James Laska <jlaska@redhat.com> - 0.11.0-2
- Updated patch2 - new_tko/tko/graphing.py uses simplejson also
- Updated patch3 - correct http log paths
- Updated patch5 - background patch to work against monitor_db_babysitter
- Updated patch7 - RH style initscript updated to use monitor_db_babysitter
- Add patch9 to correct new_tko models.py issue with older django

* Tue Aug 25 2009 Jesse Keating <jkeating@redhat.com> - 0.11.0-1
- Update for 0.11
- Drop unneeded patches
- Re-order patches with new upstream code set

* Fri Jul 31 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-8
- Fix AFE loading with the missing site_rpc_interface

* Tue Jul 14 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-7
- Remove the all-directives file, it is now redundant

* Wed Jul 08 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-6
- Move apache config files into /etc/
- Drop some unneeded files
- Set permissions accordingly
- Remove unneeded #! and add a missing one

* Tue Jul 07 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-5
- Make README.fedora a patch to the source code
- Make initscript a patch to the source code
- re-work background patch to be git compliant
- Remove macros for install
- Drop release level requirement on autotest-client.  Version is good enough

* Mon Jun 29 2009 James Laska <jlaska@redhat.com> - 0.10.0-4
- Add README.fedora
- Add autotest initscript
- Make scheduler/monitor_db.py executable

* Sat Jun 27 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-3
- Move ssh key into autotest home .ssh/ and name it generically
- Ghost the ssh dir
- More selinux fixes

* Fri Jun 26 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-2
- Patch path issues
- Set a shell for the autotest user to allow running init script
- Fix ssh key generation to run as autotest user
- SELinux fixes

* Tue Jun 16 2009 Jesse Keating <jkeating@redhat.com> - 0.10.0-1
- Initial attempt at packaging, adding to start from Lucas Meneghel Rodrigues
  <lmr@redhat.com>

