import grpc

import minecraft_pb2_grpc
from minecraft_pb2 import *

import random
import numpy as np

from DestroyAgent import PoDAgent

channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)

"""
*********** NOTICE **********
So as for the read in result, it traverse in this order for all Blocks.blocks[0] to [size]
first z will be first to move, then next on the list is y. Finally it's x.
Sothe output maybe a bit in quite a different order than expected
******************************
"""

def ravel_index(x, dims):
    i = 0
    for dim, j in zip(dims, x):
        i *= dim
        i += j
    return i

#clear out game world, moved platform etc
def clearOut(minPoint, maxPoint, cubeType = "AIR"):
    client.fillCube(FillCubeRequest(  # Clear a 20x10x20 working area
        cube=Cube(
            min = minPoint,
            max = maxPoint
        ),
        type=cubeType
    ))

#read cubes n store in a list for easier access
def readSingleCubes(minPoint, maxPoint):
    outputBlock = []
    tempRead = Blocks()
    for i in range(minPoint.x, maxPoint.x + 1):
        for j in range(minPoint.y, maxPoint.y + 1):
            for k in range(minPoint.z, maxPoint.z + 1):
                outputBlock.append(client.readCube(Cube(
                    min = Point(x=i, y=j, z=k),
                    max = Point(x=i, y=j, z=k)
                )))
    return outputBlock 

def spawnFlyingMachine():
    client.spawnBlocks(Blocks(blocks=[  # Spawn a flying machine
        # Lower layer
        Block(position=Point(x=1, y=5, z=1), type=CLAY, orientation=NORTH),
        Block(position=Point(x=1, y=5, z=0), type=GLASS, orientation=NORTH),
        Block(position=Point(x=1, y=5, z=-1), type=BRICK_BLOCK, orientation=SOUTH),
        Block(position=Point(x=1, y=5, z=-2), type=STONE, orientation=NORTH),
        Block(position=Point(x=1, y=5, z=-4), type=SLIME, orientation=NORTH),
        # Upper layer
        Block(position=Point(x=1, y=6, z=0), type=REDSTONE_BLOCK, orientation=NORTH),
        Block(position=Point(x=1, y=6, z=-4), type=REDSTONE_BLOCK, orientation=NORTH),
        # Activate
        Block(position=Point(x=1, y=6, z=-1), type=QUARTZ_BLOCK, orientation=NORTH),
        
    ]))

def locateMinMax(minPoint, maxPoint):

    minX = maxPoint.x
    maxX = minPoint.x
    minY = maxPoint.y
    maxY = minPoint.y
    minZ = maxPoint.z
    maxZ = minPoint.z

    #print ("original min point is: ", minX, " ", minY, " ", minZ)
    #print ("original max point is: ", maxX, " ", maxY, " ", maxZ)
    allCubes = client.readCube(Cube(min=minPoint,max=maxPoint))

    for cube in allCubes.blocks:
        #print (cube.type)
        # 5 is the air block, 10 is bedrock
        # exclude air, bedrock and dirt
        if cube.type != 5 and cube.type != 10 and cube.type != 93 and cube.type != 60:
        #if cube.type != 5 and cube.type != 93:
        
            minX = min(cube.position.x, minX)
            minY = min(cube.position.y, minY)
            minZ = min(cube.position.z, minZ)

            maxX = max(cube.position.x, maxX)
            maxY = max(cube.position.y, maxY)
            maxZ = max(cube.position.z, maxZ)
        


    outputTuple = (Point(x = minX, y = minY, z = minZ), 
                    Point(x = maxX, y = maxY, z = maxZ))
    return outputTuple



def singleBlockChange (position, selectedType):
        print("position to change is: ", position)
        client.fillCube(FillCubeRequest(cube=Cube(
                        min = position,
                        max = position
                    ), type=selectedType))
    


# Give two coord to reset the world within, Ground will return grass, other will be air.
def worldReset (minCoord, maxCoord):
    print("Resetting current world")

    #reset the ground level
    clearOut(Point(x=minCoord.x, y=0, z=minCoord.z), Point(x=maxCoord.x, y=3, z=maxCoord.z), GRASS)

    #Reset the air level
    clearOut(Point(x=minCoord.x, y=4, z=minCoord.z), Point(x=maxCoord.x, y=maxCoord.y, z=maxCoord.z), AIR)

if __name__ == '__main__':

    
    #Ground level is from y = 0 to y = 3
    #Air level starts from y = 4 to above
    #Made of Grass
    accurateMin = Point(x=50, y=0, z=10)
    accurateMax = Point(x=53, y=1, z=15)
    clearMin = Point(x=-100, y=0, z=-50)
    clearMax = Point(x=100, y=100, z=50)
    
    #clearOut(clearMin, clearMax, GRASS)
    worldReset(clearMin, clearMax)
    
    

    
    




   