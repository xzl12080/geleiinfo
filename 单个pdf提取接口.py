import fitz
import json
from flask import Flask,request,jsonify
app = Flask(__name__)
@app.route("/pdf_graph",methods=["GET"])
def extract_pdf_to_json():
    file_path = request.args.get("file_path")
    doc = fitz.open(file_path)
    text = ""
    json_dict = {}

    for page in doc:
        text += page.get_text()

    sections = text.split('\n')
    section_title = ''
    section_text = ''
    for section in sections:
        if section.isupper():
            if section_text:
                json_dict[section_title] = section_text.strip()
                section_text = ''
            section_title = section
        else:
            section_text += section + '\n'

    json_dict[section_title] = section_text.strip()

    return json.dumps(json_dict, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=70,debug=True)

