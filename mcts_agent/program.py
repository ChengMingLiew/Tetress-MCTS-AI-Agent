import math, copy, random
from referee.game import PlayerColor, Action, PlaceAction
from .selfboard import *
import time

# constants to be adjusted for game optimisation and running
UCB_CONST = math.sqrt(2)
EXPAND_LIMIT = 25
ROLLOUT_LIMIT = 150

# class of nodes (parents/children) to be used in the tree
class Node:
    def __init__(self, board: Selfboard, color: PlayerColor, action: PlaceAction, parent=None):
        self.board = board
        self.poss_child_actions = []
        self.color = color
        self.wins = 0
        self.visits = 0
        self.action = action
        self.parent = parent
        self.children = []
        self.num_poss_child = 0

# the game-playing agent for Monte Carlo Tree Search
class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Tetress game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = color
        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as RED")
            case PlayerColor.BLUE:
                print("Testing: I am playing as BLUE")

        self.node = Node(Selfboard(), color, None, None)      

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object. 
        """

        self.node.poss_child_actions = find_all_actions(self.node.board, self.node.board.turn_color)
        self.node.num_poss_child = len(self.node.poss_child_actions)
        self.node = monte_carlo_tree_search(self.node, referee)

        return self.node.action

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        """
        This method is called by the referee after an agent has taken their
        turn. You should use it to update the agent's internal game state. 
        """

        # the action type is PlaceAction
        place_action: PlaceAction = action

        if self._color != color:
            self.node.board.apply_action(action)
        else:
            print(self.node.board.render())
        self.node.color = color

        
# main function for the Monte Carlo Tree Search
def monte_carlo_tree_search(root: Node, referee: dict):

    start_time = time.process_time()
    root.parent = None
    root.wins = 0
    root.visits = 0
    root.children = []

    i = 0
    # checking for computational time/space and rollout capacity
    while resources_left(referee) and i in range (ROLLOUT_LIMIT):
        leaf = traverse(root)
        simulation_result = rollout(leaf)
        backpropagate(leaf, simulation_result)
        i += 1
    print(time.process_time() - start_time)

    return best_child(root)

# compare upper confidence bound value of children and return best node
def best_ucb1(node):

    maxi = calc_ucb(node, node.children[0])
    maxn = node.children[0]

    if len(node.children) > 1:
        for n in node.children[1:]:
            test = calc_ucb(node, n)
            if test > maxi:
                maxi = test
                maxn = n

    return maxn

# calculate upper confidence bound value
def calc_ucb(parent, node):
    ucb = (node.wins / node.visits) + UCB_CONST * math.sqrt(math.log(parent.visits)/node.visits)
    return ucb

# generates a new child node from the list of possible actions from the parent state
def pick_unvisited(node):

    if len(node.poss_child_actions) == 0:
        return node
    
    # picks an possible action and removes it from the list
    testaction = random.choice(node.poss_child_actions)
    node.poss_child_actions.remove(testaction)

    newboard = copy.deepcopy(node.board)
    newboard.apply_action(testaction)

    # creating a newnode
    newnode = Node(newboard, node.board.turn_color, testaction)
    newnode.parent = node
    newnode.poss_child_actions = find_all_actions(newboard, newboard.turn_color)
    newnode.num_poss_child = len(newnode.poss_child_actions)
    node.children.append(newnode)

    return newnode

# if all possible children have been generated, the node is fully expanded
def fully_expanded(node):
    if len(node.children) == node.num_poss_child:
        return True
    return False

# function for node traversal
def traverse(node):
    
    while fully_expanded(node):       
        # edge case for a terminal node
        if node.num_poss_child == 0:
            return node          
        node = best_ucb1(node)
         
    # in case no children are present / node is terminal
    return pick_unvisited(node)

# check final result of node and return winning color
def result(board):
    if board.turn_color == PlayerColor.RED:
        return PlayerColor.BLUE
    return PlayerColor.RED

# function for conducting simulation to obtain result node
def rollout(node):

    testboard = copy.deepcopy(node.board)
    
    # tests next move until no action can be found
    while True:
        action = find_random_action(testboard, testboard.turn_color)
        if action == None:
            break
        testboard.apply_action(action)
    
    return result(testboard)

# check if the node is the root
def is_root(node):
    if not node.parent:
        return True
    return False

# updates the node stats with the result
def update_stats(node, result):
    node.visits += 1
    if result == node.color:
        node.wins += 1
    return
 
# continuously sends the results "back up" the tree
def backpropagate(node, result):
    update_stats(node, result)

    # continue backpropagating if not root
    if is_root(node):
        return
    backpropagate(node.parent, result)
 
# selects best child with highest number of visits
def best_child(node):

    best = node.children[0]
    maxv = (node.children[0]).visits

    if len(node.children) > 1:
        for child in node.children[1:]:
            if child.visits > maxv:
                maxv = child.visits
                best = child

    return best

# check to ensure resource limit not exceeded
def resources_left(referee: dict):
    
    time = referee["time_remaining"]
    space = referee["space_remaining"]

    if (time == None or time < 0 )and (space == None or space < 0):
        return True    

    if time != None and (space == None or space < 0):
        if time > 0 :
            return True 
            
    if space != None and (time == None or time < 0):
        if space > 0:
            return True

    if time > 0 and space > 0:
        return True
    
    return False