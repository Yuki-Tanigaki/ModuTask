import argparse
from modutask.simulator.simulation import Simulator

def main():
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    simulator = Simulator(args.property_file)
    simulator.run_simulation()

if __name__ == '__main__':
    main()
