# --------- 使用mysql数据库 --------- #
import pymysql
pymysql.install_as_MySQLdb()

# --------- 修改后台admin站点的信息  --------- #
from django.contrib import admin

# 后台admin站点标题/头部标题
admin.site.site_header = 'DMS后台管理系统'
admin.site.site_title = 'kyfq'
