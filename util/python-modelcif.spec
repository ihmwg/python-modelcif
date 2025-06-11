Name:          python3-modelcif
License:       MIT
Group:         Applications/Engineering
Version:       1.4
Release:       1%{?dist}
Summary:       Package for handling ModelCIF mmCIF and BinaryCIF files
Packager:      Ben Webb <ben@salilab.org>
URL:           https://pypi.python.org/pypi/modelcif
Source:        modelcif-%{version}.tar.gz
BuildRequires: python3-devel, python3-setuptools, python3-ihm >= 2.6
Requires:      python3-ihm >= 2.6
BuildArch:     noarch
%if 0%{?fedora} >= 42
BuildRequires: python3-pytest
%endif

%description
This is a Python package to assist in handling mmCIF and BinaryCIF files
compliant with the ModelCIF extension. It works with Python 3.6 or later.

%prep
%setup -n modelcif-%{version}

%build
%{__python3} setup.py install --root=${RPM_BUILD_ROOT} --record=INSTALLED_FILES

%check
%if 0%{?fedora} >= 42
%pytest modelcif/test.py
%else
%{__python3} setup.py test
%endif

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Wed Jun 11 2025 Ben Webb <ben@salilab.org>   1.4-1
- Update to latest upstream.

* Tue Jan 14 2025 Ben Webb <ben@salilab.org>   1.3-1
- Update to latest upstream.

* Wed Oct 23 2024 Ben Webb <ben@salilab.org>   1.2-1
- Update to latest upstream.

* Fri Sep 27 2024 Ben Webb <ben@salilab.org>   1.1-1
- Update to latest upstream.

* Thu Jun 20 2024 Ben Webb <ben@salilab.org>   1.0-1
- Update to latest upstream.

* Mon Oct 02 2023 Ben Webb <ben@salilab.org>   0.9-1
- Update to latest upstream.

* Fri Aug 04 2023 Ben Webb <ben@salilab.org>   0.8-1
- Update to latest upstream.

* Mon Jul 31 2023 Ben Webb <ben@salilab.org>   0.7-1
- Update to latest upstream.

* Tue May 10 2022 Ben Webb <ben@salilab.org>   0.5-1
- Update to latest upstream.

* Thu Apr 14 2022 Ben Webb <ben@salilab.org>   0.4-1
- Update to latest upstream.

* Mon Mar 21 2022 Ben Webb <ben@salilab.org>   0.3-1
- Update to latest upstream.

* Thu Jan 27 2022 Ben Webb <ben@salilab.org>   0.2-1
- Update to latest upstream.

* Thu Jan 27 2022 Ben Webb <ben@salilab.org>   0.1-1
- Initial package.
