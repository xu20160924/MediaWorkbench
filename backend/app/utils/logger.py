import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

from conf import BASE_PATH

# 日志目录放在仓库根目录（backend 的父级）
LOG_DIR = os.path.join(BASE_PATH.parent, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 创建logger实例
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# 创建按日期命名的日志文件
log_file = os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log')

# 创建文件处理器
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=50*1024*1024,  # 50MB to reduce daily splits
    backupCount=5,
    encoding='utf-8'
)

# 创建控制台处理器
console_handler = logging.StreamHandler()

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler) 