# -*- coding: utf-8 -*-
import requests
import re
import json
import selenium
import time
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup

SLEEPTIME = 4
SIGNINCOOKIES = [{'domain': 'www.lawsdata.com', 'httpOnly': True, 'name': 'JSESSIONID', 'path': '/', 'secure': False, 'value': 'A5D4BC768BCA4BDE214857572EEB66BB'}, {'domain': '.lawsdata.com', 'expiry': 1873111441, 'httpOnly': False, 'name': 'gr_user_id', 'path': '/', 'secure': False, 'value': '78e4f45c-ec42-4651-8933-34e3c688070c'}, {'domain': '.lawsdata.com', 'expiry': 1589287441, 'httpOnly': False, 'name': 'Hm_lvt_e484b393f62b648c74a7d2bc1605083c', 'path': '/', 'secure': False, 'value': '1557751400'}, {'domain': '.lawsdata.com', 'expiry': 1557753199, 'httpOnly': False, 'name': 'gr_session_id_9c57f1694d616c90', 'path': '/', 'secure': False, 'value': '1e4d54ed-435b-4248-ac92-ae73dcb029b5'}, {'domain': '.lawsdata.com', 'expiry': 1557753200, 'httpOnly': False, 'name': 'gr_session_id_9c57f1694d616c90_1e4d54ed-435b-4248-ac92-ae73dcb029b5', 'path': '/', 'secure': False, 'value': 'true'}, {'domain': '.lawsdata.com', 'httpOnly': False, 'name': 'Hm_lpvt_e484b393f62b648c74a7d2bc1605083c', 'path': '/', 'secure': False, 'value': '1557751441'}]

