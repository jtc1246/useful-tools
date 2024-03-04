#!/opt/homebrew/bin/python3.9
import pdfplumber  # pip install pdfplumber
import json
from _thread import start_new_thread
import os
import sys
from threading import Lock

cache = {}
CACHE_PATH = './pdf_cache.json'
exit_lock = Lock()


def reorganize_text(text: str):
    text = text.replace('\n\uf06c\n', ' ')
    text = text.replace('\uf06c', ' ')
    text = text.replace('\nq\n', ' ')
    text = text.replace('\nq ', ' ')
    text = text.replace('\n', ' ')
    old = text
    text = text.replace('  ', ' ')
    while old != text:
        old = text
        text = text.replace('  ', ' ')
    if (text == ''):
        return ' '
    if (text[0] != ' '):
        text = ' ' + text
    if (text[-1] != ' '):
        text = text + ' '
    return text


def get_text_from_pdf(file_path: str):
    result = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            text = reorganize_text(text)
            result.append(text)
    return result


def search_default(pdf_text: list[str], text: str) -> bool:
    # 默认, 不区分大小写
    old = text
    text = text.replace('  ', ' ')
    while old != text:
        old = text
        text = text.replace('  ', ' ')
    text = text.lower()
    for page in pdf_text:
        if (page.lower().find(text) != -1):
            return True
    return False


def search_strict(pdf_text: list[str], text: str) -> bool:
    # 区分大小写
    old = text
    text = text.replace('  ', ' ')
    while old != text:
        old = text
        text = text.replace('  ', ' ')
    for page in pdf_text:
        if (page.find(text) != -1):
            return True
    return False


def search_force(pdf_text: list[str], text: str) -> bool:
    # 去除所有空格后搜索, 尽最大可能增加匹配率
    text = text.replace(' ', '').lower()
    for page in pdf_text:
        page = page.replace(' ', '').lower()
        if (page.find(text) != -1):
            return True


def save(cache_path='./pdf_cache.json'):
    with exit_lock:
        with open(cache_path, 'w') as f:
            a = json.dumps(cache, ensure_ascii=False)
            f.write(a)


def save_async(cache_path='./pdf_cache.json'):
    start_new_thread(save, (cache_path,))


def process_result(result: tuple[list[str], list[str], list[str]]) -> None:
    # 注意这个是在原地修改, 不返回任何值
    for i in range(0, 3):
        l = len(result[i])
        for j in range(0, l):
            name = result[i][j]
            if (name.startswith('./')):
                result[i][j] = name[2:]


def search_pdfs(file_paths: list[str], text: str) -> tuple[list[str], list[str], list[str]]:
    result = ([], [], [])
    for file_path in file_paths:
        if (file_path in cache):
            pdf_text = cache[file_path]
        else:
            try:
                pdf_text = get_text_from_pdf(file_path)
            except:
                pdf_text = ''
            cache[file_path] = pdf_text
            save_async(cache_path=CACHE_PATH)
        default = search_default(pdf_text, text)
        strict = search_strict(pdf_text, text)
        force = search_force(pdf_text, text)
        if (default):
            result[0].append(file_path)
        if (strict):
            result[1].append(file_path)
        if (force):
            result[2].append(file_path)
    process_result(result)
    return result


def get_files(dir_path: str) -> list[str]:
    result = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if (file[-4:] == '.pdf'):
                result.append(os.path.join(root, file))
    result.sort()
    return result


try:
    a = sys.argv[1]
except:
    print(f'Usage: {sys.argv[0]} <text> [path]')
    exit(1)
try:
    b=sys.argv[2]
except:
    b='.'

CACHE_PATH = f'./pdf_cache_{b}.json'

try:
    with open(CACHE_PATH, 'r') as f:
        cache = json.loads(f.read())
except:
    pass

d, s, f = search_pdfs(get_files(b), a)
print(f"Searched {len(d)} in default mode, {len(s)} in strict mode, {len(f)} in force mode")
print(' ')
print('Default mode:')
for i in d:
    print(i)
print(' ')
print('Strict mode:')
for i in s:
    print(i)
print(' ')
print('Following are only available in force mode:')
for i in f:
    if (i not in d):
        print(i)

with exit_lock:
    exit(0)
