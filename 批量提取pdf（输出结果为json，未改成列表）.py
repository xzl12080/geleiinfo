import json
from nltk.tokenize import word_tokenize
from 按token切割段落 import breakdown_txt_to_satisfy_token_limit_for_pdf
import os



# 转化为json格式，其中key为\n\n#后的文字，value为\n\n后的文字
def text_convert_json(text):
    paragraphs = text.split('\n\n')
    data = {}
    for i in range(len(paragraphs)):
        if paragraphs[i].startswith('#'):
            key = paragraphs[i][1:].strip()
            value = paragraphs[i+1].strip()
            data[key] = value
    json_data = json.dumps(data, ensure_ascii=False)
    return json_data

def count_tokens(text):
    tokens = word_tokenize(text)
    token_count = len(tokens)
    return token_count

def extract_pdf_path(file_manifest):
    file_name = []
    for root, dirs, files in os.walk(file_manifest):
        for file_manifest in files:
            path = os.path.join(root, file_manifest)
            file_name.append(path)
    return file_name
# def 解析PDF(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
def read_and_clean_pdf_text(fp):

    """
    这个函数用于分割pdf，用了很多trick，逻辑较乱，效果奇好

    **输入参数说明**
    - `fp`：需要读取和清理文本的pdf文件路径

    **输出参数说明**
    - `meta_txt`：清理后的文本内容字符串
    - `page_one_meta`：第一页清理后的文本内容列表

    **函数功能**
    读取pdf文件并清理其中的文本内容，清理规则包括：
    - 提取所有块元的文本信息，并合并为一个字符串
    - 去除短块（字符数小于100）并替换为回车符
    - 清理多余的空行
    - 合并小写字母开头的段落块并替换为空格
    - 清除重复的换行
    - 将每个换行符替换为两个换行符，使每个段落之间有两个换行符分隔
    """
    import fitz, copy
    import re
    import numpy as np
    from colorful import print亮黄, print亮绿
    fc = 0  # Index 0 文本
    fs = 1  # Index 1 字体
    fb = 2  # Index 2 框框
    REMOVE_FOOT_NOTE = True  # 是否丢弃掉 不是正文的内容 （比正文字体小，如参考文献、脚注、图注等）
    REMOVE_FOOT_FFSIZE_PERCENT = 0.95  # 小于正文的？时，判定为不是正文（有些文章的正文部分字体大小不是100%统一的，有肉眼不可见的小变化）

    def primary_ffsize(l):
        """
        提取文本块主字体
        """
        fsize_statiscs = {}
        for wtf in l['spans']:
            if wtf['size'] not in fsize_statiscs: fsize_statiscs[wtf['size']] = 0
            fsize_statiscs[wtf['size']] += len(wtf['text'])
        return max(fsize_statiscs, key=fsize_statiscs.get)

    def ffsize_same(a, b):
        """
        提取字体大小是否近似相等
        """
        return abs((a - b) / max(a, b)) < 0.02

    with fitz.open(fp) as doc:
        meta_txt = []
        meta_font = []

        meta_line = []
        meta_span = []
        ############################## <第 1 步，搜集初始信息> ##################################
        for index, page in enumerate(doc):
            # file_content += page.get_text()
            text_areas = page.get_text("dict")  # 获取页面上的文本信息
            for t in text_areas['blocks']:
                if 'lines' in t:
                    pf = 998
                    for l in t['lines']:
                        txt_line = "".join([wtf['text'] for wtf in l['spans']])
                        if len(txt_line) == 0: continue
                        pf = primary_ffsize(l)
                        meta_line.append([txt_line, pf, l['bbox'], l])
                        for wtf in l['spans']:  # for l in t['lines']:
                            meta_span.append([wtf['text'], wtf['size'], len(wtf['text'])])
                    # meta_line.append(["NEW_BLOCK", pf])
            # 块元提取                           for each word segment with in line                       for each line         cross-line words                          for each block
            meta_txt.extend([" ".join(["".join([wtf['text'] for wtf in l['spans']]) for l in t['lines']]).replace(
                '- ', '') for t in text_areas['blocks'] if 'lines' in t])
            meta_font.extend([np.mean([np.mean([wtf['size'] for wtf in l['spans']])
                                       for l in t['lines']]) for t in text_areas['blocks'] if 'lines' in t])
            if index == 0:
                page_one_meta = [" ".join(["".join([wtf['text'] for wtf in l['spans']]) for l in t['lines']]).replace(
                    '- ', '') for t in text_areas['blocks'] if 'lines' in t]

        ############################## <第 2 步，获取正文主字体> ##################################
        fsize_statiscs = {}
        for span in meta_span:
            if span[1] not in fsize_statiscs: fsize_statiscs[span[1]] = 0
            fsize_statiscs[span[1]] += span[2]
        main_fsize = max(fsize_statiscs, key=fsize_statiscs.get)
        if REMOVE_FOOT_NOTE:
            give_up_fize_threshold = main_fsize * REMOVE_FOOT_FFSIZE_PERCENT

        ############################## <第 3 步，切分和重新整合> ##################################
        mega_sec = []
        sec = []
        for index, line in enumerate(meta_line):
            if index == 0:
                sec.append(line[fc])
                continue
            if REMOVE_FOOT_NOTE:
                if meta_line[index][fs] <= give_up_fize_threshold:
                    continue
            if ffsize_same(meta_line[index][fs], meta_line[index - 1][fs]):
                # 尝试识别段落
                if meta_line[index][fc].endswith('.') and \
                        (meta_line[index - 1][fc] != 'NEW_BLOCK') and \
                        (meta_line[index][fb][2] - meta_line[index][fb][0]) < (
                        meta_line[index - 1][fb][2] - meta_line[index - 1][fb][0]) * 0.7:
                    sec[-1] += line[fc]
                    sec[-1] += "\n\n"
                else:
                    sec[-1] += " "
                    sec[-1] += line[fc]
            else:
                if (index + 1 < len(meta_line)) and \
                        meta_line[index][fs] > main_fsize:
                    # 单行 + 字体大
                    mega_sec.append(copy.deepcopy(sec))
                    sec = []
                    sec.append("# " + line[fc])
                else:
                    # 尝试识别section
                    if meta_line[index - 1][fs] > meta_line[index][fs]:
                        sec.append("\n" + line[fc])
                    else:
                        sec.append(line[fc])
        mega_sec.append(copy.deepcopy(sec))

        finals = []
        for ms in mega_sec:
            final = " ".join(ms)
            final = final.replace('- ', ' ')
            finals.append(final)
        meta_txt = finals

        ############################## <第 4 步，乱七八糟的后处理> ##################################
        def 把字符太少的块清除为回车(meta_txt):
            for index, block_txt in enumerate(meta_txt):
                if len(block_txt) < 100:
                    meta_txt[index] = '\n'
            return meta_txt

        meta_txt = 把字符太少的块清除为回车(meta_txt)

        def 清理多余的空行(meta_txt):
            for index in reversed(range(1, len(meta_txt))):
                if meta_txt[index] == '\n' and meta_txt[index - 1] == '\n':
                    meta_txt.pop(index)
            return meta_txt

        meta_txt = 清理多余的空行(meta_txt)

        def 合并小写开头的段落块(meta_txt):
            def starts_with_lowercase_word(s):
                pattern = r"^[a-z]+"
                match = re.match(pattern, s)
                if match:
                    return True
                else:
                    return False

            for _ in range(100):
                for index, block_txt in enumerate(meta_txt):
                    if starts_with_lowercase_word(block_txt):
                        if meta_txt[index - 1] != '\n':
                            meta_txt[index - 1] += ' '
                        else:
                            meta_txt[index - 1] = ''
                        meta_txt[index - 1] += meta_txt[index]
                        meta_txt[index] = '\n'
            return meta_txt

        meta_txt = 合并小写开头的段落块(meta_txt)
        meta_txt = 清理多余的空行(meta_txt)

        meta_txt = '\n'.join(meta_txt)
        # 清除重复的换行
        for _ in range(5):
            meta_txt = meta_txt.replace('\n\n', '\n')

        # 换行 -> 双换行
        meta_txt = meta_txt.replace('\n', '\n\n')

        # ############################## <第 5 步，展示分割效果> ##################################
        # for f in finals:
        #    print亮黄(f)
        #    print亮绿('***************************')

    # return meta_txt, page_one_meta
    return meta_txt, page_one_meta

