%global _hardened_build 1
%global sddm_commit 7a008602f5f0a4ed8586ce24012983458a687d4e

Name:           sddm
Version:        0.2.0
Release:        0.25.20131125git%(echo %{sddm_commit} | cut -c-8)%{?dist}
# code GPLv2+, fedora theme CC-BY-SA
License:        GPLv2+ and CC-BY-SA
Summary:        QML based X11 desktop manager

Url:            https://github.com/sddm/sddm
Source0:        https://github.com/MartinBriza/sddm/archive/%{sddm_commit}.tar.gz

# fedora standard sddm.conf
Source10:       sddm.conf
# Originally kdm config, shamelessly stolen from gdm
Source11:       sddm.pam
# We need to ship our own service file to handle Fedora-specific cases
Source12:       sddm.service
# systesmd tmpfiles support for /var/run/sddm
Source13:       tmpfiles-sddm.conf

# fedora theme files
Source21:       fedora-Main.qml
Source22:       fedora-metadata.desktop
Source23:       fedora-theme.conf

# Patch setting a better order of the xsessions and hiding the custom one
Patch2:         sddm-git.e707e229-session-list.patch

Patch3:         sddm-0.2.0-0.11.20130914git50ca5b20-xdmcp.patch
# Don't end the PAM session twice
Patch4:         sddm-pam_end.patch

Provides: service(graphical-login) = sddm

BuildRequires:  cmake
BuildRequires:  systemd
BuildRequires:  pam-devel
BuildRequires:  libxcb-devel
BuildRequires:  qt4-devel
BuildRequires:  pkgconfig

Obsoletes: kde-settings-sddm < 20-5

# for /usr/share/backgrounds/default.png
Requires: desktop-backgrounds-compat
# for /usr/share/pixmaps/system-logo-white.png
Requires: system-logos
Requires: systemd
Requires: xorg-x11-xinit
Requires: xorg-x11-server-Xorg
%{?systemd_requires}

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
%setup -q -n %{name}-%{sddm_commit}

%patch2 -p1 -b .session-list
%patch3 -p1 -b .xdmcp
%patch4 -p1 -b .pam_end

# get rid of the architecture flag
sed -i "s/-march=native//" CMakeLists.txt


%build
mkdir -p %{_target_platform}
pushd %{_target_platform}
%{cmake} ..
popd

make %{?_smp_mflags} -C %{_target_platform}


%install
make install/fast DESTDIR=%{buildroot} -C %{_target_platform}

install -Dpm 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/sddm.conf
install -Dpm 644 %{SOURCE11} %{buildroot}%{_sysconfdir}/pam.d/sddm
install -Dpm 644 %{SOURCE12} %{buildroot}%{_unitdir}/sddm.service
install -Dpm 644 %{SOURCE13} %{buildroot}%{_tmpfilesdir}/sddm.conf
mkdir -p %{buildroot}%{_localstatedir}/run/sddm

# install fedora theme
install -Dpm 644 %{SOURCE21} %{buildroot}%{_datadir}/apps/sddm/themes/fedora/Main.qml
install -Dpm 644 %{SOURCE22} %{buildroot}%{_datadir}/apps/sddm/themes/fedora/metadata.desktop
install -Dpm 644 %{SOURCE23} %{buildroot}%{_datadir}/apps/sddm/themes/fedora/theme.conf


%post
%systemd_post sddm.service

%preun
%systemd_preun sddm.service

%postun
%systemd_postun sddm.service 

%files
%doc COPYING README.md CONTRIBUTORS
%config %{_sysconfdir}/sddm.conf
%config(noreplace)   %{_sysconfdir}/pam.d/sddm
%config(noreplace)   %{_sysconfdir}/dbus-1/system.d/org.freedesktop.DisplayManager.conf
%{_bindir}/sddm
%{_bindir}/sddm-greeter
%{_tmpfilesdir}/sddm.conf
%attr(0711,root,root) %dir %{_localstatedir}/run/sddm
%{_unitdir}/sddm.service
%{_qt4_importdir}/SddmComponents/
# or add Requires: kde-filesystem -- rex
%dir %{_datadir}/apps
%dir %{_datadir}/apps/sddm
%{_datadir}/apps/sddm/faces/
%{_datadir}/apps/sddm/flags/
%{_datadir}/apps/sddm/scripts/
%{_datadir}/apps/sddm/sddm.conf.sample
%dir %{_datadir}/apps/sddm/themes/
# default fedora theme
%{_datadir}/apps/sddm/themes/fedora/
# %%lang'ify ? -- rex
%{_datadir}/apps/sddm/translations/

%files themes
%{_datadir}/apps/sddm/themes/circles/
%{_datadir}/apps/sddm/themes/elarun/
%{_datadir}/apps/sddm/themes/maldives/
%{_datadir}/apps/sddm/themes/maui/

%changelog
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
