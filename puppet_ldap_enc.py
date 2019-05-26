#!/usr/bin/python
# Puppet LDAP Enc
# Author: Dominic Gabriel
# Version: 0.5
#

import yaml
import sys
import argparse
import re
import ldap
import io
import os.path
import syslog

parser = argparse.ArgumentParser(description='Puppet LDAP ENC script')
parser.add_argument('fqdn', help='Hostname used for the enc query')
args = parser.parse_args()
hostname = args.fqdn

loggingpriority = syslog.LOG_CRIT
usecacheonly = False
cachepath = '/etc/puppetlabs/enc/cache/'
cachefile = cachepath + hostname

ldapserver = 'ldap://ldapserver.example.com:389'
ldapstring = '(&(objectclass=puppetClient)(cn={hostname}))'.format(hostname=hostname)
ldapbase = 'ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM'
ldapfieldexcludelist = ['objectclass']
environmentfieldname = 'environment'
classesfieldname = 'puppetclass'
parametersfieldname = 'puppetvar'

hostnamecheckenabled = False
hostnameregexpattern = '^[0-9a-zA-Z]*\.example\.com$'


def is_valid_fqdn(hostname):
  if len(hostname) > 255:
    return False
  is_valid = re.match('^[0-9a-zA-Z]*\.example\.com$', hostname)
  if is_valid is None:
    return False
  return True

def write_to_syslog(message):
  logmessage = hostname + ' - ' + message
  syslog.syslog(loggingpriority, logmessage)

def ldap_connect_search():
  try:
    connection = ldap.initialize(ldapserver)
    query_result = connection.search_s(ldapbase, ldap.SCOPE_SUBTREE, ldapstring)
    if not query_result:
      write_to_syslog('LDAP query result was empty - using cache')
      read_cache()
  except Exception:
    write_to_syslog('Connection to ' + ldapserver + ' failed - using cache')
    read_cache()
  else:
    result_dn, result_query = get_ldap_fields(query_result)
    return result_dn, result_query

def get_ldap_fields(result):
  try:
    result_dn = result[0][0]
    result_query = result[0][1]
  except Exception:
    write_to_syslog('get ldap fields failed')
    read_cache()
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
    if field == environmentfieldname:
      host_dict['environment'] = parse_ldap_field_value(value)
      continue
    if field == classesfieldname:
      host_dict['classes'] = parse_ldap_field_value(value)
      parameter_dict['roles'] = parse_ldap_field_value(value)
      continue
    if field == parametersfieldname:
      for var in query_result[parametersfieldname]:
        var = var.split('=')
        parameter_dict[var[0]] = var[1]
      continue
    parameter_dict['dn'] = query_dn
    parameter_dict[field.lower()] = parse_ldap_field_value(value)
  host_dict['parameters'] = parameter_dict
  return host_dict

def write_cache(hosts):
  if not os.path.exists(cachepath):
    os.makedirs(cachepath)
  with io.open(cachefile, 'w') as outfile:
    yaml.safe_dump(hosts, outfile, default_flow_style=False, allow_unicode=True)
  outfile.close()

def read_cache():
  if os.path.isfile(cachefile):
    with open(cachefile, 'r') as stream:
      yamlloaded = yaml.safe_load(stream)
  else:
    write_to_syslog('Cache file not available')
    sys.exit(1)
  stream.close()
  print_yaml(yamlloaded)
  sys.exit(0)

def print_yaml(data):
  print(yaml.safe_dump(data, default_flow_style=False, allow_unicode=True))


def start():
  if hostnamecheckenabled:
    if not is_valid_fqdn():
      write_to_syslog('Hostname check failed')
      sys.exit(1)
  if usecacheonly:
    read_cache()
  else:
    ldap_query_dn, ldap_query_result = ldap_connect_search()
    parsed_host_dict = parse_ldap_fields(ldap_query_result, ldap_query_dn)
    write_cache(parsed_host_dict)
    print_yaml(parsed_host_dict)

start()
