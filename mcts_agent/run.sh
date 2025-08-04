output_file="testing.txt"

for i in {1..50}
do
    echo "GAME ${i}: $(python -m referee -t 180 -s 250 agent:Agent_MCTS_C agent:Agent_MCTS)" | tee -a "$output_file"
done