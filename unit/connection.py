# -*- coding: utf-8 -*-
from unit import Args, Sqlite, Log, baidu_trans

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as Exceptions

import datetime


def build_graph_from_title(driver: webdriver, title, sqlite: Sqlite, wait_time, log: Log):
    log.append(f'Build graph from title: {title}')
    try:
        res = sqlite.select_url_from_paper(title)
        if len(res) != 0:
            url = res[0][0]
            driver.get(url)
        else:
            # 访问搜索首页
            driver.get('https://www.connectedpapers.com/')

            # 输入标题
            search_bar = WebDriverWait(driver=driver, timeout=wait_time, poll_frequency=0.5).until(
                EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[2]/div/div[1]/div/div/div[1]/div/form/input'))
            )
            search_bar.clear()
            search_bar.send_keys(title)
            # driver.find_elements(By.ID, 'searchbar-input')[1].send_keys(title)

            # 点击搜索
            WebDriverWait(driver=driver, timeout=wait_time, poll_frequency=0.5).until(
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
            res = WebDriverWait(driver=driver, timeout=wait_time, poll_frequency=0.5).until(
                EC.visibility_of_all_elements_located((By.TAG_NAME, "article"))
            )
            # res = driver.find_elements(By.TAG_NAME, "article")

            if len(res) != 0:
                # 访问第一个搜索结果
                res[0].click()

                # 当前关系图链接
                # url = driver.current_url

            else:
                print(f'Warning: without graph information. {title}')
                return False

        # 根据链接爬信息
        return paper_graph_information(driver, sqlite, wait_time, log)

    except Exceptions.NoSuchElementException as e:
        print(f'warning: paper title: {title}\n{e}')
    except Exceptions.TimeoutException as e:
        print(f'\nwarning: url failed(TimeoutException) {wait_time}\n{e}')


def paper_graph_information(driver: webdriver, sqlite: Sqlite, wait_time, log: Log):
    # log.append(f'Paper graph information: {graph_url}')
    try:
        # 访问网页
        # driver.get(graph_url)
        # print(f'current_url: {driver.current_url}')
        log.append(f'Paper graph information: {driver.current_url}')

        # 相关文献信息
        papers = WebDriverWait(driver=driver, timeout=wait_time, poll_frequency=0.5).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'authors'))
            )
        # papers = driver.find_elements(By.CLASS_NAME, 'authors')
    except Exceptions.NoSuchElementException as _:
        print(f'\nwarning: url failed(NoSuchElementException)')
        return False
    except Exceptions.TimeoutException as _:
        print(f'\nwarning: url failed(TimeoutException) {wait_time}')
        return False

    try:
        today = datetime.datetime.today()
        paper_connection = []
        for index, paper in enumerate(papers):
            paper_info = []

            # 鼠标移动到论文上来，以显示详细信息
            ActionChains(driver).move_to_element(paper).perform()

            # 标题 同时获取 semantic_scholar_url
            a = WebDriverWait(driver=driver, timeout=wait_time, poll_frequency=0.5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[1]/div/a')
                )
            )
            # a = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[1]/div/a')
            title = a.text.strip()
            title = title.replace('"', '')
            title = title.replace('.', '')
            # 翻译
            title_zh = baidu_trans(title)
            semantic_scholar_url = a.get_attribute("href")
            paper_info.append(title)
            paper_connection.append(title)
            # print(title)

            # 如果已经有了，跳过
            if sqlite.check_title_is_exists(title):
                continue

            # 作者
            div = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div/div')
            author = div.text.strip()
            paper_info.append(author)

            # year journal: 他俩之间可能是逗号，空格分割，或者只有年份没有期刊
            # //*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[3]/div[1]
            div = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[3]/div[1]')
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
            div = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[4]/div[1]')
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
            a = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[5]/a')
            connected_papers_url = a.get_attribute("href").strip()
            paper_info.append(connected_papers_url)

            # Semantic Scholar 链接
            paper_info.append(semantic_scholar_url)

            # 文章发布页面
            a = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[5]/a[3]')
            publisher_page_url = a.get_attribute("href").strip()
            paper_info.append(publisher_page_url)

            #
            div = driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[6]')
            abstract = div.text.strip()
            abstract = abstract.replace('"', '')
            abstract = abstract.replace('\n', '')
            # 翻译
            abstract_zh = baidu_trans(abstract)
            # print(abstract)
            # print(driver.find_element(By.XPATH, '//*[@id="desktop-app"]/div[2]/div[3]/div[3]/div/div[2]/div[6]/text()'))
            paper_info.append(abstract)

            # 加入翻译
            paper_info.append(title_zh)
            paper_info.append(abstract_zh)

            sqlite.insert_paper(paper_info)

        if len(paper_connection) != 41:
            log.append(f'Warning: paper connection number is not 41!')
            return False

        sqlite.insert_connection(paper_connection)
        return True

    except Exceptions.NoSuchElementException as _:
        print(f'\nwarning: url failed(NoSuchElementException)')
    except Exceptions.TimeoutException as _:
        print(f'\nwarning: url failed(TimeoutException) {wait_time}')


def bfs(driver: webdriver, titles, iteration, sqlite: Sqlite, wait_time, check_func, log: Log):
    """
    :func 建图建完整，扩展的时候再根据筛选条件决定是否扩展
    """
    log.append('--- Start bfs() ---')

    for index, item in enumerate(titles):
        # 列表作为队列，集合作为已访问，字典记录层数
        queue, looked, layer = [item], set(item), {item: 0}

        while len(queue) > 0:
            title = queue.pop(0)

            log.append(f'Title: {index + 1}-{layer.get(title, 0) + 1}, {title}')

            # 查找相邻节点
            res = sqlite.select_connection_from_graph(title)
            if len(res) == 0:
                # 没有这个图
                if not build_graph_from_title(driver, title, sqlite, wait_time, log):
                    continue

            res = sqlite.select_connection_from_graph(title)
            if len(res) == 0:
                # 真没有
                continue

            # 查找相邻节点，41个节点
            nodes = res[0]

            # 检测节点
            for node in nodes:
                if check_func(node):
                    if node not in looked and node != title:
                        # 子代
                        # layer[node] = layer.get(title, 0) + 1
                        if layer.get(title, 0) < iteration - 1:
                            layer[node] = layer.get(title, 0) + 1
                            queue.append(node)
                            looked.add(node)


def spider(args: Args):
    # 日志对象
    log = args.log

    # 浏览器驱动
    driver = args.driver

    # 数据库对象
    sqlite = Sqlite(args.database)

    # 读取目录文件
    titles = []
    with open(args.paper_title_file, 'r', encoding='utf-8') as r:
        lines = r.readlines()
        for line in lines:
            titles.append(line.strip())

    bfs(driver, titles, args.iteration, sqlite, args.wait_time, args.check_is_keyword_in_strings, log)

    print("spider finish.")
    driver.close()
    pass

