#!/usr/bin/python

import ConfigParser
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
        print url
        raise Exception('Invalid data from web service.')

    lines = [parse_line(l) for l in lines[2:]]
    lines = sorted(lines, key=lambda l: l['date'], reverse=True)
    current = lines[0]
    if len(lines) > 1:
        previous = lines[1]
        current['nav_chg'] = 100*(current['nav']-previous['nav'])/previous['nav']
        current['adj_chg'] = 100*(current['adj']-previous['adj'])/previous['adj']

    return current

def fmt_email(to, cid2qty, navs):
    msg_fmt = 'From: {mail_from}\nTo: {mail_to}\nSubject: {subject}\n\n{body}'
    body = ''
    entry_fmt = '{date}\t{name:40s}\t{nav} {currency} ({nav_chg:.2f}%, {abs_chg:.2f})\t{value:.2f}\n'
    total = 0
    total_abs_chg = 0
    classids = [x[0] for x in sorted(cid2qty.items(), key=lambda x: x[1]*navs[x[0]]['nav'],
                                     reverse=True)]
    for classid in classids:
        nav = navs[classid]
        value = cid2qty[classid]*nav['nav']
        old_nav = nav['nav'] / (1+nav['nav_chg']/100.0)
        abs_chg = cid2qty[classid]*(nav['nav']-old_nav)
        total += value
        total_abs_chg += abs_chg
        body += entry_fmt.format(value=value, abs_chg=abs_chg, **nav)

    total_chg = 100*(total-(total-total_abs_chg))/(total-total_abs_chg)
    footer_fmt = '\nTotal value: {total:.2f} ({total_chg:.2f}%, {total_abs_chg:.2f})'
    subject_fmt = 'Navup: {total_chg:.2f}%, {total_abs_chg:.2f}'
    subject = subject_fmt.format(total_abs_chg=total_abs_chg,
                                 total_chg=total_chg)
    body += footer_fmt.format(total=total, total_abs_chg=total_abs_chg,
                          total_chg=total_chg)
    return msg_fmt.format(mail_from=MAIL_FROM,
                          mail_to=to,
                          subject=subject,
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

def load_profiles():
    profiles = dict()
    conf = ConfigParser.ConfigParser()
    conf.optionxform = str # Don't transform options to lowercase
    conf.read('data/profiles')
    for email in conf.sections():
        profiles[email] = dict()
        for classid, qty in conf.items(email):
            profiles[email][classid] = float(qty)

    return profiles

def main():
    profiles = load_profiles()
    classids = set()
    for cid2qty in profiles.itervalues():
        classids.update(cid2qty.keys())

    navs = dict()
    today = datetime.date.today()
    for classid in classids:
        try:
            navs[classid] = get_nav(today, classid)
        except:
            print 'Failed to retrieve course for class id', classid
            traceback.print_exc()

    for email, cid2qty in profiles.iteritems():
        msg = fmt_email(email, cid2qty, {cid: navs[cid] for cid in cid2qty if cid in navs})
        send_email(msg, MAIL_FROM, email)

if __name__ == '__main__':
    main()
