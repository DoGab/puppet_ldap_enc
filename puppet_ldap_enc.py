#!/usr/bin/python
# Puppet LDAP Enc
# Author: Dominic Gabriel
# Version: 0.3
#
# Input: FQDN (server.example.com)
# Output: YAML
#
# Requires: re, sys, yaml, ldap (python-ldap-2.4.15-2.el7.x86_64)
#
# Output example:
# classes:
# - role_samba
# - role_nfs
# - role_apache
# environment: lab
# parameters:
#   fw_enabled: 'no'
#   mailrelay: smtp.example.com

import yaml
import sys
import argparse
import re
import ldap

parser = argparse.ArgumentParser(description='Puppet LDAP ENC script')
parser.add_argument('fqdn', help='Hostname used for the enc query')
args = parser.parse_args()

hostname = args.fqdn

ldapserver = 'ldap://ldapserver.example.com:389'
ldapstring = '(&(objectclass=puppetClient)(cn={hostname}))'.format(hostname=hostname)
ldapbase = 'ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM'
ldapfieldexcludelist = ['objectclass']

class LDAPEmptyListException(Exception):
  """LDAP query result list is empty"""

def is_valid_fqdn(hostname):
  if len(hostname) > 255:
    return False
  is_valid = re.match('^[0-9a-zA-Z]*\.example\.com$', hostname)
  if is_valid is None:
    return False
  return True

def ldap_connect_search():
  try:
    connection = ldap.initialize(ldapserver)
    result = connection.search_s(ldapbase, ldap.SCOPE_SUBTREE, ldapstring)
    if not result:
      raise LDAPEmptyListException('LDAP query result returned empty List')
  except Exception:
    raise
    sys.exit(1)
  else:
    result_dn, result_query = get_ldap_fields(result)
    return result_dn, result_query

def get_ldap_fields(result):
  try:
    result_dn = result[0][0]
    result_query = result[0][1]
  except Exception:
    raise
    sys.exit(1)
  else:
    return result_dn, result_query

def parse_ldap_field_value(value):
  if len(value) > 1:
    return value
  else:
    return value[0]

def parse_ldap_fields(query_result, query_dn):
  host_dict = {}
  parameter_dict = {}
  for field, value in query_result.iteritems():
    if field in ldapfieldexcludelist:
      continue
    if field == 'environment':
      host_dict['environment'] = value[0]
      continue
    if field == 'puppetclass':
      host_dict['classes'] = value
      parameter_dict['roles'] = value
      continue
    if field == 'puppetvar':
      for var in query_result['puppetvar']:
        var = var.split('=')
        parameter_dict[var[0]] = var[1]
      continue
    parameter_dict['dn'] = query_dn
    parameter_dict[field.lower()] = parse_ldap_field_value(value)
  host_dict['parameters'] = parameter_dict
  return host_dict

#print(is_valid_fqdn(hostname))
ldap_query_dn, ldap_query_result = ldap_connect_search()
parsed_host_dict = parse_ldap_fields(ldap_query_result, ldap_query_dn)
print(yaml.dump(parsed_host_dict, default_flow_style=False))
