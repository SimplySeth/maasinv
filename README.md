# maasinv
MAAS Dynamic Inventory for Ansible

## Getting Started
This script is meant to act as a dynamic inventory for MAAS. 

_NOTE: First run of of the script might take a long time. The file is cached for 30 minutes_
 
### Prerequisites
- `python3-maas-client` installed via apt on Ubuntu
- python 3

### Installing

The python3-maas-client seems to only be available on Ubuntu.

`apt install python3-maas-client`

If you wish to do this on a non-Ubuntu machine, you will have to grab the contents of `dpkg -L python3-maas-client` from and Ubuntu box and copy it over to your python3 directories.

### Usage
This script creates groups based on the first letters of the hostname.
e.g. `swrmwrk004` and `swrmwrk001` will be in group `swrmwrk`

Run the script with no arguments and you'll see the help prompt

```
./maasinv.py 

usage: maasinv.py [-h] [--list] [--host HOSTNAME] [--raw] [--raw-host RAWHOST]

MAAS Inventory

optional arguments:
  -h, --help          show this help message and exit
  --list              Get all items.
  --host HOSTNAME     Get a specific host.
  --raw               Get the raw data dump from MAAS.
  --raw-host RAWHOST  Get the raw data on a specific host from MAAS when given a hostname.
```

To run tasks against all MAAS nodes ...

` ansible all -m setup -i ./maasinv.py `

To run tasks against a specific group of nodes in MAAS ...

` ansible swmwrk -m setup -i ./maasinv.py`

To run tasks against a specific MAAS node in a specific group ... 

` ansible swmwrk -m setup -i ./maasinv.py -l nodename`


