# inventoryd
A clever inventory daemon for Ansible 1.x, based on the clever ideas of [Dag Wieërs](https://github.com/dagwieers), [Jeroen Hoekx][https://github.com/jhoekx], [Maurice](https://github.com/mho), Raf Van Opdorp, [Serge van Ginderachter](https://github.com/srvg), Tom Kersten and [Vincent Van der Kussen](https://github.com/vincentvdk) and myself.
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

## to do
+ REST management interface (over both http and https)
+ Various backends to store the inventory cache (postgresql, mariadb)
+ Static inventory entries, with support for Jinja2 templating
+ Connectors to many different (dynamic) data sources (postgresql, mariadb, odbc)
+ Create a systemd unit file
+ Provide a cli to the REST API

## howto
### installation
1. Create the sqlite3 db for inventoryd: *~]$ sqlite3 test.db < sql/sqlite3.sql*
2. Generate certificate and key for your ssl REST server: *~]$ sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt*
3. Include the inventoryd directory in your PYTHONPATH environment variable
4. Create a config file based on the example
5. Execute the script *~]$ ./inventoryd.py --config=/path/to/config/file*
6. Browse to *http(s)://localhost:8080/inventory/list*

### connectors
Familiarize yourself with the database first

#### connector properties
- **enabled** 0|1 *is the connector enabled?*
- **name** string *a human name for the connector*
- **connector** uri *the connector used, currently only uri is available*
- **type** hosts|groups *does the connector access info about hosts or groups. No, I don't do both*
- **priority** integer *the highest priority wins*
- **parameters** json string *connector-specific parameters*

#### connector list
- **uri** fetches a file from a local/remote location and interprets it. The parameters required are format and uri

#### parameter list
The following parameter is mandatory for each conenctor:
- **schema** A list of dictionaries defining the data source: datatype(string|integer|boolean|float), index (the index of the field) and name (the name it will be known as)

URI connector parameters:
- **format** json|csv *the expected format of the data source* 
- **uri** string *a correctly constructed uri to a local or remote resource. eg file:///tmp/data.json*

#### A schema example:
**JSON:**

    [
        {"datatype": "string", "index": "hostname", "name": "hostname"},
        {"datatype": "string", "index": "groupname", "name": "groupname"},
        {"datatype": "string","index": "parent","name": "parent"}
    ]
**CSV:**

    [
        {"datatype": "string", "index": 0, "name": "hostname"},
        {"datatype": "int", "index": 1, "name": "net_name"},
        {"datatype": "boolean","index": 2,"name": "test"}
    ]
