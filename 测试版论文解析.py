import os
import requests
import uuid
from flask import Flask, jsonify, request
from finally_Extract_PDF import 解析PDF

app = Flask(__name__)


@app.route('/pdftest', methods=['GET'])
def parse_pdf():
    result = []
    Download_addres = request.args.getlist('path')
    print(Download_addres)
    for file_name in Download_addres:
        try:
            print(file_name)
            # 生成一个随机字符串
            uuid_str = uuid.uuid4().hex
            down_path = "C:\\Users\\Administrator\\Desktop\\Down\\" + uuid_str + ".pdf"
            response = requests.get(file_name)

            # Check if the download was successful (status code 200)
            if response.status_code == 200:
                # 下载文件
                with open(down_path, "wb") as code:
                    code.write(response.content)

                # pdf = fitz.open(down_path)  # pdf文档2
                # text_list = [page.get_text() for page in pdf]
                # text_list = 解析PDF("E:\desk\down")
                text_list = 解析PDF("C:\\Users\\Administrator\\Desktop\\Down", 50)
                os.remove(down_path)
                result.append(text_list)
            else:
                # If the download was not successful, append None to the result list
                result.append(None)

        except Exception as e:
            # If an error occurs during the process, append None to the result list
            result.append(None)

    # Check if any items in the result list are None, indicating failures
    if None in result:
        return jsonify({'code': 0, 'msg': "失败", 'data': result})
    else:
        return jsonify({'code': 1, 'msg': "成功", 'data': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)