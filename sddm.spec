%global _hardened_build 1

Name:           sddm
Version:        0.14.0
Release:        13%{?dist}
# code GPLv2+, fedora theme CC-BY-SA
License:        GPLv2+ and CC-BY-SA
Summary:        QML based X11 desktop manager

Url:            https://github.com/sddm/sddm
Source0:        https://github.com/sddm/sddm/archive/v%{version}.tar.gz

## upstream patches (in lookaside cache)
#BuildRequires: git-core
Patch1: 0001-Fix-display-of-user-avatars.-684.patch
Patch2: 0002-Remove-quotes-from-ServerArguments-696.patch
Patch3: 0003-Add-a-config-option-to-enable-high-DPI-scaling-701.patch
Patch35: 0035-UserModel-Check-for-duplicates-from-getpwent.patch

## upstreamable patches
# Fixes RHBZ #1392654
Patch54: https://github.com/sddm/sddm/pull/735.patch

## downstream patches
Patch101:       sddm-0.14.0-fedora_config.patch 

Patch102:       0001-Port-from-xauth-to-libXau.patch

# Shamelessly stolen from gdm
Source11:       sddm.pam
# Shamelessly stolen from gdm
Source12:       sddm-autologin.pam
# systemd tmpfiles support for /var/run/sddm
Source13:       tmpfiles-sddm.conf
# sample sddm.conf generated with sddm --example-config, and entries commented-out
Source14: sddm.conf
# README.scripts
Source15: README.scripts

# fedora theme files
Source21:       fedora-Main.qml
Source22:       fedora-metadata.desktop
Source23:       fedora-theme.conf
Source24:       angle-down.png

Provides: service(graphical-login) = sddm

BuildRequires:  cmake >= 2.8.8
BuildRequires:  extra-cmake-modules
BuildRequires:  libxcb-devel
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  python-docutils
BuildRequires:  qt5-qtbase-devel >= 5.6
BuildRequires:  qt5-qtdeclarative-devel >= 5.6
BuildRequires:  qt5-qttools-devel >= 5.6
# verify presence to pull defaults from /etc/login.defs
BuildRequires:  shadow-utils
BuildRequires:  systemd

Obsoletes: kde-settings-sddm < 20-5

%if 0%{?fedora}
# for /usr/share/backgrounds/default.png
Requires: desktop-backgrounds-compat
# for /usr/share/pixmaps/system-logo-white.png
Requires: system-logos
%endif
Requires: systemd
Requires: xorg-x11-xinit
%ifnarch s390 s390x
Requires: xorg-x11-server-Xorg
%endif
%{?systemd_requires}

Requires(pre): shadow-utils

%description
SDDM is a modern display manager for X11 aiming to be fast, simple and
beautiful. It uses modern technologies like QtQuick, which in turn gives the
designer the ability to create smooth, animated user interfaces.

%package themes
Summary: SDDM Themes
# for upgrade path
Obsoletes: sddm < 0.2.0-0.12
Requires: %{name} = %{version}-%{release}
BuildArch: noarch
%description themes
A collection of sddm themes, including: circles, elarun, maldives, maui.


%prep
%setup -q

%patch1 -p1 -b .0001
%patch2 -p1 -b .0002
%patch3 -p1 -b .0003
%patch35 -p1 -b .0035

%patch54 -p1 -b .0054

%patch101 -p1 -b .fedora_config
%patch102 -p1 -b .libxau


%build
mkdir %{_target_platform}
pushd %{_target_platform}
%{cmake} .. \
  -DBUILD_MAN_PAGES:BOOL=ON \
  -DCMAKE_BUILD_TYPE:STRING="Release" \
  -DENABLE_JOURNALD:BOOL=ON \
  -DSESSION_COMMAND:PATH=/etc/X11/xinit/Xsession \
  -DWAYLAND_SESSION_COMMAND:PATH=/etc/sddm/wayland-session
popd

make %{?_smp_mflags} -C %{_target_platform}


%install
make install/fast DESTDIR=%{buildroot} -C %{_target_platform}

