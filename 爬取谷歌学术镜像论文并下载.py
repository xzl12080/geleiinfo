import requests
from bs4 import BeautifulSoup
import os


# query = input('你想要查找什么类型的论文:')
# # query = 'machine learning'
def 爬取谷歌学术pdf并下载(query):
    query = query.replace(' ', '+')
    url = f'https://scholar.lanfanshu.cn/scholar?q={query}'
    res = requests.get(url)
    html = BeautifulSoup(res.text, 'html.parser')
    url_list = []
    for a in html.findAll('a'):
        href = a.get('href')
        if isinstance(href, str):
            if href.startswith("/") or href.startswith('javascript'):
                pass
                # print('无效的链接')
            else:
                if '.pdf' not in href:
                    pass
                else:
                    url_list.append(href)
    #                 print(href)
    #     # print(type(href))
    #
    # # pdf = requests.get(url_list[0])
    # # print(pdf.text)
    # # print(url_list)

    pdf_links = url_list
    download_folder = r'C:\Users\Administrator\Desktop\downloads'  # 下载文件夹路径

    # 如果下载文件夹不存在，则创建它
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    from urllib.parse import urlparse

    # 遍历PDF链接列表并下载每个PDF文件

    for link in pdf_links:
        # 解析链接并去除查询参数
        parsed_link = urlparse(link)
        filename = parsed_link.path.split('/')[-1]
        # # 使用requests库下载PDF文件
        response = requests.get(parsed_link.geturl())
        # 保存文件到本地
        with open(os.path.join(download_folder, filename), 'wb') as f:
            f.write(response.content)
        print(f'Successfully downloaded {filename}!')
print(爬取谷歌学术pdf并下载('机器学习'))

