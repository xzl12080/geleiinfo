import json

from flask import Flask, jsonify,request
import fitz
import requests
import uuid
from finally_Extract_PDF import 解析PDF
import os
app = Flask(__name__)
#下载地址

@app.route('/pdftest', methods=['GET'])
def parse_pdf():
    result = []
    Download_addres = request.args.getlist('path')
    print(Download_addres)
    for file_name in Download_addres:
        print(file_name)
        # 生成一个随机字符串
        uuid_str = uuid.uuid4().hex
        down_path = "C:\\Users\\Administrator\\Desktop\\Down\\"+uuid_str+".pdf"
        f = requests.get(file_name)
        #下载文件
        with open(down_path, "wb") as code:
            code.write(f.content)

        #pdf = fitz.open(down_path)  # pdf文档2
        #text_list = [page.get_text() for page in pdf]
        # text_list=解析PDF("E:\desk\down")
        text_list = 解析PDF("C:\\Users\\Administrator\\Desktop\\Down",50)
        os.remove(down_path)
        result.append(text_list)


    return json.dumps({'code': "1", 'msg': "成功", 'data': result},ensure_ascii=False)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8802, debug=True)