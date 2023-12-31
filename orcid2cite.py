#!/usr/bin/env python3
# coding: utf-8
# By Migdał
# get citations for given ORCID ID

from bs4 import BeautifulSoup
from selenium import webdriver
from sys import argv, exit
from time import sleep
import re, requests

usage = "orcid2cite.py ORCIDID [prefix='<li>' suffix='</li>']"


class CrossRefClient(object):
    """source https://gist.github.com/dobrosketchkun/f14e1ab9ae817b00b28251f11786fbcf"""

    def __init__(self, accept='text/x-bibliography; style=apa', timeout=3):
        """
        # Defaults to APA biblio style

        # Usage:
        s = CrossRefClient()
        print s.doi2apa("10.1038/nature10414")
        """
        self.headers = {'accept': accept}
        self.timeout = timeout

    def query(self, doi, q={}):
        if doi.startswith("http://"):
            url = doi
        else:
            url = "http://dx.doi.org/" + doi
        r = requests.get(url, headers = self.headers)
        return r

    def doi2apa(self, doi):
        self.headers['accept'] = 'text/x-bibliography; style=apa'
        return self.query(doi).text

    def doi2turtle(self, doi):
        self.headers['accept'] = 'text/turtle'
        return self.query(doi).text

    def doi2json(self, doi):
        self.headers['accept'] = 'application/vnd.citationstyles.csl+json'
        return self.query(doi).json()


def names(ref):
    """source https://gist.github.com/dobrosketchkun/f14e1ab9ae817b00b28251f11786fbcf"""
    name = []
    for _item in ref['author']:
        given_in = _item['given'].split(' ')
        given = ''.join([_name[0] + '.' for _name in given_in])
        name.append(_item['family'] + ', ' + given + ', ')
    name[-1] = name[-1][:-2]
    return ''.join(name)


class Publication(dict):

    def __init__(self, doi, session=CrossRefClient()):
        self['DOI'] = doi
        out = session.doi2json(doi)
        self['authors']= names(out)
        self['year'] = int(out['created']['date-parts'][0][0])
        self['title'] = out['title']
        self['journal_short'] = out['container-title-short']
        self['volume'] = str(out['volume'])
        if 'article-number' in out.keys():
            self['pages'] = str(out['article-number'])
        else:
            self['pages'] = out['page']

    def __str__(self):
        string = self['authors'] + ' ' + \
            self['title'] + '. ' + \
            self['journal_short'] + '. ' + \
            str(self['year']) + '. ' + \
            self['volume'] + ':' + \
            self['pages'] + '. ' + \
            'doi: ' + self['DOI']
        return string


def main():
    nargs = len(argv)
    if nargs == 2:
        orcid = argv[1]
        prefix = '<li>'
        suffix = '</li>'
    elif nargs == 4:
        orcid = argv[1]
        prefix = argv[2]
        suffix = argv[3]
    else:
        print(usage)
        exit()

    url = 'https://orcid.org/' + orcid
    driver = webdriver.Firefox()
    driver.get(url)
    sleep(5)
    page_source = driver.page_source
    driver.close()
    soup = BeautifulSoup(page_source, 'html.parser')

    doi_list = []
    doi_re = re.compile('doi.org')
    for doi in soup.find_all(string='DOI:'):
        a = doi.parent.parent.findChild('a', href = doi_re)
        href = a.get('href')
        doi_list.append(href)

    session = CrossRefClient()
    pubs = [Publication(doi, session) for doi in doi_list]
    pubs.sort(reverse=True, key = lambda x: x['year'])
    for pub in pubs:
        print(prefix + str(pub) + suffix)


if __name__ == '__main__':
    main()
