import httplib
import urllib
import urllib2 
import re
import csv

from cookielib import CookieJar
from string import ascii_letters, digits
from random import choice
from datetime import date

alphanums = list(ascii_letters + digits)
def _random_id(n):
    """
    create a random alphanumeric identifier of length n
    """
    ''.join(choice(alphanums) for i in range(n))

def _convert_to_float(s):
    """
    try to convert content to float, else return original content
    """
    try:
        return float(s)
    except:
        return s
    


class pyGTrends(object):
    """Google Trends API"""
    def __init__(self, username, password):
        """
        provide login and password to be used to connect to Google Analytics
        all immutable system variables are also defined here
        website_id is the ID of the specific site on google analytics
        """        
        self.login_params = {
            'GA3T': _random_id(11),   # unique identifiers for session
            'GALX': _random_id(11),   # unique identifiers for session
            "continue": 'http://www.google.com/trends',
            'nui': '1',
            'hl': 'en-US',
            'rmShown': '1',
            "PersistentCookie": "yes",
            "Email": username,
            "Passwd": password,
            'service': 'trends' 
        }
        self.headers = [("Content-type", "application/x-www-form-urlencoded"),
                        ('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'),
                        ("Accept", "text/plain")]
        self.url_ServiceLoginBoxAuth = 'https://www.google.com/accounts/ServiceLoginBoxAuth'
        self.url_Export = 'http://www.google.com/trends/viz'
        self.header_dictionary = {}
        self._connect()
        
    def _connect(self):
        """
        connect to Google Trends
        """
        params = urllib.urlencode(self.login_params)
        self.cj = CookieJar()                            
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders = self.headers
        resp = self.opener.open(self.url_ServiceLoginBoxAuth, params)
        
    def download_report(self, keywords, date='all', geo='all', geor='all', graph = 'all_csv', sort=0, scale=0, sa='N'):
        """
        download a specific report
        date, geo, geor, graph, sort, scale and sa
        are all Google Trends specific ways to slice the data
        """
        params = urllib.urlencode({
            'q': ",".join(keywords),
            'date': date,
            'graph': graph,
            'geo': geo,
            'geor': geor,
            'sort': str(sort),
            'scale': str(scale),
            'sa': sa
        })                            
        self.raw_data = self.opener.open('http://www.google.com/trends/viz?' + params).read()[2::2]
        if self.raw_data in ['You must be signed in to export data from Google Trend']:
            raise Exception(self.raw_data)
        self._build_header_dictionary()

    def _build_header_dictionary(self):
        """
        figure out what parts of the csv point to what section
        """
        start = 0
        #print self.raw_data
        for a in range(20):
            redatapuller = re.compile("\r\n\r\n\r\n(?P<word>.*?)\t.*?\n", re.DOTALL)
            m = redatapuller.search(self.raw_data[start:])
            if not(m):
                break
            self.header_dictionary[m.group("word")] = start + m.end()
            if a==0:
                self.header_dictionary["main"] = start + m.end()
            start += m.end()
        
    def report_headers(self):
        return self.header_dictionary.keys()
        
    def columns(self):
        return self.raw_data[:self.raw_data.find("\r")].split("\t")
    
    def csv(self, section="main", column_headers=True):
        """
        return the CSV portion of the data designated by 'section'
        column_headers determines whether the the column headers should be part of the CSV output
        """
        table_end = "\r\n\r\n\r\n"
        table_head_pos = self.header_dictionary[section]
        table_end_pos = self.raw_data[table_head_pos:].find(table_end)
        if table_end_pos == -1:
            table_end_pos = len(self.raw_data)
        else:
            table_end_pos += table_head_pos
        if column_headers:
            a = ",".join(self.columns()) + "\n"
        else:
            a = ""
        return a + self.raw_data[table_head_pos:table_end_pos].replace("\t",",").replace("\r","")