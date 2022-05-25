# -*- coding: utf-8 -*-
from unit import Args, baidu_trans

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as Exceptions

import datetime


def build_graph_from_title(title: str, args: Args):
    args.log.append(f'Build graph from title: {title}')
    try:
        # 关系图链接
        res = args.sqlite.select_url_from_paper(title)
        if len(res) != 0:
            url = res[0][0]
            args.driver.get(url)
        else:
            # 访问搜索首页
            args.driver.get('https://www.connectedpapers.com/')

            # 输入标题
            search_bar = WebDriverWait(driver=args.driver, timeout=args.wait_time, poll_frequency=0.5).until(
                EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[2]/div/div[1]/div/div/div[1]/div/form/input'))
            )
            search_bar.clear()
            search_bar.send_keys(title)
            # driver.find_elements(By.ID, 'searchbar-input')[1].send_keys(title)

            # 点击搜索
            WebDriverWait(driver=args.driver, timeout=args.wait_time, poll_frequency=0.5).until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="desktop-app"]/div[2]/div/div[1]/div/div/div[1]/button')
                )
            ).click()
            # driver.find_element(
            #     By.XPATH,
            #     '//*[@id="desktop-app"]/div[2]/div/div[1]/div/div/div[1]/button').click()

            # print(driver.current_url)

            # 跳转到搜索结果页面
            res = WebDriverWait(driver=args.driver, timeout=args.wait_time, poll_frequency=0.5).until(
                EC.visibility_of_all_elements_located((By.TAG_NAME, "article"))
            )
            # res = driver.find_elements(By.TAG_NAME, "article")

            if len(res) != 0:
                # 访问第一个搜索结果
                res[0].click()

                # 当前关系图链接
                # url = driver.current_url

            else:
                args.log.append(f'Warning: without graph information. {title}')
                return []

        # 根据链接爬信息
        return paper_graph_information(args)

    except Exceptions.NoSuchElementException as _:
        args.log.append(f'Warning(build_graph_from_title): paper title: {title}')
        return []
    except Exceptions.TimeoutException as _:
        args.log.append(f'Warning(build_graph_from_title): url failed(TimeoutException) {args.wait_time}')
        return []


