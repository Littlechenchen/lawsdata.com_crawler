# -*- coding: utf-8 -*-
import requests
import re
import json
import selenium
import time
import base64
from multiprocessing import Pool
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from retrying import retry
from crawler import LegalDocCrawler

SLEEPTIME = 1
SIGNINCOOKIES = [{'domain': 'www.lawsdata.com', 'httpOnly': True, 'name': 'JSESSIONID', 'path': '/', 'secure': False, 'value': '60A135BAFEC4A967683AC774ACC3B1F5'}, {'domain': '.lawsdata.com', 'expiry': 1873696019, 'httpOnly': False, 'name': 'gr_user_id', 'path': '/', 'secure': False, 'value': 'cf900aaf-a24d-465f-a0e0-4cfc9538e476'}, {'domain': '.lawsdata.com', 'expiry': 1558337819, 'httpOnly': False, 'name': 'gr_session_id_9c57f1694d616c90_83475a72-91f1-4f05-b335-7df1daead279', 'path': '/', 'secure': False, 'value': 'true'}, {'domain': '.lawsdata.com', 'expiry': 1589872019, 'httpOnly': False, 'name': 'Hm_lvt_e484b393f62b648c74a7d2bc1605083c', 'path': '/', 'secure': False, 'value': '1558336020'}, {'domain': '.lawsdata.com', 'expiry': 1558337819, 'httpOnly': False, 'name': 'gr_session_id_9c57f1694d616c90', 'path': '/', 'secure': False, 'value': '83475a72-91f1-4f05-b335-7df1daead279'}, {'domain': '.lawsdata.com', 'httpOnly': False, 'name': 'Hm_lpvt_e484b393f62b648c74a7d2bc1605083c', 'path': '/', 'secure': False, 'value': '1558336020'}, {'domain': 'www.lawsdata.com', 'expiry': 1559200036.133683, 'httpOnly': True, 'name': 'bashou', 'path': '/', 'secure': False, 'value': 'oDADH3cXbBGpQtwjStXNLi515TuUvCEKPnYjDLILdi/r9jEKbqndgMxF3yKE90Q0dTfCMczq0GzXWyjj3zwG10BQ1g3ICo+xekw0hjxkI00JyQBFUqSYxPZOOWd32xB2UrCnVKFuigH74L1KBzMDE0AExhE4thuVLNagMpJ+EkAMbAKR+fxjemjgX9h/mucJpxUJ0gFEX6dS7buDzumSUr7FglrReJUPq5GsH++4ebPJ/z3ZgkTOMjggnYvh516JwbqZS0KEVkjdeh3P5vfH/DRTFF5JQyFxpdYa+3rEfT0gWioc/7ImGZh9XP3OL8f/ZnaoCjGgoFIUM5JGnt41BDmDN2ppWFxVKLyJLw25RQHlcLJ4O4+3+BjV/MbHIQNSpVpNYOcKIgMoWkWodsNjeEzSaTAE3J6piyON6Xx5QM1/KGoHNKT7iBYV7zFPTqTwFjqBMGEm3Aa9h7D53UryOlZCLu/6yG9Gu4xDZ6YgO0EUyJB5SoZ1eFaWHd2oJGgmmTz/h1ltSXaLNgLSPx3hfv0/mwNC3XUTWHWvUSZ4UZqCi37G11n+AG01DtVh8tzb'}]
typeReasonDict = {'criminal':[('001005', '侵犯财产'), ('001006', '妨害社会管理秩序'), ('001002', '危害公共安全'), ('001003', '破坏社会主义市场经济秩序'),
  ('001004', '侵犯公民人身权利、民主权利'), ('001008', '贪污贿赂'), ('001009', '渎职'), ('001007', '危害国防利益'), ('001001','危害国家安全')], 
  'civil':[('002004', '合同、无因管理、不当得利纠纷'), ('002009', '侵权责任纠纷'), ('002002', '婚姻家庭、继承纠纷'), ('002006', '劳动争议、人事争议'), 
  ('002003', '物权纠纷'), ('002008', '与公司、证券、保险、票据等有关的民事纠纷'), ('002005', '知识产权与竞争纠'), ('002001', '人格权纠纷'), ('002010', '适用特殊程序案件案由'), ('002007', '海事海商纠纷')],
      'admin':[('003001', '行政管理范围'), ('003002', '行政行为种类')]}
yearList = [2014, 2015, 2016, 2017, 2018]
keywordDict = {'simple':'适用简易程序', 'normal':'普通程序'}
type2No = {'civil':'1', 'criminal':'2', 'admin':'3'}




