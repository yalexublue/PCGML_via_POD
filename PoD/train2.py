import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint
import pandas as pd
import numpy as np
from keras.utils import np_utils
import os
import sys

# check if GPU is available
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

# Set variables
HOUSE_WIDTH = 13
HOUSE_HEIGHT = 13
HOUSE_DEPTH = 13
TARGET_COL = 15379
ACTION_SPACE = 7
MODEL_PATH = "paddedModels/prePaddedModel.h5"

value_map = {5: 0, 41: 1, 60: 2, 88: 3, 131: 4, 160: 5, 224: 6}

# generate column numbers for each column(13 x 13 x 13 = 2197 cubes + 1 target)
colnames = list(range(0, 15380))

# read each file in the dataset path and add to a dataframe
pod_root_path = '../dataset/prePaddedTestCsvs'
dfs = []
for file in os.listdir(pod_root_path):
    df = pd.read_csv(f"{pod_root_path}/{file}", names=colnames, header=None)
    print(f"compiling df {file} -> df shape is: {len(df)} rows - {len(df.iloc[0])} cols")
    df.reset_index(drop=True)
    print(df.head(3))
    dfs.append(df)

# combine all the df and get last column from combined df then set to y
df = pd.concat(dfs)
df = df.sample(frac=1).reset_index(drop=True)
y = df.iloc[:, -1].values
print(y)

# drop the target column after getting y labels
print(df.head(3), "df with shape:", df.shape)
df.drop(TARGET_COL, axis=1, inplace=True)
y = y.astype('int32')

# check target and final df structure
print(y,"Target labels")
print(df.head(3), "final df with shape:", df.shape)

# get all the dataframe rows into an array
X = []
for row_idx in range(len(df)):
    new_row = df.iloc[row_idx].to_numpy()
    new_row = np.array(new_row).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
    
    X.append(new_row)
    y[row_idx] = value_map[y[row_idx]]

# convert y to onehot
print("Converting y to one-hot....")
y = np_utils.to_categorical(y)
X = np.array(X)
print("shape of X:", X.shape)

# Define model
model = tf.keras.models.Sequential([
        tf.keras.layers.Conv3D(128, 3, activation='relu',
                               input_shape=(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)),
        tf.keras.layers.MaxPooling3D(2),
        tf.keras.layers.Conv3D(128, 3, activation='relu', padding="SAME"),
        tf.keras.layers.Conv3D(256, 3, activation='relu', padding="SAME"),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(7, activation='softmax')
    ])
model.summary()

# if data is stored already as .npy
# y = np.load('../processedData/10filesOneHoty.npy')
# X = np.load('../processedData/10filesOneHotX.npy')

# Train the model
print("Training Model....")
model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=[tf.keras.metrics.CategoricalAccuracy()])
mcp_save = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='categorical_accuracy', mode='max')
history = model.fit(X, y, epochs=500, steps_per_epoch=64, verbose=2, callbacks=[mcp_save])


