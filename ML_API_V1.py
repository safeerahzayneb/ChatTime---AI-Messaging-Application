#!/usr/bin/env python3
import os
import shutil
import copy
import time
import math
import random
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.models
import torchvision.transforms as transforms
import matplotlib.pyplot as plt

from PIL import Image
from pathlib import Path
from torchvision import datasets, models, transforms
from torch.optim import lr_scheduler
from torch.autograd import Variable


# GLOBAL VARIABLES
CLASSES = ['afraid','angry','disgusted','happy','neutral','sad','surprised']
LABELS = {0:"afraid", 1:"angry", 2:"disgusted", 3:"happy",
            4:"neutral", 5:"sad", 6:"surprised"}


# Artifical Neural Network Architecture
class ANNClassifier_Alexnet(nn.Module):
    def __init__(self):
        super(ANNClassifier_Alexnet, self).__init__()
        self.name = "alexnet_ann"
        self.fc1 = nn.Linear(256 * 6 * 6, 300)
        self.fc2 = nn.Linear(300, 7)

    def forward(self, x):
        x = x.view(-1, 256 * 6 * 6) #flatten feature data
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# TODO: Add class implementation for text RNN

class ModelsContainer:
    def __init__(self):
        # Init text RNN model
        # self.text_rnn = RNN() # TODO: Replace temp placeholder

        # Init facial ANN model
        self.alexnet = torchvision.models.alexnet(pretrained=True)
        self.facial_ann = ANNClassifier_Alexnet()
        state_path = os.path.normpath('/Users/Harshita/Documents/GitHub/ChatTime/test_0843_model_alexnet_ann_bs128_lr0_001_epoch149')
        state = torch.load(state_path)
        self.facial_ann.load_state_dict(state)

        # List to store text sentiment results for previous 10 messages
        self.past_msg = []

    def detect_image_emotion(self, filename):
        """ Given an image file, use facial ANN to detect the facial expression in image
        Args:
            filename: path to image file, including full filename
        Returns:
            pred_label: emotion label (str) predicted by the model
        """
        img = Image.open(filename)
        new_img = img.resize((1500, 1500))

        data_transform = transforms.CenterCrop(500)
        new_img = data_transform(img)

        new_img_path = os.path.normpath('/Users/Harshita/Documents/GitHub/ChatTime/img.jpg')
        new_img.save(new_img_path)

        # Use to convert 1-channel grayscale image to a 3-channel "grayscale" image
        # to use for AlexNet.features
        # Note: For some odd reason, differing from Colab,
        # data_transform(new_image) actually gives shape [1, 224, 224]
        # when we need [3, 224, 224] as input for AlexNet
        #########################
        grey_img = cv2.imread(new_img_path, cv2.IMREAD_ANYCOLOR)
        grey = cv2.cvtColor(grey_img, cv2.COLOR_BGR2GRAY)
        img2 = np.zeros_like(grey_img)
        img2[:,:,0] = grey
        img2[:,:,1] = grey
        img2[:,:,2] = grey
        new_grey_img_path = os.path.normpath('/Users/Harshita/Documents/GitHub/ChatTime/img_grey.jpg')
        cv2.imwrite(new_grey_img_path, img2)
        #########################

        #data_transform = transforms.Compose([transforms.CenterCrop(224),
        #                                transforms.ToTensor()])

        imgs = Image.open(new_grey_img_path)
        #imgs = data_transform(imgs)
        imgs = imgs.resize((224, 224))

        data_transform = transforms.ToTensor()

        imgs_path = os.path.normpath('/Users/Harshita/Documents/GitHub/ChatTime/input_img.jpg')
        imgs.save(imgs_path)

        imgs = data_transform(imgs)
        # print(imgs.shape) # DEBUG Log: torch.Size([3, 224, 224])
        imgs = imgs.reshape([1, 3, 224, 224])

        features = self.alexnet.features(imgs)
        # print(features.shape) # DEBUG Log: torch.Size([1, 256, 6, 6])
        features = torch.from_numpy(features.detach().numpy())

        out = self.facial_ann(features)
        prob = F.softmax(out)
        pred = prob.max(1, keepdim=True)[1]
        # print(pred) # DEBUG
        np_pred = pred.numpy() # TODO: Verify that output format is always list of lists, [[#]]
        # print(np_pred) # DEBUG
        pred_label = LABELS[np_pred[0][0]]
        print(pred_label) # DEBUG

        return pred_label

    def detect_text_sentiment(self, msg):
        self.RNN()
        # make sure it returns int

    def combine_results(self, image_file, text_msg):
        facial_expr = self.detect_image_emotion(image_file)
        text_sentiment = self.detect_text_sentiment(text_msg)

        # Store text sentiment result into list of past results
        if(len(self.past_msg) > 10):
            self.past_msg[:1] = []
        self.past_msg.append(text_sentiment)

        # RNN: 0 = negative, 1 = positive,
        if(text_sentiment == 0 and facial_expr == 'angry'):
            return True
        elif (text_sentiment == 0 and facial_expr == 'disgusted'):
            return True
        elif (text_sentiment == 0 and facial_expr == 'neutral'):
            total = sum(self.past_msg) / len(self.past_msg)
            if(total <= 0.6):
                # This means more than 40% of our previous messages were negative
                return True
            return False
        else:
            return False
