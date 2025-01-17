# 階層フォルダ"simulation"のagentファイルから、SimulationAgentを参照
# from simulation.agent import SimulationAgent
from simulator.agent import SimulationAgent
from simulation import run_simulation
#import simulation

def main():
    task_priority = None
    agents = None
    tasks = None
    seed = None
    max_step = None
    charge_station = None
    break_prob = None
    run_simulation(task_priority, agents, tasks, seed, max_step, charge_station, break_prob)
    # simulation.run_simulation(task_priority, agents, tasks, seed, max_step, charge_station, break_prob)

if __name__ == "__main__":
    main()