def 解析PDF(file_manifest):
    file_text = []
    page_text = []
    for i in range(len(extract_pdf_path(file_manifest))):
        print('开始解析:', extract_pdf_path(file_manifest)[i])
    ############################## <第 0 步，切割PDF> ##################################
    # 递归地切割PDF文件，每一块（尽量是完整的一个section，比如introduction，experiment等，必要时再进行切割）
        # 的长度必须小于 2500 个 Token
        file_content, page_one = read_and_clean_pdf_text(extract_pdf_path(file_manifest)[i])  # （尝试）按照章节切割PDF
        file_content = file_content.encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars
        page_one = str(page_one).encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars
        file_text.append(file_content)
        page_text.append(page_one)

        # TOKEN_LIMIT_PER_FRAGMENT = 1500
        #
        # paper_fragments = breakdown_txt_to_satisfy_token_limit_for_pdf(
        #     txt=file_content, get_token_fn=count_tokens, limit=TOKEN_LIMIT_PER_FRAGMENT)
        # page_one_fragments = breakdown_txt_to_satisfy_token_limit_for_pdf(
        #     txt=str(page_one), get_token_fn=count_tokens, limit=TOKEN_LIMIT_PER_FRAGMENT / 4)
        # 为了更好的效果，我们剥离Introduction之后的部分（如果有）
    return file_text
from flask import Flask,request
app = Flask(__name__)
@app.route('/analysis',methods=['GET'])
def finall_function():
    file_manifest = request.args.get('file_manifest')
    file_json = {}
    for i in range(len(解析PDF(file_manifest))):
        file_text = 解析PDF(file_manifest)[i]
        text_middle_json = text_convert_json(file_text)
        file_json.update(json.loads(text_middle_json))
    return json.dumps(file_json,ensure_ascii=False)
app.run(host='0.0.0.0',port=70)


# if __name__ == '__main__':
#     print(解析PDF(r'C:\Users\Administrator\Desktop\PDF'))

