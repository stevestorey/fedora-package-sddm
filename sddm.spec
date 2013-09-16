%global _hardened_build 1
%global sddm_commit 50ca5b20354b6d338ce8836a613af19cedb1dca2

Name:           sddm
Version:        0.2.0
Release:        0.9.20130821git%(echo %{sddm_commit} | cut -c-8)%{?dist}
License:        GPLv2+
Summary:        QML based X11 desktop manager

Url:            https://github.com/sddm/sddm
Source0:        https://github.com/MartinBriza/sddm/archive/%{sddm_commit}.tar.gz
# Originally kdm config, shamelessly stolen from gdm
Source1:        sddm.pam
# We need to ship our own service file to handle Fedora-specific cases
Source2:        sddm.service

# Patch setting a better order of the xsessions and hiding the custom one
Patch2:         sddm-git.e707e229-session-list.patch

Provides: service(graphical-login) = sddm

BuildRequires:  cmake
BuildRequires:  systemd
BuildRequires:  upower-devel
BuildRequires:  pam-devel
BuildRequires:  libxcb-devel
BuildRequires:  qt-devel
BuildRequires:  pkgconfig

Requires: kde-settings-sddm
Requires: pam
Requires: systemd
Requires: xorg-x11-server-Xorg
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
SDDM is a modern display manager for X11 aiming to be fast, simple and
beautiful. It uses modern technologies like QtQuick, which in turn gives the
designer the ability to create smooth, animated user interfaces.

%prep
%setup -q -n %{name}-%{sddm_commit}
%patch2 -p1 -b .session-list

%build
mkdir -p %{_target_platform}
# get rid of the architecture flag
sed -i "s/-march=native//" CMakeLists.txt
pushd %{_target_platform}
%{cmake} ..
popd

make %{?_smp_mflags} -C %{_target_platform}

%install
make install/fast DESTDIR=%{buildroot} -C %{_target_platform}
install -Dpm 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pam.d/sddm
install -Dpm 644 %{SOURCE2} %{buildroot}%{_unitdir}/sddm.service
# contained in kde-settings
rm %{buildroot}%{_sysconfdir}/sddm.conf

%post
%systemd_post sddm.service

%preun
%systemd_preun sddm.service

%postun
%systemd_postun sddm.service 

%files
%doc COPYING README.md CONTRIBUTORS
%config(noreplace)   %{_sysconfdir}/pam.d/sddm
%config(noreplace)   %{_sysconfdir}/dbus-1/system.d/org.freedesktop.DisplayManager.conf
%{_bindir}/sddm
%{_bindir}/sddm-greeter
%{_unitdir}/sddm.service
%{_libdir}/qt4/imports/SddmComponents
%{_datadir}/apps/sddm/faces/*
%{_datadir}/apps/sddm/flags/*
%{_datadir}/apps/sddm/scripts/*
%{_datadir}/apps/sddm/sddm.conf.sample
%{_datadir}/apps/sddm/themes/*
%{_datadir}/apps/sddm/translations/*

%changelog
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
