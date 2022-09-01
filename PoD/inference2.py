from random import randint
import grpc
from matplotlib.axis import YAxis
import numpy as np
import pandas as pd
from PoD import singleBlockChange, nbtProcessing, moveNBT
import tensorflow as tf

import minecraft_pb2_grpc
from minecraft_pb2 import *
from PoD import locateMinMax
from minecraft import MinecraftClient
from worldControl import worldReset

from copy import deepcopy

# Set variables
HOUSE_WIDTH = 13
HOUSE_HEIGHT = 13
HOUSE_DEPTH = 13
ACTION_SPACE = 7

# connect to the server
channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)

# block types that we will allow
acceptedBlocks = [5, 41, 60, 88, 131, 160, 224]

# dictionary for one-hot mapping
dict_one_hot_mapping = {5: 0, 41: 1, 60: 2, 88: 3, 131: 4, 160: 5, 224: 6}

# function to generate a random noise block of size n
def generateRandomNoiseBlock(location, size):
    for zAxis in range(location.z, location.z + size):
        for yAxis in range(location.y, location.y + size):
            for xAxis in range(location.x, location.x + size):
                randomInt = randint(0,6)
                singleBlockChange(Point(x=xAxis,y=yAxis,z=zAxis), acceptedBlocks[randomInt])
                singleBlockChange(Point(x=xAxis-30,y=yAxis,z=zAxis), acceptedBlocks[randomInt])

# function to transform blocks into input for the model to predict on
def transformInputForModel(inputBlocks, oneHotValues):
    X = []
    # initialize the empty array of size (13 x 13 x 13) x 7 -> for one-hot
    threedArr2 = np.full(((13 * 13 * 13), 7), [1,0,0,0,0,0,0])

    # fill the array
    index = 0
    for block in inputBlocks:
        inputBlock = block.type
        if block.type == 93 or block.type == 87:
            inputBlock = 5
        threedArr2[index] = oneHotValues[inputBlock]
        index += 1

    # flatten and reshape to correct format
    flattenedArray = threedArr2.flatten()
    finalArray = np.array(flattenedArray).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
    X.append(finalArray)
    X = np.array(X)
    return X

# main function
if __name__ == '__main__':

    # load the saved model
    loadedModel = tf.keras.models.load_model('/Users/hsgra/Desktop/AIforGamesPCGRLMineCraft/PoD/paddedModels/prePaddedModelIterativeMulti400k.h5')
    loadedModel.summary()

    # clear the world
    clearMin = Point(x=-100, y=0, z=-50)
    clearMax = Point(x=100, y=100, z=50)
    worldReset(clearMin, clearMax)

    '''
    # load the processed goal house to compare
    base_nbt_path = 'C:/Users/hsgra/Desktop/AIforGamesPCGRLMineCraft/dataset/nbts/'
    nbt_path = "{}/plain_village_house.nbt".format(base_nbt_path)
    blocks, unique_vals, target, color_dict, unique_val_dict = MinecraftClient.load_entity("Apartment", nbt_path=nbt_path, load_coord=(40,2,10))
    accurateMin = Point(x=50, y=2, z=10)
    accurateMax = Point(x=53, y=6, z=15)
    excludingType = [5, 93, 10, 60]
    acceptedBlocks = [5, 41, 60, 88, 131, 160, 224]
    minMax = locateMinMax(Point(x=40, y=0, z=0), Point(x=60, y=10, z=20), excludingType)
    nbtProcessing(minMax[0], minMax[1], acceptedBlocks)
    sizeX = minMax[1].x - minMax[0].x + 1
    sizeY = minMax[1].y - minMax[0].y + 1
    sizeZ = minMax[1].z - minMax[0].z + 1
    moveToCoord = Point(x=60,y=12,z=0)
    moveNBT(minMax[0], minMax[1], moveToCoord)
    size = 6
    newMinMax = [moveToCoord, Point(x=moveToCoord.x+5, y=moveToCoord.y+5, z=moveToCoord.z+5)]
    '''
    # generate noise block
    
    generateRandomNoiseBlock(Point(x=0,y=10,z=0), 6)
 
    # generate oneHotMapping
    oneHotValues = {}
    for block in acceptedBlocks:
        tempOneHot = [0] * (7)
        oneHotPosition = dict_one_hot_mapping[block]
        tempOneHot[oneHotPosition] = 1
        oneHotValues[block] = tempOneHot
    print(oneHotValues, "One hot encoded vectors")

    #######################  need to be fixed without hard-code ###############

    # go through all the noise structure blocks
    for zAxis in range(0, 6):
        for yAxis in range(10, 16):
            for xAxis in range(0, 6):
                print(f"Agent Location:({xAxis},{yAxis},{zAxis})")

                # get the surrounding 13 x 13 x 13 blocks from the agent location at center
                minPosition = Point(x = xAxis - 6, y = yAxis - 6, z = zAxis - 6 )
                maxPosition = Point(x = xAxis + 6, y = yAxis + 6, z = zAxis + 6 )
                inputBlocks = client.readCube(Cube(min=minPosition, max=maxPosition))
                print("length of Input Blocks:", len(inputBlocks.blocks))

                # transform the block data to model input
                inputData = transformInputForModel(inputBlocks.blocks, oneHotValues)
                print(inputData.shape)

                # Predict the block to replace current position block using the model 
                predictions = loadedModel.predict(inputData)
                print("Predictions=", predictions)
                
                # Generate arg maxes for predictions
                predictedNewBlock = np.argmax(predictions, axis = 1)
                predictedNewBlock = predictedNewBlock[0]
                print("Predicted new block -> ", predictedNewBlock)

                # dict to map ordinal values to cube types
                reverseValueMap = {0: 5, 1: 41, 2: 60, 3: 88, 4: 131, 5: 160, 6: 224}

                # replace the current location of agent with the predicted block
                singleBlockChange(Point(x=xAxis,y=yAxis,z=zAxis), reverseValueMap[predictedNewBlock])

                # copy agent action to show building being built
                singleBlockChange(Point(x=xAxis + 30,y=yAxis,z=zAxis), reverseValueMap[predictedNewBlock])
