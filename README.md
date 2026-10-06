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

It can be installed with:

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

## Running the `eggd800` acquisition utility

1. Open an Anaconda Prompt from the Start Menu.
1. Activate the `eggd800` environment: `conda activate eggd800`
1. Make an acquisition:
    * Unlimited duration: `python eggd800\eggd800.py acq --researcher XXX --lang YYY --spkr ZZZ --item ITEM`
    * Specified duration in seconds: `python eggd800\eggd800.py acq --researcher XXX --lang YYY --spkr ZZZ --seconds 5 --item ITEM`
    * With airflow: `python eggd800\eggd800.py acq --researcher XXX --lang YYY --spkr ZZZ --flow --item ITEM`

## Data

Recordings are stored in session folders under `C:\Users\<USERNAME>\Desktop\eggd800`. Session folders are created under the relative path `ISO\SPK\YYYYMMDD`, where:
* `ISO` is the language ISO code
* `SPK` is the speaker initials
* `YYYYMMDD` is the date of the acquisition.

Within the session folders, filenames are of the form `ISO_SPK_YOU_YYYYMMDDTHHHMMSS_ITEM_TOKEN`, where:
* `ISO` and `SPK` are the same as in the path
* `YOU` is the researcher (you)
* `YYYYMMDDTHHMMSS` is the date and timestamp of the acquisition
* `ITEM` identifies the content of the acquisition
* `TOKEN` is the instance of the `ITEM` in the session. Tokens are numbered automatically, starting at `0`.

The Windows filesystem is not case-sensitive, so `ITEM` values that differ only in case are treated as identical when token numbers are calculated. Keep that in mind if your transcription system is case-sensitive.

## Troubleshooting

If you get a `ModuleNotFoundError`, there is a good chance that you did not start an Anaconda Prompt or did not activate the `eggd800` environment. Try repeating the steps in the 'Running the `eggd800` acquisition utility' section.

If you get `Error: No such option: <option>`:
1. Check to see if the option name was mistyped.
1. Check to see whether you included a valid subcommand name (usually `acq`) to the script, e.g. `python eggd800\eggd800.py acq ...`.

    python setup.py install

The setup.py step might require the use of sudo, depending on your Python installation.

