from read_clean不带接口 import read_and_clean_pdf_text
from nltk.tokenize import word_tokenize
# import nltk
#
#
# nltk.download('punkt')

def count_tokens(text):
    tokens = word_tokenize(text)
    token_count = len(tokens)
    return token_count

def force_breakdown(txt, limit, get_token_fn):
    """
    当无法用标点、空行分割时，我们用最暴力的方法切割
    """
    for i in reversed(range(len(txt))):
        if get_token_fn(txt[:i]) < limit:
            return txt[:i], txt[i:]
    return "Tiktoken未知错误", "Tiktoken未知错误"

def breakdown_txt_to_satisfy_token_limit_for_pdf(txt, get_token_fn, limit):
    # 递归
    def cut(txt_tocut, must_break_at_empty_line, break_anyway=False):
        if get_token_fn(txt_tocut) <= limit:
            return [txt_tocut]
        else:
            lines = txt_tocut.split('\n')
            estimated_line_cut = limit / get_token_fn(txt_tocut) * len(lines)
            estimated_line_cut = int(estimated_line_cut)
            cnt = 0
            for cnt in reversed(range(estimated_line_cut)):
                if must_break_at_empty_line:
                    if lines[cnt] != "":
                        continue
                prev = "\n".join(lines[:cnt])
                post = "\n".join(lines[cnt:])
                if get_token_fn(prev) < limit:
                    break
            if cnt == 0:
                if break_anyway:
                    prev, post = force_breakdown(txt_tocut, limit, get_token_fn)
                else:
                    raise RuntimeError(f"存在一行极长的文本！{txt_tocut}")
            # print(len(post))
            # 列表递归接龙
            result = [prev]
            result.extend(cut(post, must_break_at_empty_line, break_anyway=break_anyway))
            return result
    try:
        # 第1次尝试，将双空行（\n\n）作为切分点
        return cut(txt, must_break_at_empty_line=True)
    except RuntimeError:
        try:
            # 第2次尝试，将单空行（\n）作为切分点
            return cut(txt, must_break_at_empty_line=False)
        except RuntimeError:
            try:
                # 第3次尝试，将英文句号（.）作为切分点
                res = cut(txt.replace('.', '。\n'), must_break_at_empty_line=False) # 这个中文的句号是故意的，作为一个标识而存在
                return [r.replace('。\n', '.') for r in res]
            except RuntimeError as e:
                try:
                    # 第4次尝试，将中文句号（。）作为切分点
                    res = cut(txt.replace('。', '。。\n'), must_break_at_empty_line=False)
                    return [r.replace('。。\n', '。') for r in res]
                except RuntimeError as e:
                    # 第5次尝试，没办法了，随便切一下敷衍吧
                    return cut(txt, must_break_at_empty_line=False, break_anyway=True)

if __name__ == '__main__':
    path = r'C:\Users\Administrator\Desktop\PDF\ChatGPT赋能图书馆知识服务：原理、场景与进路_郭亚军.pdf'
    print(breakdown_txt_to_satisfy_token_limit_for_pdf(read_and_clean_pdf_text(path)[0], get_token_fn=count_tokens,
                                                       limit=1500))






