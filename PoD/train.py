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
TARGET_COL = 2197
ACTION_SPACE = 8
MODEL_PATH = "paddedModels/paddedModel.h5"

'''
# use this if data is in single CSV file
DATA_FILE = "buildingData2.csv"
value_map = {5: 0, 41: 1, 224: 2, 60: 3, 160: 4, 131: 5, 88: 6}

df = pd.read_csv(DATA_FILE, header=None)
print(f"df shape {len(df)} rows {len(df.iloc[0])} cols")
print(f"df: \n{df.head()}\n\n")
'''

# dict to map cube types to ordinal values
'''
5 = AIR
41 = COBBLESTONE
60 = DIRT
88 = GLASS_PANE(window)
131 = LOG
160 = PLANKS
224 = STONE_STAIRS
247 = WOODEN_DOOR
'''
value_map = {5: 0, 41: 1, 60: 2, 88: 3, 131: 4, 160: 5, 224: 6, 247: 7}

# generate column numbers for each column(13 x 13 x 13 = 2197 cubes + 1 target)
colnames = list(range(0, 2198))

# read each file in the dataset path and add to a dataframe
pod_root_path = '../dataset/paddedTestCsvs'
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

# drop the target column after getting y labels
df.drop(TARGET_COL, axis=1, inplace=True)
y = y.astype('int32')

# check target and final df structure
print(y,"Target labels")
print(df.head(3), "final df")

'''
# Map block values to ordinal via value_map
print("Mapping values for total number of rows:", len(df))
for row_idx in range(len(df)):
    if row_idx % 10000 == 0:
        print("Currently on row:", row_idx)
    cols = df.iloc[row_idx].values
    for col_idx in range(len(cols)):
        df.iloc[row_idx,col_idx] = value_map[cols[col_idx]]
    y[row_idx] = value_map[y[row_idx]]

# Convert df to onehot
print("Converting df to one-hot....")
X = []
for row_idx in range(len(df)):
    if row_idx % 10000 == 0:
        print("Currently on row:",row_idx)
    cols = df.iloc[row_idx].values
    new_row = []
    for col_idx in range(len(cols)):
        new_onehot = [0]*8
        new_onehot[df.iloc[row_idx, col_idx]] = 1
        new_row.append(new_onehot)
    new_row = np.array(new_row).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
    X.append(new_row)

    y[row_idx] = value_map[y[row_idx]]
'''

# Map block values to ordinal via value_map and then one-hot
print("Mapping values to ordinal then one-hot for total number of rows:", len(df))
X = []
for row_idx in range(len(df)):
    if row_idx % 10000 == 0:
        print("Currently on row:", row_idx)
    cols = df.iloc[row_idx].values
    new_row = []
    for col_idx in range(len(cols)):
        df.iloc[row_idx,col_idx] = value_map[cols[col_idx]]
        new_onehot = [0]*8
        new_onehot[df.iloc[row_idx, col_idx]] = 1
        new_row.append(new_onehot)
    new_row = np.array(new_row).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
    X.append(new_row)
    y[row_idx] = value_map[y[row_idx]]

# convert y to onehot
print("Converting y to one-hot....")
y = np_utils.to_categorical(y)
X = np.array(X)
print("shape of X:", X.shape)

# save the files after processing so we dont need to do the process again.
# np.save('../processedData/10filesOneHotX.npy', X)
# np.save('../processedData/10filesOneHoty.npy', y)

# Define model
model = tf.keras.models.Sequential([
        tf.keras.layers.Conv3D(128, 3, activation='relu',
                               input_shape=(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)),
        tf.keras.layers.MaxPooling3D(2),
        tf.keras.layers.Conv3D(128, 3, activation='relu', padding="SAME"),
        tf.keras.layers.Conv3D(256, 3, activation='relu', padding="SAME"),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(8, activation='softmax')
    ])
model.summary()

# if data is stored already as .npy
# y = np.load('../processedData/10filesOneHoty.npy')
# X = np.load('../processedData/10filesOneHotX.npy')

# Train the model
print("Training Model....")
model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=[tf.keras.metrics.CategoricalAccuracy()])
mcp_save = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='categorical_accuracy', mode='max')
history = model.fit(X, y, epochs=500, steps_per_epoch=256, verbose=2, callbacks=[mcp_save])


