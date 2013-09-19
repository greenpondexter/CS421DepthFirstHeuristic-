__author__ = 'Owner'
import random
import math
import sys
sys.path.append("/Users/Chris/Programming/AIA/up-antics_02Sep2013/Antics")
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import *
from AIPlayerUtils import *
from Move import Move
from Building import *
from GameState import *
from Location import *
import sys
##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "The Hufflepuff")#FINDS the best path
        self.foodSwitch = False
        self.chosenFoodCoords = None

    ##
    # distance
    #
    # Description: calculates the length between coordinates by sum of deltaX and deltaY of two
    # coordinates on the board (not the hypotenuse)
    #
    # Parameters:
    #   tuple1, tuple2 - coordinates between which distance is measured (tuple), (tuple)
    #
    # Return: the sum distance of the two legs between the coordinates(int)
    #
    def distance(self, tuple1, tuple2):
        return int(math.fabs(tuple1[0]-tuple2[0]) + math.fabs(tuple1[1]-tuple2[1]))    ##

    ##
    #simulateMove
    #
    #Description: takes a single move and a copy of the gameState and reflects the details of the
    #  move onto the new gameState
    #
    #Parameters:
    #   move: the move that is affecting the gameState (Move)
    #   newState: a copy of the state of the game, which is being changed by the move (GameState)
    #
    #Return: newState, a copy of the gameState that has been altered as per the move
    #
    def simulateMove(self, move, newState):
        #designating the inventories to variables
        for inv in newState.inventories:
            if inv.player == newState.whoseTurn:
                myInv = inv
            else:
                theirInv = inv
        #if an ant is moved
        if move.moveType == MOVE_ANT:
            #clarifying where the ant is and where its going
            src = move.coordList[0]
            dst = move.coordList[-1]
            #moves the ant to the dst and clears the destination
            #newState.board[dst[0]][dst[1]].ant = newState.board[src[0]][src[1]].ant
            #newState.board[src[0]][src[1]].ant = None
            #assigns the ant to myAnt and changes its coords in the inventory
            for ant in myInv.ants:
                if ant.coords == src:
                    ant.coords = dst
                    myAnt = ant
            #finds the ant worthiest for attack
            inRange = self.getAttack(newState, myAnt, theirInv.ants).coords
            #attacks the inRange ant by lowering its health by one
            if inRange is not None:
                #lowers ant health by attack power of myAnt
                attackPower = UNIT_STATS[myAnt.type][ATTACK]
                #newState.board[inRange[0]][inRange[1]].ant.health -= attackPower
                for ant in theirInv.ants:
                    if ant.coords == inRange:
                        ant.health -= attackPower
                #removes the ant if its health is 0
                if newState.board[inRange[0]][inRange[1]].ant.health <= 0:
                    deadAnt = newState.board[inRange[0]][inRange[1]].ant
                    newState.board[inRange[0]][inRange[1]].ant = None
                    theirInv.ants.remove(deadAnt)
            #finds rules for ants sitting on food, tunnels or anthills
            for ant in myInv.ants:
                constr = newState.board[ant.coords[0]][ant.coords[1]].constr
                #narrows rule to apply only for workers sitting on a construction
                if ant.type == WORKER and constr is not None:
                    #if on my side of the board, compensate for food transportation
                    if ant.coords[1] < 4:
                        if constr.type == FOOD and not ant.carrying:
                            ant.carrying = True
                        elif constr.type <= TUNNEL and ant.carrying:
                            ant.carrying = False
                            inv.foodCount += 1
                    #if the worker is sitting on an anthill or tunnel on the other side of the
                    #board, modify capture health
                    elif constr.type <= TUNNEL:
                        if constr.captureHealth > 1:
                            constr.captureHealth -= 1
                            newState.board[ant.coords[0]][ant.coords[1]].constr = constr
                            for c in theirInv.constrs:
                                if c.coords == constr.coords:
                                    c = constr
                        #remove if the constr is at health one
                        else:
                            newState.board[ant.coords[0]][ant.coords[1]].constr = None
                            theirInv.constrs.remove(constr)

        #deals with build actions
        if move.moveType == BUILD:
            loc = move.coordList[0]
            #deals with building a tunnel
            if move.buildType == TUNNEL and myInv.foodCount >= 10:
                #adjusts food count
                myInv.foodCount -= CONSTR_STATS[TUNNEL][COST]
                #creates the new building as per specified
                newBuilding = Building(loc, TUNNEL, newState.whoseTurn)
                #fits newBuilding into the board and inventory
                newState.board[loc[1]][loc[1]].constr = newBuilding
                myInv.constrs.append(newBuilding)
            #deals with building an ant, works the same as tunnel except with ant objects
            else:
                myInv.foodCount -= UNIT_STATS[move.buildType][COST]
                newAnt = Ant(loc, move.buildType, newState.whoseTurn)
                newState.board[loc[1]][loc[1]].ant = newAnt
                myInv.ants.append(newAnt)
        #update the inventories and return the state
        for inv in newState.inventories:
            if inv.player == newState.whoseTurn:
                inv = myInv
            else:
                inv = theirInv
        return newState

    ##
    #stateQuality
    #
    #Description: weighs in on multiple influencing factors to find a numerically scaled quality
    #  for the state
    #
    #Parameters:
    #   newState - a copy of the state after a move that might be taken
    #
    #Return: a value quantifying the quality of the state <= 1 and >= 0 (double)
    #
    def stateQuality (self, newState, currentState):
        #assigns the inventories to variables
        for inv in newState.inventories:
            if inv.player == newState.whoseTurn:
                myInv = inv
            else:
                theirInv = inv
        #variables is a list of tuples, the first element of the tuple is the variable, the second
        #is its weight in the final quality percentage
        variables = []

        variables.append((self.winningMove(myInv, theirInv, newState), .01))
        variables.append((self.hasLost(myInv), .01))
        variables.append((self.varProximityToFood(myInv, newState), .4))
        variables.append((self.varProximityToAnthill(myInv, newState), .4))
        variables.append((self.varQueenProximityToCorner(myInv), .2))

        if variables[0] == 100:
            return 1
        elif variables[1] == 100:
            return 0
        #print self.foodSwitch
        #print variables
        # finds the numerator and denominator of the stateQuality double by finding the weighted
        #percentage of the collective variables
        numerator = denominator = 0
        for i in range(len(variables)):
            numerator += (variables[i][0]*variables[i][1])
            denominator += variables[i][1]
        return numerator/denominator


    ## VAR HELPER METHODS
    ##
    ##Description: returns the success in the field of a single variable
    ##
    ##Returns: a value quantifying success of a single factor <=1 >=0(double)
    ##



    ##
    #getCurrPlayerFoodLocation
    #
    #Description: finds the coords of HufflePuff's closest food
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #   theirInv = a copy of the new proposed game state
    #
    #Return: a value quantifying the quality of the state <= 1 and >= 0 (double)
    #

    def getCurrPlayerFoodLocation(self, myInv, newState):
        foodLocations = []
        #look for the two food items on Hufflepuff's side and append them foodLocations[]
        for col in range (0,10):
            for row in range (0,4):
                if not newState.board[col][row].constr == None:
                    if newState.board[col][row].constr.type == FOOD:
                        foodLocations.append(newState.board[col][row].coords)

        #find the anthill
        for constr in myInv.constrs:
            if constr.type == ANTHILL:
                anthill = constr.coords

        #get the distances between the anthill and the two food locations in hopes of finding the shortest distance
        anthillToFoodLocationOneDistance = self.distance(foodLocations[0], anthill)
        anthillToFoodLocationTwoDistance = self.distance(foodLocations[1], anthill)

        if anthillToFoodLocationOneDistance < anthillToFoodLocationTwoDistance:
            return foodLocations[0]
        else:
            return foodLocations[1]

    ##
    #varQueenProximityToCorner
    #
    #Description: weighs in on multiple influencing factors to find a numerically scaled quality
    #  for how close the queen is to the back left corner
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #
    #Return: a value quantifying the quality of the state <= 1 and >= 0 (double)
    #
    def varQueenProximityToCorner(self, myInv):
        counter = 0
        for ant in myInv.ants:
            if ant.type == QUEEN:
                row = random.randint(0, 1)
                col = random.randint(0, 1)
                distance = self.distance(ant.coords, (row,col))

                if distance > 4:
                    counter += .2
                elif distance > 3:
                    counter += .3
                elif distance > 2:
                    counter += .4
                elif distance > 1:
                    counter += .5
                elif distance > 0:
                    counter += .7
                elif distance == 0:
                    counter = 1
                return counter

    #varQueenProximityToFood
    #
    #Description: weighs in on multiple influencing factors to find a numerically scaled quality
    #  for how close a given worker is ant to food
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #   newState - a copy of the new proposed game state
    #
    #Return: a value quantifying the quality of the state <= .7 and >= 0 (double)
    #
    def varProximityToFood(self, myInv, newState):
        counter = 0
        #get the coordinates of the closest food item
        foodCoords = self.getCurrPlayerFoodLocation(myInv, newState)
        self.chosenFoodCoords = foodCoords
        #look for a worker and who isn't carrying food and try and guide it to the food
        for ant in myInv.ants:
            if ant.type == WORKER and self.foodSwitch == False and (ant.carrying == False or ant.coords == foodCoords):
                #get the distance between the food and the ant
                distance = self.distance(ant.coords, foodCoords)
                if ant.coords == foodCoords:
                    self.foodSwitch = True
                    counter += .1
                    return counter
                if distance > 4:
                    counter += .2
                elif distance > 3:
                    counter += .3
                elif distance > 2:
                    counter += .4
                elif distance > 1:
                    counter += .5
                elif distance > 0:
                    counter += .7
                elif distance == 0:
                    counter += 1

        return counter

    #varQueenProximityToAnthill
    #
    #Description: weighs in on multiple influencing factors to find a numerically scaled quality
    #  for how close a worker ant carrying food is to it's respective anthill
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #   newState - a copy of the new proposed game state
    #
    #Return: a value quantifying the quality of the state <= 1 and >= 0 (double)
    #
    def varProximityToAnthill(self, myInv, newState):
        counter = 0
        anyAntsCarrying = self.isCarrying(myInv)
        #get the coords for the anthill
        for constr in myInv.constrs:
            if constr.type == ANTHILL:
                anthillCoords = constr.coords
        #determine wheter or not an any in your inventory is carrying food
        for ant in myInv.ants:
            #if so, turn the foodswith on (true) so ant can tyr and find its anthill to cash in
            if anyAntsCarrying == True:
                self.foodSwitch == True
            #if the given ant is a worker, try and get it close to the anthill
            if ant.type == WORKER and self.foodSwitch == True and (ant.carrying == True or ant.coords == anthillCoords):
                #determine the distance between the anthill and the given ant
                distance = self.distance(anthillCoords, ant.coords)
                #it would at minimum require me 15+ sentences to give a less than satisfactory explanation for, much
                #less an adaquete one
                if not newState.board[self.chosenFoodCoords[0]][self.chosenFoodCoords[1]].ant == None and \
                            ant.coords == anthillCoords and anyAntsCarrying == True:
                    self.foodSwitch == False
                    return -1
                #this essentially triggers the ants to start finding food again, as
                elif ant.coords == anthillCoords and anyAntsCarrying == False:
                    self.foodSwitch = False
                    counter += .8
                    return counter
                elif distance > 4:
                    counter += .1
                elif distance > 3:
                    counter += .11
                elif distance > 2:
                    counter += .2
                elif distance > 1:
                    counter += .2
                elif distance > 0:
                    counter += .3
                elif distance == 0:
                    counter += .8

        if counter > 1:
            counter = 1
        return counter

    #winningMove
    #
    #Description: checks if the new proposed state is in fact a winning state
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #   theirInv = a copy of the opponents inventory
    #   newState - a copy of the new proposed game state
    #
    #Return: a value quantifying the quality of the state <= 100 and >= 0 (double)
    #
    def winningMove(self, myInv, theirInv, newState):
        if myInv.foodCount == 11:
            return 100

        for ants in theirInv.ants:
            if ants.type == QUEEN:
                return 0

        return 100

    #hasLost
    #
    #Description: checks if the new proposed state is in fact a losing state
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #   newState - a copy of the new proposed game state
    #
    #Return: a value quantifying the quality of the state <= 100 and >= 0 (double)
    #
    def hasLost(self, myInv):
        for ants in myInv.ants:
            if ants.type == QUEEN:
                return 0
        return 100

    #isMoving
    #
    #Description: a helper method for varProximityToAnthill that acts a switch of sorts for whether or not an
    # ant should should try to locate the anthill (necessary if it is carrying food)
    #
    #Parameters:
    #   myInv - a copy of HufflePuff's inventory
    #
    #Return: a boolean value depending on whether or not any ant in a player's inventory is carrying food
    #
    def isCarrying(self, myInv):
        for ant in myInv.ants:
            if ant.carrying == True:
                return True
        return False

    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):

                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        bestMove = None
        bestProbability = None
        for move in listAllLegalMoves(currentState):
            #print "1"
            newMove = move
            newState = self.simulateMove(move, currentState.fastclone())
            if bestMove is None or bestProbability < self.stateQuality(newState, currentState):
                bestMove = move
                bestProbability = self.stateQuality(newState, currentState)
                print bestProbability
                print bestMove
        return bestMove

    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #finds the ant worthiest for attack
        range = UNIT_STATS[attackingAnt.type][RANGE]
        inRange = None
        #iterate through enemy ants
        for inv in currentState.inventories:
            if currentState.whoseTurn != inv.player:
                for ant in inv.ants:
                    #if the enemy ant is within range of attack
                    if range >= self.distance(ant.coords,attackingAnt.coords):
                        #if inRange is undefined or the ant is a queen, redefine bestAnt
                        if inRange is None or ant.type == QUEEN:
                            inRange = ant.coords
                        #if the ant inRange isn't the queen, attack the ant with less health
                        elif inRange != inv.getQueen().coords:
                            if currentState.board[inRange[0]][inRange[1]].ant.health > ant.health:
                                inRange = ant.coords
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]