def paper_graph_information(args: Args):
    try:
        args.log.append(f'Paper graph information: {args.driver.current_url}')

        # 相关文献信息
        papers = WebDriverWait(driver=args.driver, timeout=args.wait_time, poll_frequency=0.5).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'authors'))
            )

        today = datetime.datetime.today()
        paper_connection = []

        # 会有某个元素缺失的现象，导致失败，比如没有摘要
        # https://www.connectedpapers.com/main/68f8aa2f5b59232a4e009f46566b4cb591276b97/Improved-solubility-of-TEV-protease-by-directed-evolution./graph
        for index, paper in enumerate(papers):
            paper_info = []

            # 鼠标移动到论文上来，以显示详细信息
            ActionChains(args.driver).move_to_element(paper).perform()

            # 标题 同时获取 semantic_scholar_url
            a = WebDriverWait(driver=args.driver, timeout=args.wait_time, poll_frequency=0.5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[1]/div/a')
                )
            )
            # a = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[1]/div/a')
            title = a.text.strip()
            title = title.replace('"', '')
            # if title[-1] == '.':
            #     title = title[:-1]

            # 检查, 如果第一个标题在图里，直接返回数据
            if index == 0 and args.sqlite.check_title_is_exists_in_graph(title):
                return args.sqlite.select_connection_from_graph(title)

            # 翻译
            semantic_scholar_url = a.get_attribute("href")
            paper_info.append(title)
            paper_connection.append(title)
            # print(title)

            # 如果已经有了，跳过
            if args.sqlite.check_title_is_exists(title):
                continue

            # 作者
            div = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div/div')
            author = div.text.strip()
            paper_info.append(author)

            # year journal: 他俩之间可能是逗号，空格分割，或者只有年份没有期刊
            # //*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[3]/div[1]
            div = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[3]/div[1]')
            text = div.text.strip()
            if len(text) <= 4:
                year = text
                journal = ""
            else:
                index_t = 4
                year = text[:index_t].strip()
                journal = text[index_t+1:].strip()
            paper_info.append(year)

            # journal
            paper_info.append(journal)

            # 引用
            div = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[4]/div[1]')
            text = div.text.strip()
            index_t = text.find(' ')
            citations = text[:index_t].strip()
            paper_info.append(citations)

            # 年均引用
            curr_year = today.year  # int type
            try:
                year = int(year)
                citations = int(citations)
                year_citations = citations / (curr_year - year)
            except ValueError:
                year_citations = -1
            except ZeroDivisionError:
                year_citations = citations

            paper_info.append(str(round(year_citations, 2)))

            # 关系图链接
            a = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[5]/a')
            connected_papers_url = a.get_attribute("href").strip()
            paper_info.append(connected_papers_url)

            # Semantic Scholar 链接
            paper_info.append(semantic_scholar_url)

            # 文章发布页面
            a = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[5]/a[3]')
            publisher_page_url = a.get_attribute("href").strip()
            paper_info.append(publisher_page_url)

            # 部分文章没有摘要
            try:
                div = args.driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[6]')
                abstract = div.text.strip()
                abstract = abstract.replace('"', '')
                abstract = abstract.replace('\n', '')
            except Exceptions.NoSuchElementException as _:
                abstract = ''
            paper_info.append(abstract)

            # 加入翻译
            if args.is_zh:
                title_zh = baidu_trans(title)
                abstract_zh = baidu_trans(abstract)

                paper_info.append(title_zh)
                paper_info.append(abstract_zh)
            else:
                paper_info.append('')
                paper_info.append('')

            args.sqlite.insert_paper(paper_info)

        if len(paper_connection) != 41:
            args.log.append(f'Warning(paper_graph_information): paper connection number is not 41!')
            return []

        # 插入
        args.sqlite.insert_connection(paper_connection)

        # 返回信息
        return args.sqlite.select_connection_from_graph(paper_connection[0])

    except Exceptions.NoSuchElementException as _:
        args.log.append(f'Warning(paper_graph_information): url failed(NoSuchElementException)')
        return []

    except Exceptions.TimeoutException as _:
        args.log.append(f'Warning(paper_graph_information): url failed(TimeoutException) {args.wait_time}')
        return []


def bfs(titles: list, args: Args):
    """
    :func 建图建完整，扩展的时候再根据筛选条件决定是否扩展
    """
    args.log.append('--- Start bfs() ---')

    # 规范标题
    standard_titles = set()
    for index, item in enumerate(titles):
        # 列表作为队列，集合作为已访问，字典记录层数
        queue, looked, layer = [item], set(item), {item: 0}
        standard_titles.add(item)

        while len(queue) > 0:
            title = queue.pop(0)

            args.log.append(f'Title: {index + 1}-{layer.get(title, 0) + 1}, {title}')

            # 查找相邻节点
            res = args.sqlite.select_connection_from_graph(title)
            if len(res) == 0:
                # 没有这个图，新建一个
                res = build_graph_from_title(title, args)

                if len(res) == 0:
                    # 真没有
                    args.log.append(f'Warning: no connection({title})')
                    continue
                else:
                    args.log.append(f'Info: build finish({res[0][0]})')
                    if item == title:  # 是初始标题
                        standard_titles.remove(item)
                        standard_titles.add(res[0][0])

            # 查找相邻节点，41个节点
            nodes = res[0]

            # 检测节点
            for node in nodes:
                if args.check_is_keyword_in_strings(node):
                    if node not in looked and node != title:
                        if layer.get(title, 0) < args.iteration - 1:
                            layer[node] = layer.get(title, 0) + 1
                            queue.append(node)
                            looked.add(node)

    # 将规范标题写入新文件
    with open(args.paper_title_file, 'w', encoding='utf-8') as w:
        for item in standard_titles:
            w.write(f'{item}\n')


def spider(args: Args):
    # 读取目录文件
    titles = []
    with open(args.paper_title_file, 'r', encoding='utf-8') as r:
        lines = r.readlines()
        for line in lines:
            if len(line.strip()) == 0:
                continue
            titles.append(line.strip())

    bfs(titles, args)

    args.log.append("spider finish.")
    pass