install -Dpm 644 %{SOURCE11} %{buildroot}%{_sysconfdir}/pam.d/sddm
install -Dpm 644 %{SOURCE12} %{buildroot}%{_sysconfdir}/pam.d/sddm-autologin
install -Dpm 644 %{SOURCE13} %{buildroot}%{_tmpfilesdir}/sddm.conf
install -Dpm 644 %{SOURCE14} %{buildroot}%{_sysconfdir}/sddm.conf
install -Dpm 644 %{SOURCE15} %{buildroot}%{_datadir}/sddm/scripts/README.scripts
mkdir -p %{buildroot}%{_localstatedir}/run/sddm
mkdir -p %{buildroot}%{_localstatedir}/lib/sddm
mkdir -p %{buildroot}%{_sysconfdir}/sddm/
cp -a %{buildroot}%{_datadir}/sddm/scripts/* \
      %{buildroot}%{_sysconfdir}/sddm/
# we're using /etc/X11/xinit/Xsession (by default) instead
rm -fv %{buildroot}%{_sysconfdir}/sddm/Xsession

# install fedora theme
%if 0%{?fedora}
install -Dpm 644 %{SOURCE21} %{buildroot}%{_datadir}/sddm/themes/02-fedora/Main.qml
install -Dpm 644 %{SOURCE22} %{buildroot}%{_datadir}/sddm/themes/02-fedora/metadata.desktop
install -Dpm 644 %{SOURCE23} %{buildroot}%{_datadir}/sddm/themes/02-fedora/theme.conf
install -Dpm 644 %{SOURCE24} %{buildroot}%{_datadir}/sddm/themes/02-fedora/angle-down.png
%endif


%pre
getent group sddm >/dev/null || groupadd -r sddm
getent passwd sddm >/dev/null || \
    useradd -r -g sddm -d %{_localstatedir}/lib/sddm -s /sbin/nologin \
    -c "Simple Desktop Display Manager" sddm
exit 0

%post
%systemd_post sddm.service
# handle incompatible configuration changes
(grep \
   -e '^Current=fedora$' \
   -e '^\[XDisplay\]$' \
   -e '^\[WaylandDisplay\]$' \
   %{_sysconfdir}/sddm.conf > /dev/null && \
 sed -i.rpmsave \
   -e 's|^Current=fedora$|#Current=01-breeze-fedora|' \
   -e 's|^\[XDisplay\]$|\[X11\]|' \
   -e 's|^\[WaylandDisplay\]$|\[Wayland\]|' \
   %{_sysconfdir}/sddm.conf
) ||:


%preun
%systemd_preun sddm.service

%postun
%systemd_postun sddm.service

%files
%{!?_licensedir:%global license %%doc}
%license LICENSE 
%doc README.md CONTRIBUTORS
%dir %{_sysconfdir}/sddm/
%config(noreplace)   %{_sysconfdir}/sddm/*
%config(noreplace)   %{_sysconfdir}/sddm.conf
%config(noreplace)   %{_sysconfdir}/pam.d/sddm
%config(noreplace)   %{_sysconfdir}/pam.d/sddm-autologin
%config(noreplace)   %{_sysconfdir}/pam.d/sddm-greeter
# it's under /etc, sure, but it's not a config file -- rex
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.DisplayManager.conf
%{_bindir}/sddm
%{_bindir}/sddm-greeter
%{_libexecdir}/sddm-helper
%{_tmpfilesdir}/sddm.conf
%attr(0711, root, sddm) %dir %{_localstatedir}/run/sddm
%attr(1770, sddm, sddm) %dir %{_localstatedir}/lib/sddm
%{_unitdir}/sddm.service
%{_qt5_archdatadir}/qml/SddmComponents/
%dir %{_datadir}/sddm
%{_datadir}/sddm/faces/
%{_datadir}/sddm/flags/
%{_datadir}/sddm/scripts/
%dir %{_datadir}/sddm/themes/
%if 0%{?fedora}
# default non-userlist fedora theme
%{_datadir}/sddm/themes/02-fedora/
%endif
# %%lang'ify ? -- rex
%{_datadir}/sddm/translations/
%{_mandir}/man1/sddm.1*
%{_mandir}/man1/sddm-greeter.1*
%{_mandir}/man5/sddm.conf.5*
%{_mandir}/man5/sddm-state.conf.5*

%post themes
# handle incompatible configuration changes
(grep \
   -e '^Current=circles$' \
   %{_sysconfdir}/sddm.conf > /dev/null && \
 sed -i.rpmsave \
   -e 's|^Current=circles$|#Current=01-breeze-fedora|' \
   %{_sysconfdir}/sddm.conf
) ||:

%files themes
%{_datadir}/sddm/themes/elarun/
%{_datadir}/sddm/themes/maldives/


%changelog
* Thu Aug 17 2017 Martin Bříza <mbriza@redhat.com> - 0.14.0-13
- Port from xauth to libXau (#1370222)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.14.0-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.14.0-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Jun 13 2017 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-10
- actually apply patch for bug #1446782

* Tue Jun 13 2017 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-9
- backport: UserModel: Check for duplicates from getpwent() (#1446782)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.14.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Jan 28 2017 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-7
- EnableHiDPI=false default

* Tue Nov 08 2016 Adam Williamson <awilliam@redhat.com> - 0.14.0-6
- backport PR #735 to fix RHBZ #1392654

* Wed Nov 02 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-5
- pull in upstream fixes

* Fri Oct 07 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-4
- sddm.conf default: Current=01-breeze-fedora

* Mon Oct 03 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-3
- drop deps used for fedora-only theme

* Mon Oct 03 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-2
- make 02-fedora theme, fedora only

* Sun Aug 28 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.14.0-1
- sddm-0.14.0
- -themes: circles theme was removed

* Fri Mar 11 2016 Rex Dieter <rdieter@fedoraproject.org> - 0.13.0-7
- pull in upstream fixes, some new features
- The desktop selection drop down list has an empty box (#1222228)
- sddm: RememberLastUser=false does not work (#1240749)

* Fri Mar 11 2016 Rex Dieter <rdieter@fedoraproject.org> 0.13.0-6
- sddm: use pam_gnome_keyring (#1317066)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.13.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Nov 16 2015 Rex Dieter <rdieter@fedoraproject.org> - 0.13.0-4
- rev sddm.conf for new defaults
- add /usr/share/sddm/scripts/README.scripts

* Sun Nov 15 2015 Rex Dieter <rdieter@fedoraproject.org> - 0.13.0-3
- merge Configuration.h into fedora_config.patch
- copy all scripts into /etc/sddm as %%config(noreplace)

* Sun Nov 15 2015 Rex Dieter <rdieter@fedoraproject.org> 0.13.0-2
- %%config(noreplace) /etc/sddm/Xsetup

* Sat Nov 07 2015 Rex Dieter <rdieter@fedoraproject.org> 0.13.0-1
- 0.13.0

* Thu Oct 29 2015 Rex Dieter <rdieter@fedoraproject.org> 0.12.0-6
- tweak DefaultPath (#1276450)

* Thu Oct 15 2015 Rex Dieter <rdieter@fedoraproject.org> 0.12.0-5
- Security fix for CVE-2015-0856 (#1271992,#1271993)

* Thu Sep 24 2015 Rex Dieter <rdieter@fedoraproject.org> 0.12.0-4
- omit 0008-Inherit-path-environment-variables-from-parent.patch pending security concerns

* Thu Sep 24 2015 Rex Dieter <rdieter@fedoraproject.org> - 0.12.0-3
- pull in upstream fixes (#1265813)
- fedora theme QML error (#1264946)

* Thu Sep 10 2015 Rex Dieter <rdieter@fedoraproject.org> 0.12.0-2
- sddm.pam: add pam_kwallet5 support

* Tue Sep 08 2015 Rex Dieter <rdieter@fedoraproject.org> 0.12.0-1
- 0.12.0

* Wed Sep 02 2015 Rex Dieter <rdieter@fedoraproject.org> 0.11.0-2
- use %%license tag

* Thu Aug 06 2015 Rex Dieter <rdieter@fedoraproject.org> - 0.11.0-1
- sddm-0.11 (#1209689), plus pull in a few post 0.11.0 upstream fixes
- Enable two fedora themes, allowing user selector as default (#1250204)

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.10.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 0.10.0-5
- Rebuilt for GCC 5 C++11 ABI change

* Thu Jan 29 2015 Dan Horák <dan[at]danny.cz> - 0.10.0-4
- don't Require Xorg server on s390(x)

* Wed Jan 21 2015 Martin Briza <mbriza@redhat.com> - 0.10.0-3
- Fixed positioning in the Fedora theme
- Resolves: #1183207

* Mon Oct 27 2014 Rex Dieter <rdieter@fedoraproject.org> - 0.10.0-2
- create/own %%{_sysconfdir}/sddm.conf, %%{_localstatedir}/lib/sddm (#1155898)
- don't mark stuff under /etc/dbus-1 %%config
- make %%{_localstatedir}/run/sddm group writable

* Thu Oct 16 2014 Martin Briza <mbriza@redhat.com> - 0.10.0-1
- Bump to 0.10.0

* Thu Oct 09 2014 Martin Briza <mbriza@redhat.com> - 0.9.0-2.20141007git6a28c29b
- Remove pam_gnome_keyring.so (temporarily) from sddm.pam to fix impossibility to log out
- Resolves: #1150283

* Tue Oct 07 2014 Martin Briza <mbriza@redhat.com> - 0.9.0-1.20141007git6a28c29b
- Bump to latest upstream git (and a new release)
- Hack around focus problem in the Fedora theme
- Compile against Qt5
- Removed upstreamed patch and files
- Resolves: #1114192 #1119777 #1123506 #1125129 #1140386 #1112841 #1128463 #1128465 #1149608 #1149628 #1148659 #1148660 #1149610 #1149629

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-0.32.20140627gitf49c2c79
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jun 27 2014 Martin Briza <mbriza@redhat.com> - 0.2.0-0.31.20140627gitf49c2c79
- Patch unitialized values in signal handler in the daemon

* Fri Jun 27 2014 Martin Briza <mbriza@redhat.com> - 0.2.0-0.30.20140627gitf49c2c79
- Bump to latest upstream, switch back to sddm project
- Drop sddm.service
- Enable manpage and journald support

* Tue Jun 24 2014 Martin Briza <mbriza@redhat.com> - 0.2.0-0.29.20140623gitdb1d7381
- Fix default config to respect the new /usr/share paths
- Fixed multiple users after autologin

* Mon Jun 23 2014 Martin Briza <mbriza@redhat.com> - 0.2.0-0.28.20140623gitdb1d7381
- Fix Requires, release

* Mon Jun 23 2014 Martin Briza <mbriza@redhat.com> - 0.2.0-0.27.20131125gitdb1d7381
- Updated to the latest upstream git
- Notable changes: Greeter runs under the sddm user, it's possible to configure display setup, different install paths in /usr/share
- Resolves: #1034414 #1035939 #1035950 #1036308 #1038548 #1045722 #1045937 #1065715 #1082229 #1007067 #1027711 #1031745 #1008951 #1016902 #1031415 #1020921

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-0.26.20131125git7a008602
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu May 01 2014 Rex Dieter <rdieter@fedoraproject.org> 0.2.0-0.25.20131125git7a008602
- update pam config (+pam_kwallet,-pam_mate_keyring)

* Mon Jan 27 2014 Adam Jackson <ajax@redhat.com> 0.2.0-0.24.20131125git7a008602
- Rebuild for new sonames in libxcb 1.10

* Mon Dec 16 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.23.20131125git7a008602
- Revert all work done on authentication, doesn't support multiple logins right now

* Mon Nov 25 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.22.20131125git7a008602
- Fix saving of last session and user

* Mon Nov 25 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.21.20131125git7a008602
- Rebase to current upstream
- Fix the theme (and improve it by a bit)
- Fix the authentication stack
- Don't touch numlock on startup
- Disabled the XDMCP server until it's accepted upstream
- Resolves: #1016902 #1028799 #1031415 #1031745 #1020921 #1008951 #1004621

* Tue Nov 05 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.20.20130914git50ca5b20
- Fix xdisplay and tty vars

* Tue Nov 05 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.19.20130914git50ca5b20
- Patch cleanup

* Tue Nov 05 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.18.20130914git50ca5b20
- Cmake magic

* Tue Nov 05 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.17.20130914git50ca5b20
- Rewritten the authentication stack to work right with PAM

* Tue Oct 15 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.16.20130914git50ca5b20
- Fixed the Fedora theme wallpaper path

* Tue Oct 15 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.15.20130914git50ca5b20
- Added XDMCP support patch
- Modified the config to reflect the added XDMCP support (disabled by default)

* Tue Oct 15 2013 Rex Dieter <rdieter@fedoraproject.org> - 0.2.0-0.14.20130914git50ca5b20
- sddm.conf: CurrentTheme=fedora

* Mon Oct 14 2013 Rex Dieter <rdieter@fedoraproject.org> - 0.2.0-0.13.20130914git50ca5b20
- include standard theme/config here, Obsoletes: kde-settings-sddm
- sddm.conf: SessionCommand=/etc/X11/xinit/Xsession

* Mon Oct 14 2013 Rex Dieter <rdieter@fedoraproject.org> - 0.2.0-0.12.20130914git50ca5b20
- -themes: Obsoletes: sddm ... for upgrade path

* Mon Oct 14 2013 Rex Dieter <rdieter@fedoraproject.org> - 0.2.0-0.11.20130914git50ca5b20
- -themes subpkg

* Sat Sep 21 2013 Rex Dieter <rdieter@fedoraproject.org> - 0.2.0-0.10.20130914git50ca5b20
- use %%_qt4_importdir, %%systemd_requires macros
- own %%_datadir/apps/sddm
- fix Release
- drop explicit Requires: pam (let rpm autodeps handle it)

* Mon Sep 16 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.9.20130914git50ca5b20
- Requires: kde-settings-sddm

* Mon Sep 16 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.8.20130914git50ca5b20
- Moved the config to the kde-settings-sddm package

* Sat Sep 14 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.7.20130914git50ca5b20
- Removed the nonfree font from the package, replaced with "Sans"
- Temporarily set my own repository as the origin to avoid having the font in the srpm
- Changing the source also brings us a few new commits and removes Patch1 for PAM

* Mon Sep 09 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.6.20130821gite707e229
- Added the patch, forgot to apply it, now it's okay

* Mon Sep 09 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.5.20130821gite707e229
- Set a better order of the X sessions selection and hidden the Custom one (#1004902)

* Mon Sep 02 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.4.20130821gite707e229
- Complete PAM conversations and end them properly when the session ends
- Ship our own systemd service file especially to provide Conflicts: getty@tty1.service

* Tue Aug 27 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.3.20130821gite707e229
- Suppress error output from missing PAMs.

* Tue Aug 27 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.2.20130821gite707e229
- Switched the pam config to the one GDM uses. Solves issues with pulseaudio and possibly more.

* Thu Aug 22 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.1.20130821gite707e229
- Fixed the package version

* Wed Aug 21 2013 Martin Briza <mbriza@redhat.com> - 0.2.0-0.130821.git.e707e229
- Imported the latest upstream git commit

* Mon Aug 19 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-7
- Set the build to be hardened

* Tue Aug 06 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-6
- Added mate-keyring to PAM config (#993397)

* Mon Jul 22 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-5
- Store xauth in /var/run/sddm

* Mon Jul 22 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-4
- Added the documentation bits

* Thu Jul 18 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-3
- Changed the source package to tar.gz
- Config files are now noreplace
- Buildrequires -systemd-devel +systemd +cmake

* Tue Jul 16 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-2
- Removed unneeded BuildRequires
- Fixed systemd scriptlets
- Fixed release
- Simplified setup
- Added Requires needed for basic function
- Added Provides for graphical login

* Thu Jul 04 2013 Martin Briza <mbriza@redhat.com> - 0.1.0-1
- Initial build