board = [[Location((col, row)) for row in xrange(0,BOARD_LENGTH)] for col in xrange(0,BOARD_LENGTH)]
inventories = []
inv1 = None
inv2 = None
ants = []
constrs = []


num = 15
i = 0
locations = []
#Generate 15 random locations on PLAYER_ONE side for the
# Anthill, Tunnel
# 9 Pieces of Grass
# Worker and Queen
# 2 Food Objects

while i < num:
    if i == 0:
        x = random.randint(0, 9)
        y = random.randint(0, 4)
        locations.append((x,y))
        i+= 1
    else:
         x = random.randint(0, 9)
         y = random.randint(0, 4)
         while (x,y) in locations:
            x = random.randint(0, 9)
            y = random.randint(0, 4)
         locations.append((x,y))
         i+= 1

print locations
sys.stdout.flush()

board[locations[0][0]][locations[0][1]].ant = None
#create ANTHILL construction object
construction = Construction((locations[0][0], locations[0][1]), ANTHILL)
# add this object to the constrs [], which will individually be added to PLAYER_ONE inventory
constrs.append(construction)

board[locations[0][0]][locations[0][1]].constr = construction
board[locations[0][0]][locations[0][1]].coords = (locations[0][0], locations[0][1])

board[locations[1][0]][locations[1][1]].ant = None
construction = Construction((locations[1][0], locations[1][1]), TUNNEL)
# add this object to the constrs [], which will individually be added to PLAYER_ONE inventory
constrs.append(construction)

