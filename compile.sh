#!/bin/bash

########################################
############# CSCI 2951-O ##############
########################################

# install Python3.8
wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz
tar xzf Python-3.8.12.tgz

(cd Python-3.8.12; ./configure --enable-optimizations -prefix=$HOME)
(cd Python-3.8.12; make altinstall)

Python-3.8.12/python -m pip install -r requirements.txt

(cd cplex; ../Python-3.8.12/python setup.py install)
