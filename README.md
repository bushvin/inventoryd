# inventoryd
A clever inventory daemon for Ansible 1.x, based on the clever ideas of [Dag Wieërs](https://github.com/dagwieers), [Jeroen Hoekx](https://github.com/jhoekx), [Maurice](https://github.com/mho), Raf Van Opdorp, [Serge van Ginderachter](https://github.com/srvg), Tom Kersten and [Vincent Van der Kussen](https://github.com/vincentvdk) and myself.
## disclaimer
inventoryd is currently in development, and any feature may break at any given time.
**Use at your own risk!**
## features
+ REST interface to the inventory
+ REST management interface (http(s) hostvars and connectors)
+ Role Based Access Control
+ Static inventory entries
+ Connector to URI data sources (currently only json and csv)
+ Inventory caching
+ Prioritization of data sources
+ Automatic data sync scheduling
+ Automatic cache housekeeping
+ Various backends to store the inventory cache (currently only supports sqlite3)
+ Create a System V init script
+ Static inventory entries, with support for Jinja2 templating on groups

## to do
+ REST management interface (over both http and https)
+ Various backends to store the inventory cache (postgresql, mariadb)
+ Connectors to many different (dynamic) data sources (postgresql, mariadb, odbc)
+ Create a systemd unit file
+ Provide a cli to the REST API

For more information about installing and configuring inventoryd, please check the [Wiki](/bushvin/inventoryd/wiki)