board[locations[1][0]][locations[1][1]].constr = construction
board[locations[1][0]][locations[1][1]].coords = (locations[1][0], locations[1][1])

#Creating GRASS objects and adjusting the board locatios accordingly
for i in range(2,11):
    coords = (locations[i][0], locations[i][1])
    construction = Construction((locations[i][0], locations[i][1]), GRASS)

    board[locations[i][0]][locations[i][1]].constr = construction
    board[locations[i][0]][locations[i][1]].ant = None
    board[locations[i][0]][locations[i][1]].coords = coords



ant_1 = Ant((locations[11][0], locations[11][1]), QUEEN, PLAYER_ONE)
# add this object to the ants[], which will individually be added to PLAYER_ONE inventory
ants.append(ant_1)

ant_2 = Ant((locations[12][0], locations[12][1]), WORKER, PLAYER_ONE)
# add this object to the ants[], which will individually be added to PLAYER_ONE inventory
ants.append(ant_2)

board[locations[11][0]][locations[11][1]].ant = ant_1
board[locations[12][0]][locations[12][1]].ant = ant_2

food1 = Construction((locations[13][0], locations[13][1]), FOOD)
food2 = Construction((locations[14][0], locations[14][1]), FOOD)

board[locations[13][0]][locations[13][1]].constr = food1
board[locations[14][0]][locations[14][1]].constr = food2


