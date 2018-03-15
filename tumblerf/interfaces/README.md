TumbleRF: Interfaces
===

## Install

Select interfaces may require additional configuration in order to integrate them with one's system. 

### For specific interfaces:

#### For `gr-ieee802-15-4`-based interfaces:
Install `GNU Radio` and `UHD` from source or with development headers from your package manager:
```bash
sudo apt-get install gnuradio-dev libuhd-dev
```
Install `GNU Radio` out of tree dependencies [`gr-ieee802-15-4`](https://github.com/bastibl/gr-ieee802-15-4) and [`gr-foo`](https://github.com/bastibl/gr-foo):
```bash
git clone https://github.com/bastibl/gr-foo.git && pushd gr-foo && mkdir build && cd build && cmake ../ && make -j8 && sudo make install && sudo ldconfig && popd
git clone https://github.com/bastibl/gr-ieee802-15-4.git && pushd gr-foo && mkdir build && cd build && cmake ../ && make -j8 && sudo make install && sudo ldconfig && popd
```
Once installed, a headerless 802.15.4 PHY transceiver block must be generated locally.  To do this, open the `/tumblerf/interfaces/gr_ieee802_15_4/ieee802_15_4_OQPSK_headerless_PHY.grc` flowgraph in `gnuradio-companion` and press `F5`.  This will create a Python representation of the flowgraph which can be instantiated and invoked by `tumblerf`.

#### For `Killerbee`-based interfaces:

For the `interface_killerbee` interface, you must install [KillerBee](https://github.com/riverloopsec/killerbee):
```bash
git clone git@github.com:riverloopsec/killerbee.git
pushd killerbee
git checkout feature/standard-fcs
python setup.py install
popd
```
