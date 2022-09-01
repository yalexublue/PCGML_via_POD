import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint
import pandas as pd
import numpy as np
from keras.utils import np_utils
import os
import sys

# Follows this guide for data generator -> https://towardsdatascience.com/thousands-of-csv-files-keras-and-tensorflow-96182f7fabac

# check if GPU is available
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

# Set variables
HOUSE_WIDTH = 13
HOUSE_HEIGHT = 13
HOUSE_DEPTH = 13
TARGET_COL = 15379
ACTION_SPACE = 7
TRAIN_DATA_COEFFICIENT = 0.90
MODEL_PATH = "paddedModels/prePaddedModelIterativeMulti400k.h5"

# set the directory where the csv files are stored
dirname = os.path.dirname(__file__)
INPUT_DATA_DIR = os.path.join(dirname, 'prePaddedIterativeData/')

# get all the file names that need to be used
files = []
for (dirpath, dirnames, filenames) in os.walk(INPUT_DATA_DIR):
    files.extend(filenames)
    break
print("Files:", files)

# split the files into training and validation
train_files_finish = int(len(files) * TRAIN_DATA_COEFFICIENT)
train_files = files[0:train_files_finish]
validation_files = files[train_files_finish:len(files)]

# function to generate batches from the individual csv files as a generator
def generate_batches(files, batch_size):
    counter = 0
    value_map = {5: 0, 41: 1, 60: 2, 88: 3, 131: 4, 160: 5, 224: 6}

    # generate column numbers for each column(13 x 13 x 13 = 2197 cubes + 1 target)
    colnames = list(range(0, 15380))

    while True:

        # get the current file name
        fname = files[counter]

        # read contents of current file
        counter = (counter + 1) % len(files)
        df = pd.read_csv(INPUT_DATA_DIR + fname, names=colnames, header=None)

        # preprocessing
        df.reset_index(drop=True)
        df = df.sample(frac=1).reset_index(drop=True)
        y = df.iloc[:, -1].values

        # drop the target column after getting y labels
        df.drop(TARGET_COL, axis=1, inplace=True)
        y = y.astype('int32')

        # get all the dataframe rows into an array
        X = []
        for row_idx in range(len(df)):
            new_row = df.iloc[row_idx].to_numpy()
            new_row = np.array(new_row).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
            
            X.append(new_row)
            y[row_idx] = value_map[y[row_idx]]
        
        # convert y to onehot
        y = np_utils.to_categorical(y)
        X = np.array(X)

        input = X
        output = y

        for local_index in range(0, input.shape[0], batch_size):
            input_local = input[local_index:(local_index + batch_size)]
            output_local = output[local_index:(local_index + batch_size)]

            yield input_local, output_local

# set the batch size and create the training and validation generators
batch_size = 128
train_generator = generate_batches(files=train_files, batch_size=batch_size)
test_generator = generate_batches(files=validation_files, batch_size=batch_size)
print(train_generator, type(train_generator))

# create the dataset stream from the generators
train_dataset = tf.data.Dataset.from_generator(
    generator=lambda: generate_batches(files=train_files, batch_size=batch_size),
    output_types=(tf.int32, tf.int32),
    output_shapes=([None, 13,13,13,7], [None, 7])
)

test_dataset = tf.data.Dataset.from_generator(
    generator=lambda: generate_batches(files=validation_files, batch_size=batch_size),
    output_types=(tf.int32, tf.int32),
    output_shapes=([None, 13,13,13,7], [None, 7])
)

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

# train the model
model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=[tf.keras.metrics.CategoricalAccuracy()])
mcp_save = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='categorical_accuracy', mode='max')
history = model.fit(
    steps_per_epoch=len(train_files),
    use_multiprocessing=True,
    workers=4,
    x=train_dataset,
    verbose=1,
    max_queue_size=32,
    epochs=500,
    callbacks=[mcp_save],
    validation_data=test_dataset,
    validation_steps=len(validation_files)
)