# create inventory object for player one, this will be added to the Inventories [] list object for the Gamestate
inv1 = Inventory(PLAYER_ONE, ants, constrs, 3)



##-------------------##
#PLAYER 2
ants2 = []
constrs2 = []

num = 15
i = 0
locations = []
#Generate 15 random locations on PLAYER_TWO side for the
# Anthill, Tunnel
# 9 Pieces of Grass
# Worker and Queen
# 2 Food Objects
while i < num:
    if i == 0:
        x = random.randint(0, 9)
        y = random.randint(5, 9)
        locations.append((x,y))
        i+= 1
    else:
         x = random.randint(0, 9)
         y = random.randint(5, 9)
         while (x,y) in locations:
            x = random.randint(0, 9)
            y = random.randint(5, 9)
         locations.append((x,y))
         i+= 1


board[locations[0][0]][locations[0][1]].ant = None
#create ANTHILL construction object
construction = Construction((locations[0][0], locations[0][1]), ANTHILL)
# add this object to the constrs [], which will individually be added to PLAYER_TWO inventory
constrs2.append(construction)

board[locations[0][0]][locations[0][1]].constr = construction
board[locations[0][0]][locations[0][1]].coords = (locations[0][0], locations[0][1])

board[locations[1][0]][locations[1][1]].ant = None
construction = Construction((locations[1][0], locations[1][1]), TUNNEL)
# add this object to the constrs [], which will individually be added to PLAYER_TWO inventory
constrs2.append(construction)

