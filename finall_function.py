import json
from collections import OrderedDict
from nltk.tokenize import word_tokenize
import os
import jieba
import re

#切割字符串
def flatten_list(nested_list):
    flattened_list = []
    for item in nested_list:
        if isinstance(item, list):
            flattened_list.extend(flatten_list(item))
        else:
            flattened_list.append([item])
    return flattened_list
def split_string(my_string, max_tokens):
    tokens = word_tokenize(my_string)
    num_tokens = len(tokens)
    num_splits = (num_tokens + max_tokens - 1) // max_tokens
    result = []
    for i in range(num_splits):
        start = i * max_tokens
        end = (i + 1) * max_tokens
        result.append(' '.join(tokens[start:end]))
    return result

def text_convert_dic(text):
    paragraphs = text.split('\n\n')
    data = OrderedDict()  # 使用有序字典
    for i in range(len(paragraphs)):
        if paragraphs[i].startswith('#'):
            if count_tokens_diff(paragraphs[i][1:]) > 50:
                key = f'段落{i}'
                value = paragraphs[i][1:].strip()
                data[key] = value  # 将键值对添加到有序字典中
            else:
                key = paragraphs[i][1:].strip()
                value = paragraphs[i + 1].strip()
                data[key] = value  # 将键值对添加到有序字典中
    return data

def count_tokens_diff(text):
    def is_english(text):
        return bool(re.match('^[a-zA-Z0-9_]*$', text))
    if is_english(text):
        tokens = word_tokenize(text)
    else:
        tokens = jieba.lcut(text)
    return len(tokens)

def extract_pdf_path(file_folder):
    file_path = []
    for root, dirs, files in os.walk(file_folder):
        for file_name in files:
            path = os.path.join(root, file_name)
            file_path.append(path)
    return file_path
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

def 解析PDF(file_manifest,max_tokens):
    filename_pdftext = []  # 存储每个PDF的文件名和内容
    for i in range(len(extract_pdf_path(file_manifest))):
        # print('开始解析:', extract_pdf_path(file_manifest)[i])
        file_content, page_one = read_and_clean_pdf_text(extract_pdf_path(file_manifest)[i])
        file_content = file_content.encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars
        page_one = str(page_one).encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars

        filename_pdftext.append([os.path.basename(extract_pdf_path(file_manifest)[i]), file_content])

    """
    将标题变成字典的key，对应的内容变成字典的value
    """

    for i in range(len(extract_pdf_path(file_manifest))):
        filename_pdftext[i][1] = text_convert_dic(filename_pdftext[i][1])

    """
    将字典的keys和values都变成对应的列表
    """
    file_text = []
    for i in range(len(filename_pdftext)):
        file_name = filename_pdftext[i][0]
        new_list = [[file_name]]
        for key, value in filename_pdftext[i][1].items():
            # 创建一个新的子列表，将键和值添加到其中

            # 将子列表添加到新列表中
            new_list.append([key])
            new_list.append([value])
        # 将新列表添加到file_text列表中
        file_text.append(new_list)
    """
    将token过多的段落元素切割，也变成列表存放进对应pdf的列表中
    """
    for j in range(len(file_text)):
        for i in range(len(file_text[j])):
            if count_tokens_diff(file_text[j][i][0]) > max_tokens:
                split_string(file_text[j][i][0], max_tokens)
                new_list = []
                for string in split_string(file_text[j][i][0], max_tokens):
                    new_list.append([string])
                file_text[j][i] = new_list
    for i in range(len(file_text)):
        file_text[i] = flatten_list(file_text[i])
    """
    最终输出的文本格式为嵌套式列表，[[pdf1],[pdf2],[pdf3],....]
    每个pdf中的内容也为列表，[pdf1]:[[文件名],[标题1],[内容1],[标题2],[内容2]]，
    """

    return file_text




























