import os
import numpy as np
import time
import errno

FIFO_PATH = '/tmp/adapt_sim_fifo'
N_ELEMENTS = 10
NUM_PIXELS = 12 * 6 * 32  # match the simulation layout


def create_fifo(path):
    if os.path.exists(path):
        os.remove(path)
    os.mkfifo(path)
    print(f"FIFO created at {path}")


def generate_simulation_data():
    """Generate random data for all pixels."""
    return [np.random.rand(N_ELEMENTS).tolist() for _ in range(NUM_PIXELS)]


def flush_fifo(path):
    """Flush the FIFO by reading all available data."""
    try:
        with open(path, 'rb', buffering=0) as fifo:
            while True:
                try:
                    data = fifo.read(4096)
                    if not data:
                        break
                except BlockingIOError:
                    break
    except Exception:
        pass


def write_data_to_fifo(path, data):
    """Write the simulation data to the FIFO as a single line of text."""
    # Flatten and convert to CSV string
    flat = [str(x) for arr in data for x in arr]
    line = ','.join(flat) + '\n'
    with open(path, 'w') as fifo:
        fifo.write(line)
        fifo.flush()


def main():
    create_fifo(FIFO_PATH)
    print("Starting simulation data writer. Press Ctrl+C to stop.")
    while True:
        flush_fifo(FIFO_PATH)
        data = generate_simulation_data()
        write_data_to_fifo(FIFO_PATH, data)
        print("Wrote new data to FIFO.")
        time.sleep(1)  # Write new data every second


if __name__ == '__main__':
    main()
