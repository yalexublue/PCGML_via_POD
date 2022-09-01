#from turtle import position
import grpc
import numpy as np
import pandas as pd
import csv

import minecraft_pb2_grpc
from minecraft_pb2 import *
from PoD import locateMinMax

# connect to the server
channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)

# get the boundries positions of the building
minMax = locateMinMax(Point(x=50, y=2, z=10), Point(x=53, y=6, z=15))
print(minMax, "minMax")

# read all the blocks in the range
blocks = client.readCube(Cube(
    min=Point(x=minMax[0].x, y=minMax[0].y, z=minMax[0].z),
    max=Point(x=minMax[1].x, y=minMax[1].y, z=minMax[1].z)
))

# create a 3D array with the max required dimensions, added + 1 to handle index errors
threedArr = np.full((minMax[1].x + 1, minMax[1].y + 1, minMax[1].z + 1), 5)
print(threedArr.shape)
for block in blocks.blocks:
    print(block.position.x, block.position.y, block.position.z)
    threedArr[block.position.x][block.position.y][block.position.z] = block.type
print(threedArr)

# flatten the array
flattenedArray = np.stack(threedArr, axis=1).flatten()

# add shape data to the flattened array
# flattenedArray.append(threedArr.shape)
flattenedArray = np.append(flattenedArray, threedArr.shape)
print(flattenedArray, flattenedArray.shape)

# convert array into dataframe
DF = pd.DataFrame(flattenedArray)
  
# save the dataframe as a csv file
DF.to_csv("data1.csv", index=False)
