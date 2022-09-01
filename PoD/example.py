from turtle import position
import grpc

import minecraft_pb2_grpc
from minecraft_pb2 import *

#test functions

#clear out game world, moved platform etc
def clearOut(minPoint, maxPoint):
    client.fillCube(FillCubeRequest(  # Clear a 20x10x20 working area
        cube=Cube(
            min = minPoint,
            max = maxPoint
        ),
        type=AIR
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


channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)


clearMin = Point(x=-500, y=4, z=-500)
clearMax = Point(x=500, y=14, z=500)
clearOut(clearMin, clearMax)


#client.spawnBlocks(Blocks(blocks=[]))
client.spawnBlocks(Blocks(blocks=[  # Spawn a flying machine
    # Lower layer
    Block(position=Point(x=1, y=5, z=1), type=CONCRETE, orientation=NORTH),
    Block(position=Point(x=1, y=5, z=0), type=SLIME, orientation=NORTH),
    Block(position=Point(x=1, y=5, z=-1), type=STICKY_PISTON, orientation=SOUTH),
    Block(position=Point(x=1, y=5, z=-2), type=CONCRETE, orientation=NORTH),
    Block(position=Point(x=1, y=5, z=-4), type=SLIME, orientation=NORTH),
    # Upper layer
    Block(position=Point(x=1, y=6, z=0), type=REDSTONE_BLOCK, orientation=NORTH),
    Block(position=Point(x=1, y=6, z=-4), type=REDSTONE_BLOCK, orientation=NORTH),
    # Activate
    Block(position=Point(x=1, y=6, z=-1), type=QUARTZ_BLOCK, orientation=NORTH),
    
    
]))
   
#blocks = client.readCube(Cube(
#    min=Point(x=1, y=5, z=-4),
#    max=Point(x=1, y=6, z=1)
#))

blocks = client.readCube(Cube(
    min=Point(x=1, y=5, z=-4),
    max=Point(x=1, y=6, z=1)
))

singleBlock = client.readCube(Cube(Point(x=1, y=5, z=-4)))

print(singleBlock)
#blocks[2].type = AIR
print(blocks)

#read func test (flying machine loc)
minPoint = Point(x=1, y=5, z=-4)
maxPoint = Point(x=1, y=6, z=1)

readBlocks = readSingleCubes(minPoint, maxPoint)

print("below is single read result")
print(readBlocks[0].position)





