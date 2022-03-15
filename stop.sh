#!/usr/bin/env bash

ps -ef|grep proxy.py|awk '{print $2}'|xargs -i kill -9 {}
ps -ef|grep server.py|awk '{print $2}'|xargs -i kill -9 {}
