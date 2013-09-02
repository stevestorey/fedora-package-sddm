%global _hardened_build 1
%global sddm_commit e707e22901049495818a9bedf71f0ba829564700

Name:           sddm
Version:        0.2.0
Release:        0.4.20130821git%(echo %{sddm_commit} | cut -c-8)%{?dist}
License:        GPLv2+
Summary:        QML based X11 desktop manager

Url:            https://github.com/sddm/sddm
Source0:        https://github.com/sddm/sddm/archive/%{sddm_commit}.tar.gz
# Originally kdm config, shamelessly stolen from gdm
Source1:        sddm.pam
# We need to ship our own service file to handle Fedora-specific cases
Source2:        sddm.service

# Upstreamed patch waiting for review, need it right now
Patch1:         0001-Store-the-PAM-handle-in-the-Authenticator-class-and-.patch

Provides: service(graphical-login) = sddm

BuildRequires:  cmake
BuildRequires:  systemd
BuildRequires:  upower-devel
BuildRequires:  pam-devel
BuildRequires:  libxcb-devel
BuildRequires:  qt-devel
BuildRequires:  pkgconfig

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
%patch1 -p1 -b .pam_close

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
# tmpfiles
sed -i "s/AuthDir=\/var\/run\/xauth/AuthDir=\/var\/run\/sddm/" %{buildroot}%{_sysconfdir}/sddm.conf
# set the first VT used to be 1
sed -i "s/^MinimumVT=[0-9]*$/MinimumVT=1/" %{buildroot}%{_sysconfdir}/sddm.conf

%post
%systemd_post sddm.service

%preun
%systemd_preun sddm.service

%postun
%systemd_postun sddm.service 

%files
%doc COPYING README.md CONTRIBUTORS
%config(noreplace)   %{_sysconfdir}/pam.d/sddm
%config(noreplace)   %{_sysconfdir}/sddm.conf
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

%changelog
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
