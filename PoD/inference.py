from random import randint
import grpc
import numpy as np
import pandas as pd
from PoD import singleBlockChange
import tensorflow as tf

import minecraft_pb2_grpc
from minecraft_pb2 import *
from PoD import locateMinMax
from worldControl import worldReset

from copy import deepcopy

# Set variables
HOUSE_WIDTH = 13
HOUSE_HEIGHT = 13
HOUSE_DEPTH = 13
TARGET_COL = 2197
ACTION_SPACE = 8

# connect to the server
channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)

# block types that we will allow
acceptedBlocks = [5, 41, 60, 88, 131, 160, 224, 247]

# function to generate a random noise block of size n
def generateRandomNoiseBlock(location, size):
    for xAxis in range(location.x, location.x + size):
        for yAxis in range(location.y, location.y + size):
            for zAxis in range(location.z, location.z + size):
                randomInt = randint(0,7)
                singleBlockChange(Point(x=xAxis,y=yAxis,z=zAxis), acceptedBlocks[randomInt])

# function to transform blocks into input for the model to predict on
def transformInputForModel(inputBlocks, minPoint):

    # dict to map cube types to ordinal values
    value_map = {5: 0, 41: 1, 60: 2, 88: 3, 131: 4, 160: 5, 224: 6, 247: 7}

    # initialize empty array of AIR with correct size
    threedArr = np.full((13,13,13), 5)

    # for each block
    for block in inputBlocks.blocks:
        threedArr[block.position.y-minPoint.y][block.position.x-minPoint.x][block.position.z-minPoint.z] = block.type

    # flatten the array
    flattenedArray = np.stack(threedArr, axis=1).flatten()

    # push the flattned array into a dataframe as a row
    df = pd.DataFrame(flattenedArray).T

    # Map block values to ordinal via value_map
    for row_idx in range(len(df)):
        cols = df.iloc[row_idx].values
        for col_idx in range(len(cols)):
            df.iloc[row_idx,col_idx] = value_map.get(cols[col_idx], 8)
    print(df.head())

    # Convert df to onehot
    X = []
    for row_idx in range(len(df)):
        cols = df.iloc[row_idx].values
        new_row = []
        for col_idx in range(len(cols)):
            new_onehot = [0]*8
            new_onehot[df.iloc[row_idx, col_idx]] = 1
            new_row.append(new_onehot)
        new_row = np.array(new_row).reshape(HOUSE_HEIGHT,HOUSE_WIDTH,HOUSE_DEPTH,ACTION_SPACE)
        X.append(new_row)
    
    X = np.array(X)
    return X

'''
class recoverAgent:
    def __init__(self, minBound = Point(x=0,y=0,z=0), maxBound = Point(x=0,y=0,z=0)):
        
        #mute the block or not
        self.coinFlip = 80
        

        self.minBoundary = minBound
        self.maxBoundary = maxBound

        #start from minboundary to move the agent
        self.currPosition = deepcopy(self.minBoundary) 
        
        """
        45 = "CONCRETE"
        23 = "BRICK_BLOCK"
        217 = "STONE"
        """
        # self.selectedTiles = [45, 23, 217]
        self.selectedTiles = [5, 41, 131, 160, 88, 224, 247, 60]
        self.reachEnd = False

    # position argument needs a Point type instance, selectedType can be int or string
    def singleBlockChange (self, position, selectedType):
        #print("position to change is: ", position)
        client.fillCube(FillCubeRequest(cube=Cube(
                        min = position,
                        max = position
                    ), type=selectedType))

    def getBlockType (self, position):
        blocks = client.readCube(Cube(min=position, max=position))

        return blocks.blocks[0].type
    
    def takeAction(self):
        #print ("action is taken")
        coinToss = random.randint(0, 100)
        
        
        #action, which is the original tile type before change been made is recorded here
        action = self.getBlockType(self.currPosition)
        #proceed to take next step of destruction
        #Destruction traverse order is: z -> y -> x
        if coinToss <= self.coinFlip:
            #block will be changed to one of the type in tile Selection
            randomTile = random.randint(0, 7)
            tileChangeTo = self.selectedTiles[randomTile]
            self.singleBlockChange(self.currPosition, tileChangeTo)
        #after change or not move on to next target
        if self.currPosition.z + 1 < self.maxBoundary.z + 1:
            self.currPosition.z += 1
        elif self.currPosition.y + 1 < self.maxBoundary.y + 1:
            #print("z should reset")
            self.currPosition.z = self.minBoundary.z
            self.currPosition.y += 1
        elif self.currPosition.x + 1 < self.maxBoundary.x + 1:
            self.currPosition.z = self.minBoundary.z
            self.currPosition.y = self.minBoundary.y
            self.currPosition.x += 1
        #meet maxBoundary
        else:
            print("boundary reached")
            self.reachEnd = True
            return action

        #print("new location is: ", self.currPosition)
        return action
'''

# main function
if __name__ == '__main__':

    # clear the world
    clearMin = Point(x=-100, y=0, z=-50)
    clearMax = Point(x=100, y=100, z=50)
    worldReset(clearMin, clearMax)

    # generate noise block
    generateRandomNoiseBlock(Point(x=0,y=4,z=0), 6)

    # load the saved model
    loadedModel = tf.keras.models.load_model('models/paddedModel.h5')
    loadedModel.summary()

    #######################  need to be fixed without hard-code ###############
    # go through all the blocks
    for xAxis in range(0, 6):
        for yAxis in range(4, 10):
            for zAxis in range(0, 6):
                excludingType = [5, 93, 10, 60]
                minMax = locateMinMax(Point(x=-1, y=0, z=-1), Point(x=7, y=10, z=7), excludingType)

                # Get the current building data
                currBuilding = client.readCube(Cube(
                    min=minMax[0],
                    max=minMax[1]
                ))
                # print(currBuilding)
                moveToCoord = Point(x=0,y=4,z=0)
                newMinMax = [moveToCoord, Point(x=moveToCoord.x+5, y=moveToCoord.y+5, z=moveToCoord.z+5)]

                # Process the blocks data
                oneHotEncodedInputBlocks = transformInputForModel(currBuilding, newMinMax[0])

                # Predict the block to replace current position block using the model 
                predictions = loadedModel.predict(oneHotEncodedInputBlocks)
                print("Predictions=", predictions)
                
                # Generate arg maxes for predictions
                predictedNewBlock = np.argmax(predictions, axis = 1)
                predictedNewBlock = predictedNewBlock[0]
                print("Predicted new block -> ", predictedNewBlock)

                # dict to map ordinal values to cube types
                reverseValueMap = {0:5, 1:41, 2:60, 3:88, 4:131, 5:160, 6:224, 7:247, 8: 5}

                # replace the current location of agent with the predicted block
                singleBlockChange(Point(x=xAxis,y=yAxis,z=zAxis), reverseValueMap[predictedNewBlock])

                # copy agent action to show building being built
                singleBlockChange(Point(x=xAxis + 15,y=yAxis,z=zAxis), reverseValueMap[predictedNewBlock])