def url_generator(keyword, caseTypeNo, year, reasonId, reason):
    """
    generate a target urlstr from giving information
    input:
    (str)keyword e.g.'适用简易程序'
    (str)caseTypeNo 1 criminal 2 civil 3 admin
    (int)year e.g 2017 ：case year range yyyy-yyyy
    (str)reasonId a corresponding id to case reason
    (str)reason: case reason under different case type
    """
    urlStr = 'http://www.lawsdata.com/?q='
    pQu = '{"m":"advance","a":{"texts":[{"type":"all","subType":"","value":"'
    pCasetype = '"}],"caseType":["'
    pReasonId = '"],"reasonId":["'
    pJudgeYear= '"],"judgementYear":"'
    pReason = '","fuzzyMeasure":"0","reason":"'
    pEnd = '"},"sm":{"textSearch":["single"],"litigantSearch":["paragraph"]}}'

    keywordStr = pQu + keyword + pCasetype + caseTypeNo + pReasonId + reasonId + pJudgeYear + "{}-{}".format(str(year), str(year) ) + pReason + reason + pEnd
    urlStr += base64.b64encode(keywordStr.encode('utf-8') )

    return urlStr

def single_doc_crawl(doCrawler, idName):
    doCraw.go_legalDoc_page(idName[0] )
    pageContent = doCraw.legaldoc_dict_parse(idName[0], idName[1])
    print('Finish docId:{}: {}'.format(idName[0], idName[1]))
    return json.dumps(pageContent, ensure_ascii=False)+'\n'

if __name__ == "__main__":
    """
    temp crawler fun, use python crawler.py to run
    simple function url http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjnroDmmJPnqIvluo8ifV0sInJlZmVyZW5jZWRUeXBlIjpbIjEwIiwiNjAiXSwiZnV6enlNZWFzdXJlIjoiMCJ9LCJzbSI6eyJ0ZXh0U2VhcmNoIjpbInNpbmdsZSJdLCJsaXRpZ2FudFNlYXJjaCI6WyJwYXJhZ3JhcGgiXX19&s= 
    normal function url http://www.lawsdata.com/?q=eyJtIjoiYWR2YW5jZSIsImEiOnsidGV4dHMiOlt7InR5cGUiOiJhbGwiLCJzdWJUeXBlIjoiIiwidmFsdWUiOiLpgILnlKjmma7pgJrnqIvluo8ifV0sInJlZmVyZW5jZWRUeXBlIjpbIjEwIiwiNjAiXSwiZnV6enlNZWFzdXJlIjoiMCJ9LCJzbSI6eyJ0ZXh0U2VhcmNoIjpbInNpbmdsZSJdLCJsaXRpZ2FudFNlYXJjaCI6WyJwYXJhZ3JhcGgiXX19&s=
    """
    p = Pool(10)
    use_cookie = True
    total_counter = 0
    idCraw = LegalDocCrawler(webdriver.Chrome() )
    doCraw = LegalDocCrawler(webdriver.Chrome() )
    doCraws = [LegalDocCrawler(webdriver.PhantomJS() )]
    idCraw.go_url('http://www.lawsdata.com')
    doCraw.go_url('http://www.lawsdata.com')
     
    if use_cookie:
        # 利用cookie加载登录信息
        for ck in SIGNINCOOKIES:
            idCraw.browser.add_cookie(ck)
            doCraw.browser.add_cookie(ck)
        idCraw.refresh()
        doCraw.refresh()
    
    else:
        # 手动登陆账号
        time.sleep(30)
    for year in yearList:
        for caseType in type2No:
            for keyword in keywordDict:
                target_name = keyword + caseType + str(year)
                fileName = target_name+'.json'
                with open(fileName, 'a', encoding='utf-8') as f:
                    for (reasonId, reason) in typeReasonDict[type2No[caseType] ]:
                        try:
                            url = url_generator(keywordDict[keyword], type2No[caseType], year, reasonId, reason)
                            idCraw.go_url(url)

                            start_page = 1
                            if start_page >1:
                                idCraw.go_pageNo(start_page)

                            while total_counter < 5000000:
                                crawList = idCraw.get_all_pageidName()
                                print('crawling page No.{}.\nHave Finished {} docs'.format(idCraw.get_currentPageNo(), doCraw.counter ) ) 
                                idCraw.go_next_page()
                                idCraw.counter += 1

                                for i,idName in enumerate(crawList):
                                    p.
                                doCraw.counter += 10
                        except selenium.common.exceptions.ElementClickInterceptedException:
                            continue
            
    doCraw.browser.quit()
    idCraw.browser.quit()

