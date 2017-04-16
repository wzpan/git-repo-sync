#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: wzpan
# this script is used for transfer codes from source repo to target repo
# python sync.py <source repo> <target repo>

import io
import os
import sys
import time
import subprocess
import shutil

reload(sys)
sys.setdefaultencoding('utf8')

def get_tmp_folder_name(address):
    '''根据仓库地址获得相应本地克隆位置. '''
    pos = address.rfind('/')
    if pos < 0:
        sys.stderr.write("错误：仓库地址 %s 不是合法地址" % address)
        exit(1)
    repo_name = address[pos+1:]
    tmp_folder = os.path.join("/tmp", repo_name + "_" + str(time.time()))
    return tmp_folder

def check_repo_address(address):
    '''检查仓库地址是否合法.'''
    if not address.startswith("git@") and not address.startswith("http://"):
        sys.stderr.write("错误：仓库地址 %s 不是有效的地址" % address)
        exit(1)

def sync(source, target, tmp_folder):
    '''同步仓库'''
    pipe = subprocess.Popen(['git', 'clone', source, tmp_folder], cwd="/tmp")
    res = pipe.wait()
    if res != 0:
        sys.stderr.write("错误：原仓库地址 %s 克隆失败" % source)
        return 1
    subprocess.call(['git', 'remote', 'add', 'target', target], cwd=tmp_folder)
    res = subprocess.call(['git', 'config', '--get', 'push.default'])
    if res != 0:
        subprocess.call(['git', 'config', '--global', 'push.default', 'matching'])
    output = subprocess.Popen(["git branch -r | grep -v -- '->'"], shell=True, cwd=tmp_folder, stdout=subprocess.PIPE)
    oc = output.communicate()[0] #取出output中的字符串
    branch_list = oc.split('\n')
    all_success = True
    for branch in branch_list:
        branch = branch.strip()
        if branch != "":
            pos = branch.find('/')
            if pos > -1:
                branch = branch[pos+1:]
            print("正在拉取 %s 分支..." % branch)
            res = subprocess.call(['git', 'checkout', branch], cwd=tmp_folder)
            if res != 0:
                sys.stderr.write("错误：原仓库 %s 分支拉取失败" % (source, branch))
                all_success = False
    if not all_success:
        sys.stderr.write("错误：原仓库地址 %s 拉取失败" % source)
        return 1
    print("全部分支拉取成功")
    res = subprocess.call(['for b in `git branch | sed "s/*//"`; do git push -u target $b; done'], cwd=tmp_folder, shell=True)
    if res != 0:
        sys.stderr.write("错误：目标仓库地址 %s 分支同步失败" % source)
        return 1
    res = subprocess.call(['git fetch -t'], cwd=tmp_folder, shell=True)
    if res != 0:
        sys.stderr.write("错误：原仓库地址 %s 标签拉取失败" % source)
        return 1
    res = subprocess.call(['for b in `git tag`; do git push -u target $b; done'], cwd=tmp_folder, shell=True)
    if res != 0:
        sys.stderr.write("错误：目标仓库地址 %s 标签同步失败" % source)
    return res

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) != 3:
        sys.stderr.write("参数错误")
        exit(1)
    source = argv[1]
    target = argv[2]
    check_repo_address(source)
    check_repo_address(target)
    print("即将同步代码\n %s -> %s" % (source, target))
    tmp_folder = get_tmp_folder_name(source)
    res = sync(source, target, tmp_folder)
    if os.path.exists(tmp_folder):
        shutil.rmtree(tmp_folder)
    exit(res)