board[locations[1][0]][locations[1][1]].constr = construction
board[locations[1][0]][locations[1][1]].coords = (locations[1][0], locations[1][1])

#Creating GRASS objects and adjusting the board locations accordingly
for i in range(2,11):
    coords = (locations[i][0], locations[i][1])
    construction = Construction((locations[i][0], locations[i][1]), GRASS)

    board[locations[i][0]][locations[i][1]].constr = construction
    board[locations[i][0]][locations[i][1]].ant = None
    board[locations[i][0]][locations[i][1]].coords = coords



ant_1 = Ant((locations[11][0], locations[11][1]), QUEEN, PLAYER_ONE)
# add this object to the ants[], which will individually be added to PLAYER_ONE inventory
ants2.append(ant_1)

ant_2 = Ant((locations[12][0], locations[12][1]), WORKER, PLAYER_ONE)
# add this object to the ants[], which will individually be added to PLAYER_ONE inventory
ants2.append(ant_2)

board[locations[11][0]][locations[11][1]].ant = ant_1
board[locations[12][0]][locations[12][1]].ant = ant_2

food1 = Construction((locations[13][0], locations[13][1]), FOOD)
food2 = Construction((locations[14][0], locations[14][1]), FOOD)

board[locations[13][0]][locations[13][1]].constr = food1
board[locations[14][0]][locations[14][1]].constr = food2


# create inventory object for player one, this will be added to the Inventories [] list object for the Gamestate
inv2 = Inventory(PLAYER_TWO, ants2, constrs2, 3)

inventories.append(inv2)

gamestate = GameState(board, inventories, PLAY_PHASE, PLAYER_ONE)


print gamestate.phase
john = AIPlayer("The Huff")





