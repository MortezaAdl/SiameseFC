# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 23:05:14 2022

@author: Sarah Munir
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 14:57:02 2022

@author: Sarah Munir
"""

import cv2
import os
import shutil


cwd = os.path.join(os.getcwd(),'OTB100')
for filedir in os.listdir(cwd):
    filepath = os.path.join(cwd,filedir)
    if os.path.isdir(filepath): 
        if not os.path.exists(os.path.join(filepath,'img')):
            os.makedirs(os.path.join(filepath,'img'))         
        for filename in os.listdir(filepath):
            if filename.endswith('.jpg'):
                if not os.path.exists(os.path.join(filepath,'img',filename)):
                    shutil.move(os.path.join(filepath, filename), os.path.join(filepath,'img'))

            
