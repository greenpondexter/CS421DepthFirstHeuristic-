import random
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
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
        super(AIPlayer,self).__init__(inputPlayerId, "Random")
    
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
        #Get my inventory
        myInv = None
        for inv in currentState.inventories:
            if inv.player == currentState.whoseTurn:
                myInv = inv
                break
        #If my inventory is still none, then I don't have one.
        if myInv == None:
            return Move(END, None, None)
        #Try to build an ant
        if myInv.foodCount >= UNIT_STATS[SOLDIER][COST]:  #is there enough food?
            #Detect whether the anthill has nothing on top of it
            hill = myInv.getAnthill()
            if currentState.board[hill.coords[0]][hill.coords[1]].ant == None:
                #build a random ant
                toPlace = random.randint(WORKER, R_SOLDIER)
                return Move(BUILD, [hill.coords], random.randint(WORKER, R_SOLDIER))
        #See if you can move any ants
        antsToMove = []
        for ant in myInv.ants:
            if not ant.hasMoved:
                antsToMove.append(ant)
        #Move first of these ants
        if antsToMove != []:
            chosen = antsToMove[0]
            coordList = [chosen.coords]
            totalCost = 0
            lastStep = None
            while totalCost < UNIT_STATS[chosen.type][MOVEMENT]:
                #pick a random direction that won't move me back.
                possibleDirections = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                validDirections = []
                for direction in possibleDirections:
                    nextLoc = addCoords(coordList[-1], direction)
                    #Check that the move would be inside the board bounds
                    if nextLoc[0] > 9 or nextLoc[0] < 0 or nextLoc[1] > 9 or nextLoc[1] < 0:
                        continue
                    #Check that the move cost would not exceed what this ant is capable of
                    costOfStep = currentState.board[nextLoc[0]][nextLoc[1]].getMoveCost()
                    if currentState.board[nextLoc[0]][nextLoc[1]].ant == None and UNIT_STATS[chosen.type][MOVEMENT] >= totalCost + costOfStep:
                        validDirections.append(direction)
                #If no directions are valid, break out of the loop.
                if validDirections == []:
                    break
                else:
                    #Choose a random direction
                    randDir = random.randint(0, len(validDirections) - 1)
                    #Apply it
                    nextCoord = addCoords(coordList[-1], validDirections[randDir])
                    coordList.append(nextCoord)
                    #Add its cost to the total move cost
                    totalCost += currentState.board[nextCoord[0]][nextCoord[1]].getMoveCost()
            #Return the chosen move
            return Move(MOVE_ANT, coordList, None)
        #If I can't to anything, end turn
        return Move(END, None, None)
    
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
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]
