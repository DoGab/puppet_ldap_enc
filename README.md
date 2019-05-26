# Puppet LDAP Enc

## Table of content
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Customization](#customization)
4. [Enable puppet ldap enc](#enable-puppet-ldap-enc)
5. [Example](#example)
6. [Changelog](#changelog)
7. [Disclaimer and License](#disclaimer)

Puppet external node classifier (ENC) for ldap connections written in Python. With Puppet Version 6.X the LDAP node_terminus will be removed. This script can be used to still use LDAP as the source for node parameters.

The script takes one parameter which is the hostname of the server, performs an LDAP search for the given hostname and returns a yaml output in the following format. At the same time it writes the transformed LDAP query result to a local file cache. If the LDAP server is unavailable it will try to read from the local cache before a puppet run fails.

For more information about writing an Enc see the documentation [here](https://puppet.com/docs/puppet/5.5/nodes_external.html). For a full example of an output consult the example section.

```yaml
classes:
- role_common
- role_samba
- role_apache
environment: lab
parameters:
  fwenabled: 'no'
  mailserver: mail.example.com
```

## Requirements
The following python modules are required to properly run the script.

* yaml
* sys
* argparse
* re
* ldap
* io
* os.path
* syslog

## Installation

### On RHEL7
Install via yum package manager:

```bash
sudo yum install python-ldap
```

### On Ubuntu
Install via apt package manager:

```bash
sudo apt install python-ldap
```

## Customization
Modify these variables in the header of the script to customize your LDAP query. By default all fields of the matching object will be passed to puppet as parameters.

### Caching and logging variables

* `loggingpriority`: Define the priority which will be used to log failures to syslog.
* `usecacheonly`: Set to `True` to disable LDAP query and read from the local cache. Take care that this requires a cache file per server, otherwise the puppet run will fail.
* `cachepath`: Set the path where to save cache files.
* `cachefile`: Modify to change the format where and how the cache file will be saved on disk.

```python
loggingpriority = syslog.LOG_CRIT
usecacheonly = False
cachepath = '/etc/puppetlabs/enc/cache/'
cachefile = cachepath + hostname
```

### LDAP variables

* `ldapserver`: The server and port for the LDAP query
* `ldapstring`: Filter which objects should be included.
* `ldapbase`: Where to search for matching objects.
* `ldapfieldexcludelist`: All fields of the LDAP object except the ones in this list will be passed to puppet as parameters.
* `environmentfieldname`: The name of the field in ldap which contains the definition for the environment.
* `classesfieldname`: The name of the field in ldap whcih contains all the classes which should be applied to the servers.
* `parametersfieldname`: The name of the field in ldap which contains all parameters. The field expects a format of `<key>=<value>` and will be split by the `=` character.

```python
ldapserver = 'ldap://ldapserver.example.com:389'
ldapstring = '(&(objectclass=puppetClient)(cn={hostname}))'.format(hostname=hostname)
ldapbase = 'ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM'
ldapfieldexcludelist = ['objectclass']
environmentfieldname = 'environment'
classesfieldname = 'puppetclass'
parametersfieldname = 'puppetvar'
```

### Hostname check variables

* `hostnamecheckenabled`: Set to `True` to enable checking if the provided hostname has the correct format, like defined in the `hostnameregexpattern` variable.
* `hostnameregexpattern`: Define the format for your hostname check.

```python
hostnamecheckenabled = False
hostnameregexpattern = '^[0-9a-zA-Z]*\.example\.com$'
```


## Enable puppet ldap enc
To enable the new ldap enc copy the script to your desired location. After that you need to edit the `/etc/puppetlabs/puppet/puppet.conf` and restart the puppetserver service.

Remove theses lines...
```bash
node_terminus = ldap
ldapserver = ldapserver.example.com
ldapstring = (&(objectclass=puppetClient)(cn=%s))
ldapbase = ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM
```

add these ones...
```bash
node_terminus = exec
external_nodes = /etc/puppetlabs/enc/puppet_ldap_enc.py
```

and restart the puppetserver:
```bash
sudo systemctl restart puppetserver
```

### Migration
To safely migrate to the new ldap enc you can process the following steps.

1. Create a new role which contains your changes of the `puppet.conf` as well as the ldap enc script.
2. Enable the role on your testing puppetmaster server.
3. Test some of your production severs against the catalogue of the lab puppetmaster in `noop` mode.
```bash
puppet agent --server <testingpuppetmaster> --vardir /var/lib/puppet/<testingpuppetmaster> --ssldir /var/lib/puppet/<testingpuppetmaster>/ssl --test --noop
```

If you made it so far without errors it's very likely that you also won't run into problems when enabling the ldap enc on your production puppetmaster.

1. Disable all puppet agents by running `puppet agent --disable` on every server.
2. Apply the new role with your puppet ldap enc changes on the production puppetmaster.
3. Enable all servers in an environment, starting with the `lab` environment and continuing until all servers are running the puppet agent again.

## Example
An LDAP object might have the following fields:

| field | value | passed to |
|-------|-------|-----------|
|puppetclass|[common, samba, apache]|classes, parameter - roles|
|environment|lab|environment|
|puppetvar|['mailserver=mail.example.com', 'fwenabled=no']|parameter - mailserver, fwenabled|
|appldesc|'Simple Webserver'|parameter - appldesc|
|environmentsoftware|Development|parameter - environmentsoftware|
|hostlocation|ZH|parameter - hostlocation|
|hostname|srv01|parameter - hostname|
|osversion|'7.6'|parameter - osversion|
|state|'In use'|parameter - state|

The output for the object above will produce an output like below and being passed to puppet.
```yaml
$ /etc/puppetlabs/enc/puppet_ldap_enc.py srv01.example.com
classes: &id001
- common
- samba
- apache
environment: lab
parameters:
  cn: srv01.example.com
  dn: cn=srv01.example.com,ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM
  mailserver: mail.example.com
  fwenabled: 'no'
  roles: *id001
  appldesc: 'Simple Webserver'
  environment: lab
  environmentsoftware: Development
  hostlocation: ZH
  hostname: srv01
  osversion: '7.6'
  state: In use
```

## Changelog

see [Changelog](https://github.com/DoGab/puppet_ldap_enc/blob/master/CHANGELOG.md)

## Disclaimer
This program is distributed WITHOUT ANY WARRANTY.
Without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the License for more details.

## License
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

For more information see the [license](https://github.com/DoGab/puppet_ldap_enc/blob/master/LICENSE) file.
