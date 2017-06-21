#!/usr/bin/env python3
from apiclient import maas_client
import argparse
import configparser
from collections import defaultdict,OrderedDict
from datetime import datetime, timedelta
from functools import wraps
import json
import os
import re
import subprocess
import sys


CONFIGFILE = '/etc/maasinv/maasinv.ini'

# For a more descriptive state ...
powered_state = {
  "on" : "POWERED ON",
  "off":"POWERED OFF",
  "unknown": "UNKNOWN",
  "error": "ERROR"
}

class Cache(object):
  '''
    USE: @Cache(<filename>,<timespan>)
    e.g: @Cache('nodes.json', days=1)
    e.g: @Cache('nodes.json', minutes=30)
  '''
  def __init__(self,filename,**kwargs):
    self.time_ago = datetime.now() - timedelta(**kwargs)
    self.filename = filename

  def __call__(self,fn):
    '''
    When writing decorators, the `__call__` function is crucial.
    This is what makes the magic happen.
    The `wrapped` function is also needed to make things work.
    '''
    def wrapped(*oargs,**okwargs):
      # If there is no file, create one by populating it with data...
      if not os.path.isfile(self.filename):
        self.cache(fn(*oargs,**okwargs))
        return self.read()

      # If the file exists ...
      # check for age using the `self.time_ago` variable
      # and the `self.filename` variable
      time_ago = self.time_ago
      filename = self.filename
      c_age = datetime.fromtimestamp(os.path.getctime(filename))
      m_age = datetime.fromtimestamp(os.path.getmtime(filename))

      # if its passed the threshold, then call the original function referenced as `fn`
      # and populate the data
      # if not, just return the data from the file ...
      if c_age < time_ago or m_age < time_ago:
        self.cache(fn(*oargs,**okwargs))
        return self.read()
      else:
        return self.read()
    return wrapped

  def cache(self,data):
      '''
      The function that actually writes the data to the file ...
      '''
      with open(self.filename,'w+') as ef:
        ef.write(data)

  def read(self):
    '''
    The function that actually reads the data from the file ...
    '''
    f = open(self.filename,'r')
    data = f.read()
    f.close()
    return data

class MaasInv(object):
    '''
    MAAS inventory class that has the functions to query MAAS
    '''
    def __init__(self):
        '''
            Initialize the connection and return a client (cursor?) ...
        '''
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGFILE)
            apikey = config['maas']['apikey']
            maas_url = config['maas']['url']
            auth = maas_client.MAASOAuth(*apikey.split(":"))
            self.client = maas_client.MAASClient(auth, maas_client.MAASDispatcher(), maas_url)
        except Exception as e:
            print (str(e))
            sys.exit(1)

    @Cache('nodes.json',minutes=30)
    def getNodes(self):
        client = self.client
        data = client.get("nodes/").read().decode('utf-8')
        return data

    def getGroups(self):
      '''
        Dynamically create groups and group nodes
      '''
      nodes = self.getNodes()
      group_dict = defaultdict(lambda: {})
      data =  json.loads(nodes)
      for l in data:
        if '-' not in l['hostname']:
          g = re.split('[0-9]+',l['hostname'],flags=re.IGNORECASE)[0]
          group_dict[g]
      return json.dumps(group_dict,indent=1,sort_keys=True,separators=(',', ': '))

    def getGoupInv(self):
      '''
        Dynamically create groups and group nodes
      '''
      nodes = self.getNodes()
      group_dict = defaultdict(lambda: {'hosts':[], 'vars': dict()})
      group_dict['all'] = {'hosts':[], 'vars': dict()}
      group_dict['_meta'] = {"hostvars": defaultdict(lambda: {})}
      data =  json.loads(nodes)
      for l in data:
        if '-' not in l['hostname']:
          g = re.split('[0-9]+',l['hostname'],flags=re.IGNORECASE)[0]
          group_dict[g]['hosts'].append(l['hostname'])
          group_dict['all']['hosts'].append(l['hostname'])
          group_dict['_meta']['hostvars'][l['hostname']]['ansible_ssh_host'] = l['ip_addresses'][0]
          group_dict['_meta']['hostvars'][l['hostname']]['hw_power_status'] = powered_state[l['power_state']]

      # Sort the lists in the dictionary ...
      for i in group_dict:
        try:
          group_dict[i]['hosts'].sort()
        except KeyError:
          pass
      return json.dumps(group_dict,indent=1,sort_keys=True,separators=(',', ': '))

    def getNode(self,hostname):
        '''
            Raw node query from MAAS ...
        '''
        client = self.client
        data = client.get("nodes/?hostname="+hostname).read().decode('utf-8')
        return data

    def getNodeData(self,nodename):
      '''
        Find one node by name
      '''
      nodes = self.getNodes()
      data =  json.loads(nodes)
      node = False
      node_facts = dict()
      for l in data:
        if '-' not in l['hostname']:
          if nodename in l['hostname']:
            node =  json.dumps(l,indent=1,sort_keys=True,separators=(',', ': '))
            node_data =  json.loads(node)
            return [node,node_data]
          else:
            pass
        else:
          pass
      if not node:
        return False

    def getNodeInv(self,nodename):
      '''
        Construct the output for a single node.
        This returns two facts, the first IP and the Powered State.
      '''
      node = self.getNodeData(nodename)
      if not node[1]:
        return False
      node_data = node[1]
      node_facts = dict()
      node_facts['ansible_ssh_host'] = node_data['ip_addresses'][0]
      node_facts['hw_power_status'] = powered_state[node_data['power_state']]
      return json.dumps(node_facts,indent=2)

    def getNode(self,nodename):
      node = self.getNodeData(nodename)
      if not node[0]:
        return False
      return node[0]


def getArgs():
  parser = argparse.ArgumentParser(description='MAAS Inventory')
  parser.add_argument('--list',action="store_true", default=False,
    help='Get all items.')
  parser.add_argument('--host',dest='hostname', action='store',
    default=False,help='Get a specific host.')
  parser.add_argument('--raw',dest='rawall',action="store_true",
    default=False,help='Get the raw data dump from MAAS.')
  parser.add_argument('--raw-host',dest='rawhost', action='store',
    default=False, help='Get the raw data on a specific host from MAAS when given a hostname.')
  parser.add_argument('--groups',dest='groups', action='store_true',
    default=False, help='Get the generated groups.')
  args = parser.parse_args()
  if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)
  else:
    return args

def main():
  args =  getArgs()
  m = MaasInv()
  if args.list:
    return m.getGroupInv()
  if args.hostname:
    return m.getNodeInv(args.hostname)
  if args.groups:
    return m.getGroups()
  if args.rawall:
    return m.getNodes()
  if args.rawhost:
    return m.getNodes(args.rawhost)

  #nodes = m.getGroups()
  #print (nodes)
if __name__ == "__main__":
  print (main())
