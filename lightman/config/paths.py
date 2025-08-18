"""
提供全局的路径定义
"""
from os.path import dirname, join, abspath

root_path = abspath(dirname(dirname(dirname(__file__))))  # 整个项目目录，并不是源代码级别目录
src_path = abspath(dirname(dirname(__file__)))  # 源代码根目录
config_path = join(src_path, 'config')  # 配置目录