class LegalDocCrawler():
    def __init__(self, browser):
        self.proxy = None
        self.counter = 0
        self.browser = browser
        self.browser.implicitly_wait(10)
        self.fileCouter = 0

    def instructionalCase_parse(self, htmlText):
        # param:
        # htmlText is the source code html of the instructionalCase
        # return:
        # title, title of the desicisiontext; 
        # caseFacts;
        # isSimple, Function or not

        soup = BeautifulSoup(htmlText, 'lxml')
        # find paragraph range of case facts
        # tag begin & end corresponding to the index of where to find the range
        TAG_BEGIN = 3
        TAG_END   = 4 
        listOfSeg = []
        for line in soup.find_all('a'):
            if line.get('data-target-id'):
                listOfSeg.append(line.get('data-target-id'))
        beginPid = re.findall('seg(\d*)' , listOfSeg[TAG_BEGIN])
        endPid =  re.findall('seg(\d*)' , listOfSeg[TAG_END]) 

        beginPid = int(beginPid)
        endPid = int(endPid)
        i = beginPid+1
        caseFacts = ''
        for para in soup.find_all('p'):
            if i >= endPid:
                break
            pid = 'paragraph'+str(i)
            if para.get('id') == pid:
                caseFacts = caseFacts + para.text + '\n'
                i += 1

        title = soup.title.text
        # Or use another function to parse whether it is a simple fnuction or not
        isSimple = (soup.text.find('适用简易程序') > 0)

        return title, caseFacts, isSimple
        
    def go_url(self, url):
        self.browser.get(url)
        
    def go_next_page(self):
        '''
        let the crawler load the next page
        '''
        results = self.browser.find_element_by_id('pageDiv')
        for r in results.find_elements_by_tag_name('a'):
            if r.get_attribute('rel') == 'next':
                r.click()
                return
    
    def go_pageNo(self, pageNo):                         
        results = self.browser.find_element_by_id('pageDiv')         
        Nolist = str.split(results.text, '\n')                  
        while pageNo > int(Nolist[-2]):                            
            result = results.find_elements_by_tag_name('a')[-2]  
            result.click()
            time.sleep(SLEEPTIME)
            results = self.browser.find_element_by_id('pageDiv')         
            Nolist = str.split(results.text, '\n')

        else:                                                   
            while pageNo > self.get_currentPageNo():
                self.go_next_page()
                time.sleep(SLEEPTIME)  
    
    
    def get_currentPageNo(self):
        pageNo = -1
        if self.is_element_exist(By.ID, 'pageDiv'):
            result = self.browser.find_element_by_id('pageDiv')
            pageNo = result.find_element_by_class_name('active').text
        else:
            print('Not a Searching page!')
        return int(pageNo)


    def get_all_pageidName(self):
        """
        get all the legaldoc's id& title in current searching page
        
        return:
        tuple lise with tuple like(id, name)
        """
        pageidNames = []
        results = self.browser.find_elements_by_class_name('detail-instrument-link')
        for r in results:
            docName = r.text
            docPid = re.findall('.*=(.*)&.*', r.get_attribute('href') )[0]
            pageidNames.append((docPid, docName) )
        return pageidNames
    
    def is_element_exist(self, byType, locator):
        try:
            self.browser.find_element(byType, locator)
            return True
        except selenium.common.exceptions.NoSuchElementException:
            return False


    def legaldoc_dict_parse(self, docId=None, docName=None):
        """
        if current page is a legal, parse & transfer to a json txt

        return: legaldoc's corresponding content dict
        """
        pageContents = {}
        pageContents['id'] = docId
        pageContents['docName'] = docName
        # 案件基本属性
        # 审理法院
        if self.is_element_exist(By.CLASS_NAME, 'detail-court'):
            pageContents['court'] = self.browser.find_element_by_class_name('detail-court').text
        # 案号
        if self.is_element_exist(By.CLASS_NAME, 'detail-caseNo'):
            pageContents['caseNo'] = self.browser.find_element_by_class_name('detail-caseNo').text
        # 案件类型 刑事、民事、行政等
        if self.is_element_exist(By.CLASS_NAME, 'detail-caseType'):
            pageContents['caseType'] = self.browser.find_element_by_class_name('detail-caseType').text
        # 文书类型 裁决书，决定书等
        if self.is_element_exist(By.CLASS_NAME, 'detail-instrumentTypeId'):
            pageContents['instrumentType'] = self.browser.find_element_by_class_name('detail-instrumentTypeId').text
        # 案由
        if self.is_element_exist(By.CLASS_NAME, 'detail-reason'):
            pageContents['reason'] = self.browser.find_element_by_class_name('detail-reason').text
        # 审理程序
        if self.is_element_exist(By.CLASS_NAME, 'detail-procedureId'):
            pageContents['procedureId'] = self.browser.find_element_by_class_name('detail-procedureId').text
        # 参考类型
        if self.is_element_exist(By.CLASS_NAME, 'detail-referencedType'):
            pageContents['referenceType'] = self.browser.find_element_by_class_name('detail-referencedType').text
        # 裁判日期
        if self.is_element_exist(By.CLASS_NAME, 'detail-judgementDateStart'):
            pageContents['judgementDateStart'] = self.browser.find_element_by_class_name('detail-judgementDateStart').text

        # 提取案件信息
        segs = []
        result = self.browser.find_element_by_class_name('todo-project-list')
        for r in result.find_elements_by_tag_name('a'):
            segNo = re.findall('seg(.*)', r.get_attribute('data-target-id') )[0]
            segName = r.text
            segs.append((segNo, segName) )

        
        for i in range(len(segs) ):
            PARAPREFIX = 'paragraph'
            p = int(segs[i][0])

            content = ''
            if i < len(segs)-1:
                while p < int(segs[i+1][0]):
                    paraId = PARAPREFIX + str(p)
                    if self.is_element_exist(By.ID, paraId):
                        content += self.browser.find_element_by_id(paraId).text + '\n'
                    p += 1

            else:
                paraId = PARAPREFIX+str(p)
                # some doc's segnum is not the first para no of content, and needed +1
                # e.g. seg3 -> start at para4
                if not self.is_element_exist(By.ID, paraId):
                    p += 1
                    paraId = PARAPREFIX + str(p)

                while self.is_element_exist(By.ID, paraId):
                    content += self.browser.find_element_by_id(paraId).text + '\n'
                    p += 1
                    paraId = PARAPREFIX + str(p)
            pageContents[segs[i][1] ] = content
        
        return pageContents

                
    def go_legalDoc_page(self, docId):
        PAGEPREFIX = 'http://www.lawsdata.com/detail?id='
        pageURL = PAGEPREFIX + docId
        self.browser.get(pageURL)
        return

    def write_dict2json(self, dictContent, fileName):
        with open(fileName, 'a') as file:
            file.write(json.dumps(dictContent) )
        return

    

