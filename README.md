# PoParse

A quick and dirty data processing script for leaked Podesta emails.


## Setup

__Get the email__

` $ wget https://file.wikileaks.org/file/podesta-emails/podesta-emails.mbox-2016-11-06.gz`

That takes forever I had my connect reset repeatedly, you may have better luck with [these torrents](https://www.reddit.com/r/WikiLeaks/comments/5an2yi/torrents_of_all_podesta_emails_sets_124_along/).

__Get the `formail` utility__

On Debian this comes from the `procmail` package.

` $ sudo apt-get install procmail`

__Unpack the email__

` $ ./email_unpack.sh`

This will create a `messages` directory with a separate file for each email.

__Run the parser__

` $ python poparse.py`

Go make a snack, this takes a while.

__Explore the data__

All email attachments will be stored in an `attachments` directory.

```
$ find attachments/ -type f | head
attachments/30528/image1.JPG
attachments/21876/clip_image002.jpg
attachments/32292/image.png
attachments/40338/image001.png
attachments/9451/NWF President & CEO Position Specification.pdf
attachments/30808/P9220307 (1).JPG
attachments/20411/image001.jpg
attachments/15040/image001.jpg
attachments/4962/pic00153.gif
attachments/34320/October Report to the Faculty.docx
```

A sqlite database file called `data.db` will be created


```
$ sqlite3 data.db 
SQLite version 3.8.2 2013-12-06 14:53:30
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> .schema
CREATE TABLE email (
	id INTEGER NOT NULL, 
	from_addr VARCHAR, 
	from_name VARCHAR, 
	to_addr VARCHAR, 
	to_name VARCHAR, 
	name VARCHAR, 
	dkim_verified BOOLEAN, 
	has_dkim BOOLEAN, 
	msg_id INTEGER, 
	PRIMARY KEY (id), 
	CHECK (dkim_verified IN (0, 1)), 
	CHECK (has_dkim IN (0, 1))
);

```

Get a list of all email addresses who sent Podesta an email.

```
sqlite> select distinct(to_addr) from email;
sara.latham@ptt.gov
mgitenstein@mayerbrown.com
johnpodesta@gmail.com
kmclean@deweysquare.com
gruncom@aol.com
jeff.mason@thomsonreuters.com
ghirshberg@stonyfield.com
huma@hrcoffice.com
rstephe@att.com
dschwerin@hrcoffice.com
...

```


Get count of all emails which have DKIM signatures.

```
sqlite> select count(*) from email where has_dkim = 1;
```

Get a count of all signed emails which fail verification.

```
sqlite> select count(*) from email where has_dkim = 1 and dkim_verified=0;
```

Find emails from the white house!

```
sqlite> select from_name, from_addr from email where from_addr like '%whitehouse%';
Sheldon Whitehouse |sheldonwhitehouse@cox.net
```

Oh well! ¯\_(ツ)_/¯


#Notes

The email address and name parsing code is not great. It handles normal stuff okay but a lot of people have stuff like `From: "Full Name" <fname@place.com><mailto:fname@place.com>>'` and I can't be arsed to cover every dumb corner case. Also it totally disregards emails sent to multiple people and just uses the first address it finds.

I have no idea what the `'t'` and `Timeout` output is about when processing the emails. I think it may have something to do with trying to validate DKIM sigs but I'm not certain, all I know is I'm not putting it there. Also there are multiple attachments which don't decode correctly.
