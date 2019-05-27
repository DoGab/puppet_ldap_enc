# Puppet LDAP Enc Changelog

## Version 0.6

* Bugfix: classes will always get passed to puppet as list event if it contains one class
* Added exception handling around file access in `read_cache` and `write_cache` methods

## Verison 0.5

* Logging to syslog added
* Implemented a local file cache per host
* Possibility to only use the cache and perform no LDAP query
* Possibility to enable hostname checking with regular expression
* Updated README.md

## Version 0.4

* Capability to also manage ä, ö, ü in LDAP fields and correctly pass them to puppet.
* Updated README.md
