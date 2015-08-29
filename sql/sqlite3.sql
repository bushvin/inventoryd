
CREATE TABLE user(
    name          CHAR(16) PRIMARY KEY NOT NULL,
    passhash      CHAR(129) NOT NULL);

INSERT INTO user (name, passhash) VALUES('root','11ad591a16c1b3272a92c915e95c50284dc59ed58b2d02ba961c9162494e041dd73819d5d2c97d120bb924cca9efbd2ea8847db5ce56acec3c7fcd7f9b5d3538:99adc231b045331e514a516b4b7680f588e3823213abe901738bc3ad67b2f6fcb3c64efb93d18002588d3ccc1a49efbae1ce20cb43df36b38651f11fa75678e8');

CREATE TABLE role(
    name          CHAR(32) PRIMARY KEY NOT NULL);

INSERT INTO role (name) VALUES('root');


CREATE TABLE acl(
    role_name     CHAR(32) NOT NULL,
    object        CHAR(16) NOT NULL,
    ace_list          INTEGER DEFAULT 0,
    ace_create        INTEGER DEFAULT 0,
    ace_modify        INTEGER DEFAULT 0,
    ace_delete        INTEGER DEFAULT 0);

INSERT INTO acl (role_name, object, ace_list, ace_create, ace_modify, ace_delete) VALUES('root','group',1,1,1,1), ('root','host',1,1,1,1), ('root','connector',1,1,1,1), ('root','user',1,1,1,1), ('root','role',1,1,1,1);

CREATE TABLE auth_token(
    token         CHAR(64) NOT NULL,
    username      CHAR(16) NOT NULL,
    created       TEXT DEFAULT '0000-00-00 00:00:00.000',
    expires       TEXT DEFAULT '0000-00-00 00:00:00.000');

CREATE TABLE role_member(
    role_name     CHAR(16) NOT NULL,
    user_name     CHAR(16) NOT NULL);
    
INSERT INTO role_member (role_name, user_name) VALUES('root','root');

CREATE TABLE sync_history(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    connector_id   INTEGER NOT NULL,
    datetime_start TEXT DEFAULT '0000-00-00 00:00:00.000',
    datetime_end   TEXT DEFAULT '0000-00-00 00:00:00.000',
    active         INTEGER DEFAULT 0,
    resultcode     INTEGER DEFAULT 1,
    message        TEXT);

CREATE TABLE sync_connector(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled        INT DEFAULT 1,
    name           CHAR(64) NOT NULL,
    connector      CHAR(64) NOT NULL,
    type           CHAR(64) DEFAULT 'hosts',
    parameters     TEXT,
    priority       INT DEFAULT 1000);

CREATE TABLE cache_vars(
    history_id     INTEGER NOT NULL,
    name           CHAR(256),
    type           CHAR(256),
    fact           CHAR(256),
    value          TEXT);

CREATE TABLE cache_groupmembership(
    history_id     INTEGER NOT NULL,
    name           CHAR(256),
    childname      CHAR(256),
    childtype      CHAR(64));

CREATE TABLE static_vars(
    created        TEXT DEFAULT '0000-00-00 00:00:00.000',
    name           CHAR(256),
    type           CHAR(256),
    fact           CHAR(256),
    value          TEXT);

CREATE TABLE static_groupmembership(
    created        TEXT DEFAULT '0000-00-00 00:00:00.000',
    name           CHAR(256),
    childname      CHAR(256),
    childtype      CHAR(64));

