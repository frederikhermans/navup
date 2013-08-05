#!/usr/bin/python

import datetime
import smtplib
import traceback
import urllib2

MAIL_FROM = open('conf/username').read().strip()
DATE_FMT = '%Y-%m-%d'
URL_FMT = 'https://secust.msse.se/se/amf/NAVS/default.aspx?datum1={from_date}&datum2={to_date}&cid={classid}&DocType=Text&clientattributes=1'

def get_nav(today, classid):
    def parse_line(line):
        elems = line.strip().split(';') 
        keys = ['name', 'date', 'nav', 'adj', 'currency']
        ret = dict(zip(keys, elems))
        ret['nav'] = float(ret['nav'].replace('\xc2\xa0', '').replace(',', '.'))
        ret['adj'] = float(ret['adj'].replace('\xc2\xa0', '').replace(',', '.'))
        return ret

    from_date = today - datetime.timedelta(days=7)
    url = URL_FMT.format(from_date=from_date.strftime(DATE_FMT),
                         to_date=today.strftime(DATE_FMT),
                         classid=classid)
    lines = urllib2.urlopen(url).readlines()
    if len(lines) < 3:
        raise Exception('Invalid data from web service.')

    current = parse_line(lines[2])

    if len(lines) > 3:
        previous = parse_line(lines[3])
        current['nav_change'] = 100*(current['nav']-previous['nav'])/previous['nav']
        current['adj_change'] = 100*(current['adj']-previous['adj'])/previous['adj']

    return current

def fmt_email(to, navs):
    msg_fmt = 'From: {mail_from}\nTo: {mail_to}\nSubject: {subject}\n\n{body}'
    body = ''
    entry_fmt = '{date}\t{name:40s}\t{adj} {currency} ({adj_change:.2f}%)\n'
    for classid, nav in navs.iteritems():
        body += entry_fmt.format(**nav)
    return msg_fmt.format(mail_from=MAIL_FROM,
                          mail_to=to,
                          subject='Your navup updates',
                          body=body)

def send_email(msg, mail_from, mail_to):
    server = smtplib.SMTP(open('conf/smtp-server').read().strip())
    server.ehlo()
    server.starttls()
    username = open('conf/username').read().strip()
    password = open('conf/password').read().strip()
    server.login(username, password)
    server.sendmail(mail_from, mail_to, msg)
    server.quit()

def load_email_to_classids():
    email_to_classids = dict()
    for line in open('data/email_to_classids').readlines():
        line = line.strip().split(',')
        email = line[0]
        cids = line[1:]
        email_to_classids[email] = cids

    return email_to_classids

def main():
    email_to_classids = load_email_to_classids()
    all_classids = set()
    for cids in email_to_classids.itervalues():
        all_classids.update(cids)

    navs = dict()
    today = datetime.date.today()
    for classid in all_classids:
        try:
            navs[classid] = get_nav(today, classid)
        except:
            print 'Failed to retrieve course for class id', classid
            traceback.print_exc()

    for email, cids in email_to_classids.iteritems():
        msg = fmt_email(email, {cid: navs[cid] for cid in cids})
        send_email(msg, MAIL_FROM, email)
