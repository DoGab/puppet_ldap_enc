# Puppet LDAP Enc
Puppet external node classifier (ENC) for ldap connections written in Python. With Puppet Version 6.X the LDAP node_terminus will be removed. This script can be used to still use LDAP as the source for node parameters.

The script takes one parameter which is the hostname of the server and returns a yaml output in the following format. For more information see the documentation [here](https://puppet.com/docs/puppet/5.5/nodes_external.html). For a full example of an output consult the testing section.

```
classes:
- common
- samba
- apache
environment: lab
parameters:
  ntp_servers:
  - ntp1.example.com
  - ntp2.example.com
  mail_server: mail.example.com
```

## Requirements
The following python modules are required to properly run the script.

* yaml
* sys
* argparse
* re
* ldap

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
Modify the variables in the header of the header to customize your LDAP query. By default all fields of the matching object will be passed to puppet as top-scope variables.

* `ldapserver`: The server and port for the LDAP query
* `ldapstring`: Filter which objects should be included.
* `ldapbase`: Where to search for matching objects.
* `ldapfieldexcludelist`: Define which fields of your puppetclient object should not being passed to puppet.

This is an example how these variables could be filled:
```
ldapserver = 'ldap://ldapserver.example.com:389'
ldapstring = '(&(objectclass=puppetClient)(cn={hostname}))'.format(hostname=hostname)
ldapbase = 'ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM'
ldapfieldexcludelist = ['objectclass']
```

## Enable puppet ldap enc
To enable the new ldap enc copy the script to your desired location. After that you need to edit the `/etc/puppetlabs/puppet/puppet.conf` and restart the puppetserver service.

Remove theses lines...
```
node_terminus = ldap
ldapserver = ldapserver.example.com
ldapstring = (&(objectclass=puppetClient)(cn=%s))
ldapbase = ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM
```

add these ones...
```
node_terminus = exec
external_nodes = /etc/puppetlabs/enc/puppet_ldap_enc.py
```

and restart the puppetserver:
```
sudo systemctl restart puppetserver
```

## Testing

```python
$ /etc/puppetlabs/enc/puppet_ldap_enc.py srv01.example.com
classes: &id001
- common
- samba
- apache
environment: lab
parameters:
  cn: srv01.example.com
  dn: cn=srv01.example.com,ou=Unix,ou=Server,ou=Infrastruktur,ou=Informatik,DC=EXAMPLE,DC=COM
  ntp_servers:
  - ntp1.example.com
  - ntp2.example.com
  mail_server: mail.example.com
  roles: *id001
  appldesc: 'Simple Webserver'
  environment: Development
  environmentsoftware: lab
  hostlocation: ZH
  hostname: srv01
  osversion: '7.6'
  state: In use
```

### Use it with puppet lookup
