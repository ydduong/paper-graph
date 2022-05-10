# -*- coding: utf-8 -*-

from unit import Sqlite, Args
import openpyxl


class Write:
    def __init__(self, args: Args):
        self._check_func = args.check_is_keyword_in_strings
        self._excel_file = args.excel_file
        self._markdown = args.markdown
        self._log = args.log
        self._is_zh = args.is_zh

        self._sqlite = Sqlite(args.database)
        self._result = self._sqlite.select_all_from_paper()
        self._header = self._sqlite.header

        # 对结果按引用量排序
        self._result = list(self._result)
        self._result.sort(key=lambda x: float(x[5]), reverse=True)

        count = 4
        for index in range(len(self._result)):
            print(self._result[index])
            if index >= count:
                break
        pass

    def to_excel(self):
        self._log.append('Starting write to excel.')
        target_workbook = openpyxl.Workbook(write_only=True)
        target_sheet = target_workbook.create_sheet('sheet0')

        # 表头
        header = ['title', 'author', 'year', 'journal', 'citations', 'year_citations', 'connected_papers_url', 'semantic_scholar_url', 'publisher_page_url', 'abstract']
        if self._is_zh:
            header = ['title', 'author', 'year', 'journal', 'citations', 'year_citations', 'connected_papers_url', 'semantic_scholar_url', 'publisher_page_url', 'abstract', 'title_zh', 'abstract_zh']

        target_sheet.append(header)

        # 写入
        if self._is_zh:
            for item in self._result:
                if self._check_func(item[0]):
                    target_sheet.append(item)
        else:
            for item in self._result:
                if self._check_func(item[0]):
                    item = list(item)
                    item = item[:-2]
                    target_sheet.append(item)

        target_workbook.save(self._excel_file)
        pass


if __name__ == '__main__':
    pass