if __name__ == "__main__":
    """
    temp crawler fun, use python crawler.py to run
    simple function url http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjnroDmmJPnqIvluo8ifV0sInJlZmVyZW5jZWRUeXBlIjpbIjEwIiwiNjAiXSwiZnV6enlNZWFzdXJlIjoiMCJ9LCJzbSI6eyJ0ZXh0U2VhcmNoIjpbInNpbmdsZSJdLCJsaXRpZ2FudFNlYXJjaCI6WyJwYXJhZ3JhcGgiXX19&s= 
    normal function url http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjmma7pgJrnqIvluo8ifV0sInJlZmVyZW5jZWRUeXBlIjpbIjEwIiwiNjAiXSwiZnV6enlNZWFzdXJlIjoiMCJ9LCJzbSI6eyJ0ZXh0U2VhcmNoIjpbInNpbmdsZSJdLCJsaXRpZ2FudFNlYXJjaCI6WyJwYXJhZ3JhcGgiXX19&s=
    """
    urlDict = {
        'simpleFun2018':'http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjnroDmmJPnqIvluo8ifV0sImp1ZGdlbWVudFllYXIiOiIyMDE4LTIwMTgiLCJmdXp6eU1lYXN1cmUiOiIwIn0sInNtIjp7InRleHRTZWFyY2giOlsic2luZ2xlIl0sImxpdGlnYW50U2VhcmNoIjpbInBhcmFncmFwaCJdfX0=&s=',
        'simpleFun2017':'http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjnroDmmJPnqIvluo8ifV0sImp1ZGdlbWVudFllYXIiOiIyMDE3LTIwMTciLCJmdXp6eU1lYXN1cmUiOiIwIn0sInNtIjp7InRleHRTZWFyY2giOlsic2luZ2xlIl0sImxpdGlnYW50U2VhcmNoIjpbInBhcmFncmFwaCJdfX0=&s=',
        'simpleFun2016':'http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjnroDmmJPnqIvluo8ifV0sImp1ZGdlbWVudFllYXIiOiIyMDE2LTIwMTYiLCJmdXp6eU1lYXN1cmUiOiIwIn0sInNtIjp7InRleHRTZWFyY2giOlsic2luZ2xlIl0sImxpdGlnYW50U2VhcmNoIjpbInBhcmFncmFwaCJdfX0=&s=',
        'normalFun2018':'http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLmma7pgJrnqIvluo8ifV0sImp1ZGdlbWVudFllYXIiOiIyMDE4LTIwMTgiLCJmdXp6eU1lYXN1cmUiOjB9LCJzbSI6eyJ0ZXh0U2VhcmNoIjpbInNpbmdsZSJdLCJsaXRpZ2FudFNlYXJjaCI6WyJwYXJhZ3JhcGgiXX19&s='
    }
    target_name = 'normalFun2018'
    fileName = target_name+'.json'
    url = urlDict[target_name ]
    use_cookie = True
    with open(fileName, 'a', encoding='utf-8') as f:
        idCraw = LegalDocCrawler(webdriver.Chrome() )
        doCraw = LegalDocCrawler(webdriver.Chrome() )
        idCraw.go_url(url)
        doCraw.go_url(url)
        if use_cookie:
            # 利用cookie加载登录信息
            for ck in SIGNINCOOKIES:
                idCraw.browser.add_cookie(ck)
                doCraw.browser.add_cookie(ck)
            idCraw.go_url(url)
            doCraw.go_url(url)
        
        else:
            # 手动登陆账号
            time.sleep(30)

        while doCraw.counter < 500000:
            crawList = idCraw.get_all_pageidName()
            print('crawling page No.{}.\nHave Finished {} docs'.format(idCraw.get_currentPageNo(), doCraw.counter ) ) 
            idCraw.go_next_page()
            idCraw.counter += 1

            for idName in crawList:
                doCraw.go_legalDoc_page(idName[0] )
                #time.sleep(2)
                pageContent = doCraw.legaldoc_dict_parse(idName[0], idName[1])
                f.write(json.dumps(pageContent, ensure_ascii=False)+'\n')
                print('Finish docId:{}: {}'.format(idName[0], idName[1]))
                #time.sleep(SLEEPTIME)
            doCraw.counter += 10
            
        doCraw.browser.quit()
        idCraw.browser.quit()

