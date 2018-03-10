# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 21:37:00 2016
@author: me
"""

import facebook
from robobrowser import RoboBrowser
from selenium import webdriver
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pprint import pprint
import re
from time import sleep
from shutil import which

from my_details import MyDetails # singleton that contains email, password and token fields
                                 # get token from https://developers.facebook.com/tools/explorer



class FacebookBrowser2:
    def __init__(self, Details, page_id = 'Some_page_id'):
        """
        :param Details: singleton, should contain auth data and have fields email and password.
                page_id: id for page to visit
        """
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        browser = webdriver.Chrome(chrome_options=chrome_options)

        url = 'https://www.facebook.com/'
        browser.get(url)
        email = browser.find_element_by_id('email')
        password = browser.find_element_by_id('pass')
        email.send_keys(Details.email)
        password.send_keys(Details.password)
        form = browser.find_element_by_id('login_form')
        form.submit()
        self.Details = Details

        self.browser = browser

        self.reaction_types = ['like','love','wow','haha','sad','angry','thankful']
        self.token = Details.token

        self.page_id = page_id

        self.reacting_people = []

    def getReactions(self,url):
        """

        :param url: url for so-called reaction page for a comment of a post
        :return: dict with reactions. each reaction is a list of dicts {link, name} of the profile of the reaction-er
        """
        self.browser.get(url)
        timetowait = 3 # afte each "see more" click
        timetowait_load = 1 # after initial login
        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'ego_section'))
            WebDriverWait(self.browser, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")
        sleep(timetowait_load) # is necessary? how to wait for load TODO

        # when we have many reactions, they're not all shown in advance. the user needs to click "Peer into the depths"
        # to open them.

        for _ in range(5):
            buttons = self.browser.find_elements_by_xpath("//a[contains(@class, 'pam uiBoxLightblue uiMorePagerPrimary')]")
            for button in buttons[::-1]:
                for _ in range(5):
                    try:
                        button.click()
                        break
                    except:
                        print('can\'t click, retrying...')

                print('CLICKING ON SEE MORE')
                sleep(timetowait)

            if len(buttons)==0:
                break
        #input('bla')
        reaction_types = self.reaction_types
        reactions={}
        for i, reaction in enumerate(reaction_types):
            #reactions[reaction] = self.browser.find_elements_by_xpath('ul',id='reaction_profile_browser%d'%(i+1))
            try:
                element = self.browser.find_element_by_xpath("//ul[contains(@id, 'reaction_profile_browser%d')]"%(i+1))
                reactions[reaction] = element.get_attribute('innerHTML')
                print(element.get_attribute('innerHTML'))
            except:
                pass
        data = {}
        for reaction, content in reactions.items():
            m = re.findall('href="([^"]*)"[^>]*>([^<]*)<\/a>',content)
            for link, name in m:
                try:
                    data[reaction].append({'link':link,'name':name})
                except:
                    data[reaction] = [{'link': link, 'name': name}]
        return data

    def analyzeReactions(self):
        graph = facebook.GraphAPI(access_token=self.token, version='2.6') # hopefully this will work with ver 2.3 as well
        reaction_page_template = lambda id: 'https://www.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier='+id
        feed = graph.get_connections(self.page_id,'posts')
        feeddata = feed['data']
        count=0
        while feeddata:
            for feeditem in feeddata:
                print(feeditem.keys())
                if 'message' in feeditem.keys():
                    print('message',feeditem['message'])
                    print('id',feeditem['id'])
                    #obj = graph.get_connections(feeditem['id'], 'likes')
                    #print(obj)
                    obj = graph.get_connections(feeditem['id'],'comments')

                    #print(feeditem['comments'])
                    for comment in obj['data']:
                        print(comment['message'])
                        #comment_obj = graph.get_object(comment['id'], fields='comments')#
                        #print(comment_obj)
                        ret = self.getReactions(reaction_page_template(comment['id']))
                        #pprint(ret)
                        lengths = {k:len(x) for k,x in ret.items()}
                        pprint(lengths)
                        cur_reacting = [ y['name'] for x in ret.values() for y in x  ]
                        self.reacting_people += cur_reacting
                        print('*** total reactions recorded',len(self.reacting_people))
                        print('*** uniques',len(set(self.reacting_people)))
                    print(' ---- NEXT POST ---- ')
            """
            # to get next pages
            feed = requests.get(feed['paging']['next']).json()
            if 'data' in feed.keys():
                feeddata= feed['data']
            else:
                print('NO MORE DATA, maybe token expired.')
                data=None

            if count>=1e5:
                break
            """

if __name__=='__main__':
    fb = FacebookBrowser2(MyDetails)
    #x='https://www.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier=10155425859252076_10155425905842076'
    #ret = fb.getReactions(url=x)
    #pprint(ret)
    #lengths = {k: len(x) for k, x in ret.items()}
    #pprint(lengths)
    fb.analyzeReactions()


