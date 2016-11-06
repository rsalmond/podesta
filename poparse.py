import os
import sys
import base64
import email
import dkim
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#sqlalchemy init
engine = create_engine('sqlite:///data.db')
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Email(Base):
    __tablename__ = 'email'
    id = Column(Integer, primary_key=True)
    from_addr = Column(String)
    from_name = Column(String)
    to_addr = Column(String)
    to_name = Column(String)
    name = Column(String)
    dkim_verified = Column(Boolean)
    has_dkim = Column(Boolean)
    msg_id = Column(Integer)

    def __init__(self, email, fliename):
        # parse an email object and record interesting fields

        from_field = email.get('Received-From')
        if from_field is None:
            from_field = email.get('From')

        from_field = Email.gimme_unicode(from_field)

        self.from_name, self.from_addr = Email.parse_email_field(from_field)

        to_field = email.get('Delivered-To')
        if to_field is None:
            to_field = email.get('To')

        to_field = Email.gimme_unicode(to_field)
        self.to_name, self.to_addr = Email.parse_email_field(to_field)

        self.has_dkim = self.dkim_present(email)
        if self.has_dkim:
            self.dkim_verified = self.dkim_verify(email)

        try:
            self.msg_id = int(filename.split('.')[0].split('/')[1])
        except Exception as e:
            print e, filename

        self.save()

    def save(self):
        session.add(self)
        session.commit()

    def dkim_present(self, email):
        # check for dkim header
        if email.get('DKIM-Signature') is not None:
            return True

    def dkim_verify(self, email):
        # verify dkim 
        dkim_obj = dkim.DKIM(email.as_string())
        try:
            verified = dkim_obj.verify()
        except dkim.ValidationError as e:
            return False
        except dkim.KeyFormatError as e:
            return False
        except Exception as e:
            print e
            return False

        return verified

    @classmethod
    def parse_email_field(cls, field):
        # turn 'Some Name <somename@whatever.com>' into 'Some Name', 'somename@whatever.com'

        def clean_email(email):
            return email.strip('<>').lower()

        def clean_name(name):
            return name.replace('"', '')

        field = field.strip()

        # handle "Some Name <SomeName@whatever.com<mailto:SomeName@whatever.com>>"
        if 'mailto' in field:
            # split out Some Name into head
            head = ' '.join([part for part in field.split('mailto:')[0].split(' ') if '@' not in part])
            # split email address into tail
            tail = field.split('mailto:')[-1:][0].strip('<>')
            # turn field into something like "Some Name somename@whatever.com"
            field = ' '.join((head, tail))

        # handle "SomeName<somename@whatever.com>"
        field = field.replace('<', ' ')

        # handle "Some Name <somename@whatever.com>"
        if ' ' in field:
            split = field.split(' ')
            name = ' '.join(split[:-1])
            try:
                email_address = split[-1]
            except:
                import pdb
                pdb.set_trace()

            return clean_name(name), clean_email(email_address)
        else:
            return None, clean_email(field)

    @classmethod
    def gimme_unicode(cls, value):
        # fucking unicode
        try:
            new = unicode(value)
        except UnicodeDecodeError as e:
            try:
                new = unicode(value, 'utf-8')
            except UnicodeDecodeError as e:
                try:
                    new = unicode(value, 'latin-1')
                except UnicodeDecodeErorr as e:
                    import pdb
                    pdb.set_trace()
        return new


def itermail(email_dir):
    # walk the extracted email
    for filename in os.listdir(email_dir):
        if filename.endswith(".eml"):
            yield os.path.join(email_dir, filename)


def safe_filename(filename):
    badchars = '?*/='
    for char in badchars:
        filename = filename.replace(char, '')

    return filename

def save_attachments(msg):
    # save any attachments into msgname/attachmentname
    parts = [payload for payload in msg.get_payload()]
    for part in parts:
        if part.get_filename() is not None:
            attachname = safe_filename(part.get_filename())
            dirname = os.path.join('attachments', filename.split('.')[0].split('/')[1])
            try:
                os.makedirs(dirname)
            except OSError as e:
                #directory already exists
                if e.errno == 17:
                    continue
                import pdb
                pdb.set_trace()
            path = os.path.join(dirname, attachname)
            # save attachment to disk
            with open(path, 'wb') as f:
                try:
                    f.write(base64.b64decode(part.get_payload()))
                except Exception as e:
                    print 'Error {} writing attachment file {}'.format(e, attachname)


if __name__ == '__main__':
    # initialize db
    Base.metadata.create_all(engine)

    email_dir = 'messages'

    # iterate over all the email files and extract info and attachments
    for filename in itermail(email_dir):
    #filename = sys.argv[1]
        with open(filename, 'r') as f:
            contents = f.read()
            msg = email.message_from_string(contents)
            email_record = Email(msg, filename)

        if len(msg.get_payload()) > 1 and type(msg.get_payload()) == list:
            save_attachments(msg)
