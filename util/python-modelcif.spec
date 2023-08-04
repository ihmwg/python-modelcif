Name:          python3-modelcif
License:       MIT
Group:         Applications/Engineering
Version:       0.8
Release:       1%{?dist}
Summary:       Package for handling ModelCIF mmCIF and BinaryCIF files
Packager:      Ben Webb <ben@salilab.org>
URL:           https://pypi.python.org/pypi/modelcif
Source:        modelcif-%{version}.tar.gz
BuildRequires: python3-devel, python3-setuptools, python3-ihm >= 0.34
Requires:      python3-ihm >= 0.34
BuildArch:     noarch

%description
This is a Python package to assist in handling mmCIF and BinaryCIF files
compliant with the ModelCIF extension. It works with Python 2.7 or Python 3.

%prep
%setup -n modelcif-%{version}

%build
%{__python3} setup.py install --root=${RPM_BUILD_ROOT} --record=INSTALLED_FILES

%check
%{__python3} setup.py test

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
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
