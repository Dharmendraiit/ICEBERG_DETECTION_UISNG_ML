# -*- coding: utf-8 -*-
"""iceberg vs boat-tuner testing.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Je9gJtH9ojfAr7DQVIyYBjrF6YSEkJjZ

## Loading and preprocessing data
"""

import pandas as pd
import keras.optimizers

# Code to read csv file into colaboratory:
!pip install -U -q PyDrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials

auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

#2.1 Get the file
downloaded = drive.CreateFile({'id':'1tygtRvSHxmtbWIUq4hb9v8IcPIqWBLCy'}) # replace the id with id of file you want to access
downloaded.GetContentFile('train.json')

import pandas as pd

data = pd.read_json('test.json',orient=None,
    typ='frame',
    dtype=None,
    convert_axes=None,
    convert_dates=True,
    keep_default_dates=True,
    numpy=False,
    precise_float=False,
    date_unit=None,
    encoding=None,
    lines=True,
    chunksize=None,
    compression='infer',)

pd.__version__

py.__version__

from kerastuner.tuners import RandomSearch
from kerastuner.engine.hyperparameters import HyperParameters

import time
LOG_DIR = f"{int(time.time())}"

data = pd.read_json('train.json')

X = data.iloc[:, 1:3].values

bd1 = [X[i][0] for i in range(len(X))]
bd2 =  [X[i][1] for i in range(len(X))]

import numpy as np

"""## 3 bands inorder to represent the image in 3 channels format with 3rd band as the average of 1st and 2nd band"""

bd1 = np.array([np.array(band).astype(np.float32).reshape(75, 75) for band in bd1])

bd2=  np.array([np.array(band).astype(np.float32).reshape(75, 75) for band in bd2])

bd3 = (bd1 + bd2)/2.0

"""## Stacking 3 channels to form a 3 channel image"""

imgs = np.concatenate([bd1[:, :, :, np.newaxis], bd2[:, :, :, np.newaxis], bd3[:, :, :, np.newaxis]], axis=-1)

import matplotlib.pyplot as plt

"""## Rescalling the decimel values of the SAR images to 0 - 1"""

bd1dn = [np.array(np.exp((np.array(X[i][0])/10))) for i in range(len(X))]
bd2dn = [np.array(np.exp((np.array(X[i][1])/10))) for i in range(len(X))]
bd1dn = np.array([np.array(band).astype(np.float32).reshape(75, 75) for band in bd1dn])
bd2dn=  np.array([np.array(band).astype(np.float32).reshape(75, 75) for band in bd2dn])
bd3dn = (bd1dn + bd2dn)/2.0
imgsdn = np.concatenate([bd1dn[:, :, :, np.newaxis], bd2dn[:, :, :, np.newaxis], bd3dn[:, :, :, np.newaxis]], axis=-1)

imgsdn[0]

import matplotlib.pyplot as plt

"""## Visualising the images with matplotlib"""

plt.imshow(bd1[2]) #band 1 image

plt.imshow(bd1dn[2]) #band1 image after rescalling

plt.imshow(imgsdn[2]) #3 channel image after rescalling

X_imgdn_train = imgsdn[0:1000]
X_imgdn_test = imgsdn[1000:]

y_imgdn = data.is_iceberg

y_imgdn_train=y_imgdn[:1000].values.reshape(-1,1)
y_imgdn_test=y_imgdn[1000:].values.reshape(-1,1)



y_imgdn_train.shape
y_imgdn_test.shape

y_imgdn.shape

"""## Removing speckle"""

import cv2
l = []

for i in range(len(imgsdn)):
    
    median = cv2.medianBlur(imgsdn[i],5)
    l.append(median)
np.array(l)
filteredimgsdn =np.array(l)
X_filtered_imgdn = filteredimgsdn
X_filtered_imgdn_train = X_filtered_imgdn[:1000]
X_filtered_imgdn_test = X_filtered_imgdn[1000:]

from tensorflow.keras import Sequential
from tensorflow import keras
from tensorflow.keras.layers import Dense, Activation, Conv2D, MaxPooling2D, Dropout, Flatten

def build_model(hp):
    
    gmodel=Sequential()
    
    #Conv Layer 1
    gmodel.add(Conv2D(hp.Int('input_units',min_value=32, max_value = 256, step=32), kernel_size=(3, 3),activation='relu', input_shape=(75, 75, 3)))
    gmodel.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    gmodel.add(Dropout(0.2))

    #Conv Layer 2
    for i in range(hp.Int('n_layers', 1, 4)):
        gmodel.add(Conv2D(hp.Int(f'conv_{i}_units',min_value=32, max_value = 256, step=32), kernel_size=(3, 3), activation='relu' ))
        #gmodel.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
        gmodel.add(Dropout(0.2))

#     #Conv Layer 3
#     gmodel.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
#     gmodel.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
#     gmodel.add(Dropout(0.2))

#     #Conv Layer 4
#     gmodel.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
#     gmodel.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
#     gmodel.add(Dropout(0.2))

    #Flatten the data for upcoming dense layers
    gmodel.add(Flatten())

    #Dense Layers
    gmodel.add(Dense(512))
    gmodel.add(Activation('relu'))
    gmodel.add(Dropout(0.2))

    #Dense Layer 2
    gmodel.add(Dense(256))
    gmodel.add(Activation('relu'))
    gmodel.add(Dropout(0.2))

    #Sigmoid Layer
    gmodel.add(Dense(1))
    gmodel.add(Activation('sigmoid'))
    
    mypotim=keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    gmodel.compile(loss = 'binary_crossentropy', optimizer = mypotim, metrics = ['acc'])

    return gmodel

tuner = RandomSearch(build_model, objective='val_acc', max_trials=3, executions_per_trial = 1,
                     directory = LOG_DIR)

tuner.search(x = X_filtered_imgdn_train,y = y_imgdn_train, epochs = 1, batch_size = 200, validation_data = (X_filtered_imgdn_test, y_imgdn_test))



















"""## Compiling and fitting the model"""



"""## Removing speckle effect from SAR images by median filtering"""

# plt.imshow(bd1dn[1])

# plt.imshow(bd1dn[0])

"""## Images before and after removing the Speckling"""

# plt.imshow(imgsdn[1])

# plt.imshow(filteredimgsdn[1])

# X_filtered_imgdn_train.shape
# plt.imshow(X_filtered_imgdn_train[1])

"""## Fitting the Model on filtered Images"""

# gmodel.fit(X_filtered_imgdn_train, y_imgdn_train, epochs=5,  batch_size = 400, validation_split=.2)

"""## Evaluating the Model"""

# gmodel.evaluate(X_filtered_imgdn_test, y_imgdn_test)













