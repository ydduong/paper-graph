功能

- 借助 https://www.connectedpapers.com/ 网站查找相关联文章
- 收集相关信息（论文信息和关联信息），存入数据库
- 根据关联信息，构建关系图，使用BFS广度优先搜索
- 生成其他文件格式

配置

- 配置selenium工具所需对应浏览器驱动: https://zhuanlan.zhihu.com/p/88152781 
- 使用教程: https://betterprogramming.pub/the-beginners-guide-to-selenium-with-python-cde1937585c6
- 驱动下载网址: https://registry.npmmirror.com/binary.html?path=chromedriver/
- 


使用

- 初始论文标题在txt文件内，一行一个，如：test-title.txt
- ```text
  PROSO II – a new method for protein solubility prediction
  Sequence-based prediction of protein solubility.
  Prediction of protein solubility in E. coli
  ```
- 配置参数文件 config.json
- ```text
  {
    "title-file": "test-title.txt",
    "driver": "/Users/yudd/Downloads/chromedriver",
    "iteration": 8,
    "filter-keywords": ["solubility", "predict"],
    "wait-time": 30,
    "is-zh": 1
  }
  ```
- 运行main.py
