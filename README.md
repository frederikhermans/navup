# navup #

Send most recent net asset values (NAVs) of funds.

## Configuration ##

### SMTP Server ###

You need to set up your outgoing SMTP server. The configuration is stored in three files.

* `conf/smtp-server` Contains the hostname:port of the SMTP server. The server is required to support TLS.
* `conf/username` Username to authenticate at the SMTP server.
* `conf/password` Password to authenticate at the SMTP server.

### E-mail addresses, class IDs and quantities ###

You need to define which updates to send to which email addresses. The configuration is stored in `data/profiles`. Each line specifies an email address, class IDs of the assets, and the quantity for each asset. Lines must have the following format:

`email-addr,classid1,qty1,classid2,qty2,classid3,qty3,...`

## Running ##

After configuration, simply run
`$ python main.py`
Setup a cron job to have emails sent periodically.
