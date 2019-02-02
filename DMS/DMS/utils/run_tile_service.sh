#!/usr/bin/env bash
source activate algo-work
cd /home/kyfq/MyPython/PycharmProjects/dms/services

# 先kill掉关于tiles_server的进程
pkill -f 'python -u tiles_server.py'

# 然后再重新开启四个端口, 四个进程切图
python -u tiles_server.py 8071 &
python -u tiles_server.py 8072 &
python -u tiles_server.py 8073 &
python -u tiles_server.py 8074 &
python -u tiles_server.py 8075 &
