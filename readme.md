### Getting Started

The files 'mcts_agent', 'rand_agent' and 'referee' must be in the same folder in order for this to run correctly. 'mcts_agent' refers to the AI agent that utilises the Monte Carlo Tree Search method in order to play the game while 'rand_agent' refers to the game playing agent that places random moves.

To run the game, enter this into the terminal:

```
python -m referee <agent> <agent>
```

An example of putting an 'mcts_agent' against another 'mcts_agent would be:

'''
python -m referee mcts_agent mcts_agent 
'''


