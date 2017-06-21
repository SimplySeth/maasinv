# maasinv
MAAS Dynamic Inventory for Ansible

## Getting Started
This script is meant to act as a dynamic inventory for MAAS. 

*NOTE: First run of of the script might take a long time. The file is cached for 30 minutes*
 
### Prerequisites
- `python3-maas-client` installed via apt on Ubuntu
- python 3

### Installing

The python3-maas-client seems to only be available on Ubuntu.

`apt install python3-maas-client`

If you wish to do this on a non-Ubuntu machine, you will have to grab the contents of `dpkg -L python3-maas-client` from and Ubuntu box and copy it over to your python3 directories.




