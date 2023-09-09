import bs4
from bs4 import BeautifulSoup
import requests
head = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"
}
for start_num in range(0,250,25):
    res = requests.get(f'https://movie.douban.com/top250?start={start_num}&filter=',headers=head).text
    html = BeautifulSoup(res,'html.parser')
    for title in html.findAll('span',attrs={'class':'title'}):
        if "/" not in title.string:
            print(title.string)



