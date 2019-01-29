"""
Django settings for DMS project.

Generated by 'django-admin startproject' using Django 2.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$v%z9m=g!h3fl7@d21w*0lxgb6u^zkor9xtu$j%=&^v%0+0%lk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# 跨域增加忽略
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = (
    '*'
)

# 允许跨域的方法
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)

# 允许跨域请求头
CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 第三方应用
    'rest_framework',
    'django_filters',
    'rest_framework_swagger',
    # 'django_crontab',
    'django_extensions',  # python manage.py shell_plus --print-sql
    'dwebsocket',

    # 自己的应用
    'Case',
    'Diagnosis',
    'FileRenameRecord',
    'Image',
    'Check',
    'Train',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 跨域
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DMS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DMS.wsgi.application'


# ------------------------------ 数据库相关配置 ------------------------------ #
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dms',
        'USER': 'root',
        'PASSWORD': 'kyfq',
        # 'HOST': '192.168.2.179',
        'HOST': 'localhost',
        'PORT': 3306,
    }
}

# ------------------------------ 配置上传时文件保存的数据库引擎 ------------------------------ #
UPLOAD_DB_ENGINE = 'mysql+mysqldb://root:kyfq@localhost:3306/dms?charset=utf8'


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ------------------------------ 时间时区相关配置 ------------------------------ #
# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# ------------------------------ 静态文件相关配置 ------------------------------ #

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, '../../resources/static')
STATIC_URL = '/static/'


# ------------------------------ DRF相关配置 ------------------------------ #

REST_FRAMEWORK = {
    # 设置默认的分页控制
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,  # 默认每页显示多少条
}


# ------------------------------ 自定义参数设置 ------------------------------ #

# 本机中的data_samba的路径
DATA_SAMBA_PREX = '/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/LCT_DATA'

# 移动大图到垃圾文件夹的目录
TRASH_FILE_PATH = 'TMP/IMAGE_GARBAGE'

# 大图存储路径
DATA_SAMBA_IMAGE_LOCATE = '0TIFF'

# 训练数据存储路径
# batch6
BATCH6_CELLS_PATH = '4TRAIN_DATA/20181201_BATCH_6/CELLS'
BATCH6_XMLS_PATH = '4TRAIN_DATA/20181201_BATCH_6/XMLS'
# batch6.1
BATCH6_1_CELLS_PATH = '4TRAIN_DATA/20181205_BATCH_6.1/CELLS'
BATCH6_1_XMLS_PATH = '4TRAIN_DATA/20181216_BATCH_6.1/XMLS_CHECKED'
# batch6.2
BATCH6_2_CELLS_PATH = '4TRAIN_DATA/batch6.2-cells'
# batch6.3
BATCH6_3_CELLS_PATH = '4TRAIN_DATA/batch6.3/CELLS'
BATCH6_3_XMLS_PATH = '4TRAIN_DATA/batch6.3/XMLS_CHECKED'


# ------------------------------ 配置下载excel格式的插件 ------------------------------ #

FILE_UPLOAD_HANDLERS = ("django_excel.ExcelMemoryFileUploadHandler",
                        "django_excel.TemporaryExcelFileUploadHandler",)


# ------------------------------------- 配置swagger -------------------------------------- #

SWAGGER_SETTINGS = {
    # 基础样式
    'SECURITY_DEFINITIONS': {
        "basic": {
            'type': 'basic'
        }
    },
    'SHOW_REQUEST_HEADERS': True,
    # 控制API列表的显示方式, None：折叠所有(默认), list：列出所有操作
    'DOC_EXPANSION': 'list',
    # 接口文档中方法列表以首字母升序排列
    'APIS_SORTER': 'alpha',
    # 如果支持json提交, 则接口文档中包含json输入框
    'JSON_EDITOR': True,
    # 方法列表字母排序
    'OPERATIONS_SORTER': 'alpha',
}


# ------------------------------ 配置日志 ------------------------------ #
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s [%(asctime)s] [%(module)s:%(funcName)s] %(message)s'
        },
        'sample': {
            'format': '%(levelname)s [%(asctime)s] %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
    },
    'handlers': {  # 日志处理方法
        'file': {  # 向文件中输出项目日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/dms.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
        # 'monitor': {  # 向文件中输出管控日志
        #     'level': 'INFO',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(BASE_DIR, 'logs/monitor_0tiffs.log'),  # 日志文件的位置
        #     'maxBytes': 300 * 1024 * 1024,
        #     'backupCount': 5,
        #     'formatter': 'sample'
        # },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['file'],  # 向文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
        # 'monitor_0tiff': {  # 定义了一个名为monitor_0tiff的日志器
        #     'handlers': ['monitor'],  # 向文件中输出日志
        #     'propagate': True,  # 是否继续传递日志信息
        #     'level': 'INFO',  # 日志器接收的最低日志级别
        # },
    }
}


# WEBSOCKET_ACCEPT_ALL=True
# WEBSOCKET_FACTORY_CLASS = 'dwebsocket.backends.uwsgi.factory.uWsgiWebSocketFactory'