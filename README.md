[![docs](https://readthedocs.org/projects/python-ma/badge/)](https://python-ma.readthedocs.org/)
[![Linux Build Status](https://github.com/ihmwg/python-ma/workflows/build/badge.svg)](https://github.com/ihmwg/python-ma/actions?query=workflow%3Abuild)
[![Windows Build Status](https://ci.appveyor.com/api/projects/status/5o28oe477ii8ur4h?svg=true)](https://ci.appveyor.com/project/benmwebb/python-ma)
[![codecov](https://codecov.io/gh/ihmwg/python-ma/branch/main/graph/badge.svg)](https://codecov.io/gh/ihmwg/python-ma)

This is a Python package to assist in handling [mmCIF](http://mmcif.wwpdb.org/)
and [BinaryCIF](https://github.com/dsehnal/BinaryCIF) files compliant with the
[Model Archive (MA)](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Index/)
extension. It works with Python 2.7 or Python 3.

Please [see the documentation](https://python-ma.readthedocs.org/)
or some
[worked examples](https://github.com/ihmwg/python-ma/tree/main/examples)
for more details.

# Installation

This module is still a work in progress and currently works only with the
latest git HEAD of the [python-ihm](https://github.com/ihmwg/python-ihm)
module. To use, first build and install python-ihm. Then, build with

```
python setup.py build
python setup.py install
```

If you want to read or write [BinaryCIF](https://github.com/dsehnal/BinaryCIF)
files, you will also need the
Python [msgpack](https://github.com/msgpack/msgpack-python) package.

# Testing

There are a number of testcases in the `test` directory. Each one can be run
like a normal Python script to test the library. They can also be all run at
once using [nose](https://nose.readthedocs.io/en/latest/)
or [pytest](https://docs.pytest.org/en/latest/).
