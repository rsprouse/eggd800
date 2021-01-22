eggd800
=======

Python utilities for configuring the EGG-D800 from Laryngograph.

Current version is alpha. API subject to change.

Requirements
============

eggd800 depends on a forked cython-hidapi library that depends on a forked
hidapi library. These forked libraries add functionality similar to
HidD\_GetInputReport().

https://github.com/rsprouse/cython-hidapi

The hidapi library is a submodule of cython-hidapi.

It can get installed with:

    git clone --recursive https://github.com/rsprouse/cython-hidapi

The --recursive parameter clones the `hidapi` submodule at the same time as the parent `cython-hidapi` repository.

Then:

    python setup.py install

Install
=======

To install, first get the code:

    git clone https://github.com/rsprouse/eggd800

Then run:

    cd eggd800
    python setup.py install

The setup.py step might require the use of sudo, depending on your Python installation.

