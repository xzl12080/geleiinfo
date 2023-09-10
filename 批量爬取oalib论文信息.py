import json
import requests
import re
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/pachong',methods=['GET'])
def 批量爬取oalib论文():
    keywords = request.args.get('keywords')
    pagenum = request.args.get('page_num')
    list_all = []
    for i in range(int(pagenum)):
        url = 'https://www.oalib.com/search'
        param = {
            'kw': keywords,
            'pageNo': i
        }
        head = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183'
        }
        res = requests.get(url=url, params=param, headers=head)
        soup = BeautifulSoup(res.text, 'lxml')

        pdf_journal_list = []
        for i in range(len(soup.findAll('a', attrs={'style': 'font-weight: bold;'}))):
            pdf_journal = soup.findAll('a', attrs={'style': 'font-weight: bold;'})[i]['href']
            # 判断论文是否能直接获得pdf的url地址
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                pdf_journal_list.append('https:'+ pdf_journal)

        pdf_title_list = []
        for i in range(len(soup.findAll('span', attrs={'style': 'font-size: 16px;'}))):
            pdf_title = soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                pdf_title_list.append(pdf_title[:-8])

        """
        此方法需要不断从主网页获取进入次网页的链接，再进入次网页获取doi，时间复杂度太高，算力太大
        """
        # pdf_doi_list = []
        # for i in pdf_journal_list:
        #     response = requests.get(i,headers=head)
        #     souper = BeautifulSoup(response.text,'lxml')
        #     pdf_doi = souper.findAll('a', attrs={'style': 'color:#FF3300'})[0]['href']
        #     pdf_doi_list.append(pdf_doi)
        # print(pdf_doi_list)

        # # 获取论文doi
        # t3 = time.time()
        attrs = {'style': 'padding: 10px 0 10px 5px; border-bottom: solid 1px #c0c0c0; font-size: 14px;width: 720px'}
        pdf_doi_list = []
        for i in range(len(soup.findAll('td',attrs=attrs))):
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                pre_doi = soup.findAll('td',attrs=attrs)[i].text
                patt = 'DOI.*\d'
                pre_doi = re.findall(patt,pre_doi)
                pdf_doi = pre_doi[0][5:]
                pdf_doi_list.append('http://dx.doi.org/'+pdf_doi)

        middle_date = soup.findAll('td', attrs={'style': 'padding: 10px 0 10px 5px; border-bottom: solid 1px #c0c0c0; font-size: 14px;width: 720px'})
        pdf_date_list = []
        for i in range(len(middle_date)):
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                patt = '\d\d\d\d'
                pdf_date = re.findall(patt,middle_date[i].text)[0]
                pdf_date_list.append(pdf_date)

        middle_abstract = soup.findAll('td',attrs={'style':'padding: 10px 0 10px 5px; border-bottom: solid 1px #c0c0c0; font-size: 14px;width: 720px'})
        pdf_abstract_list = []
        for i in range(len(middle_abstract)):
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                pdf_abstract = middle_abstract[i].div.text.split('\t')[-1]
                pdf_abstract_list.append(pdf_abstract.replace('\n',' '))

        pdf_authors_list = []
        middle_author = soup.findAll('span', attrs={'class': 'authorLimit'})
        for i in range(len(middle_author)):
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                pdf_authors = middle_author[i].text
                pdf_authors_list.append(pdf_authors)


        middle_url = soup.findAll('span',attrs={'style':'font-size: 16px;'})
        pdf_url_list = []
        for i in range(len(middle_url)):
            if 'PDF' in soup.findAll('span', attrs={'style': 'font-size: 16px;'})[i].text:
                patt = 'http.*\d'
                pdf_url = re.findall(patt,str(middle_url[i]))[0]
                pdf_url_list.append(pdf_url)


        for i in range(len(pdf_journal_list)):
            dic = {}
            dic['title'] = pdf_title_list[i]
            # 先检查列表长度，确保索引不会超出范围
            if i < len(pdf_authors_list):
                dic['authors'] = pdf_authors_list[i]
            else:
                dic['authors'] = "作者信息未提供"
            dic['abstract'] = pdf_abstract_list[i]
            dic['url'] = pdf_url_list[i]
            dic['date'] = pdf_date_list[i]
            list_all.append(dic)
    if None in list_all:
        return jsonify({'success': 'false', 'code': 20001, 'message': "失败", 'data': None})
    else:
        return jsonify({'success':'true','code': 20000, 'message': "成功", 'data': {"result":list_all}})

app.run(host='0.0.0.0',port=8888)

