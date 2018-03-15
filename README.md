TumbleRF: RF Fuzzing Framework
===

## Overview

TumbleRF is a framework that orchestrates the application of fuzzing techniques to RF systems.  While fuzzing has always been a powerful mechanism for fingerprinting and enumerating bugs within software systems, the application of these techniques to wireless and hardware systems has historically been nontrivial due to fragmented and siloed tools.  TumbleRF aims to enable RF fuzzing by providing an API to unify these techniques across protocols, radios, and drivers.

## Presentations

"Unifying RF Fuzzing Techniques under a Common API: Introducing TumbleRF", TROOPERS 18

## Install

### Create a Python 2.7 virtaulenv and activate it:
```bash
virtualenv -p $(which python2.7) py2-virtualenv
source py2-virtualenv/bin/activate
```

You should now see a prompt that looks similar to:
```bash
(py2-virtualenv) ... $
```

Now, install the required dependencies:
```bash
pip install -r tumblerf/requirements.txt
```

### Install dependencies for specific features:

Some of these steps and dependencies are _not_ needed if you do not use certain features/generators.

#### For specific generators:

1. For `dot15d4_*` generators, you must install Scapy (in the GPL version of this code):
** First install dependencies:
*** macOS:
```bash
pip install pcapy
brew install --with-python libdnet
echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> py2-virtualenv/lib/python2.7/site-packages/homebrew.pth
```
*** Linux: install `pcapy` with your package manager:
```bash
sudo apt-get install python-pcapy
#or
pip install pcapy
```
** Then install Scapy, which must be the _exact correct_ version which contains `scapy/layers/dot15d4.py` and has it configured to load:
```bash
git clone git@github.com:BastilleResearch/scapy-radio.git
pushd scapy-radio/scapy
# Now, manually edit scapy/config.py to add 'dot15d4' to the list
python setup.py install
popd
```

#### For specific harnesses:

1. For `ssh_*` harness _test suites_, you must have Docker installed and running.

#### For specific interfaces:

See ./interfaces/README.md.

## Running

This tool needs to be scripted to carry out most tasks, however a CLI is available for some uses.

Running `./tumblerf/cli.py` will tell you what interfaces, generators, and harnesses are available so you can define each.

A very simple run case can be done based on something like the following.
This just transmits random frames from one device to another which looks to see if it got them, and is thus uninteresting.
However, it demonstrates how we pick the _second_ interface to use for TX, as ReceivedFrameHarness will ... TODO
~~~bash
﻿(py2-virtualenv)$ zbid
           Dev Product String       Serial Number
           1:3 KILLERB001           A60400A01C25
           1:4 KILLERB001           0004251CA001

﻿(py2-virtualenv)$ ./tumblerf/cli.py -I KillerBeeInterface -i 1:3 -G Dot15d4RandomPayloadGenerator -H ReceivedFrameHarness --rx_iface_device 1:4
~~~

> NOTE: If you see errors such as the below, you may have a permission issue accessing your USB devces.
> You may correct this via your OS and permissions, or you may run with sudo (not recommended...).
> ```
ERROR:Tue Mar 13 12:16:26 2018 KillerBee Interface:Error when starting, unable to open KillerBee interface.
INFO: Transmit Interface is 802.15.4 KillerBee Interface(Not Available)
```

## Looking at Results

You can process the JSON however you desire, but you may desire to use `parse_results.py` to visualize summaries.

## Testing

~~~bash
pytest -s
~~~

> NOTE: This will, by default, run all test suites. See notes above about certain test suites having additional dependencies.

## Contributing

We welcome bug fixes, feature additions, and more with open arms. Please submit a pull-request.

We ask that you adhere to the Python style guide and implement pytest unit testing wherever possible.
