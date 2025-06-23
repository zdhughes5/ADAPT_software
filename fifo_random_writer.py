import os
import sys
import time
import random
import signal
import threading
import json
import string  # <-- for random string generation

class FifoWriter:
    def __init__(self, base_path, interval=1.0, array_length=100, fifo_names=None):
        self.base_path = base_path
        self.interval = interval
        self.array_length = array_length
        if fifo_names is None:
            self.fifo_names = [
                'float1.fifo',
                'float2.fifo',
                'int1.fifo',
                'int2.fifo',
                'array.fifo',
                'string.fifo'  # <-- add string fifo
            ]
        else:
            self.fifo_names = fifo_names
        self.fifo_paths = [os.path.join(self.base_path, name) for name in self.fifo_names]
        self.running = False
        self.threads = []

    def create_fifos(self):
        for path in self.fifo_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                os.mkfifo(path)
            except FileExistsError:
                pass

    def remove_fifos(self):
        for path in self.fifo_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def start(self):
        self.running = True
        self.create_fifos()
        self.threads = [
            threading.Thread(target=self.write_float_fifo, args=(self.fifo_paths[0],)),
            threading.Thread(target=self.write_float_fifo, args=(self.fifo_paths[1],)),
            threading.Thread(target=self.write_int_fifo, args=(self.fifo_paths[2],)),
            threading.Thread(target=self.write_int_fifo, args=(self.fifo_paths[3],)),
            threading.Thread(target=self.write_array_fifo, args=(self.fifo_paths[4],)),
            threading.Thread(target=self.write_string_fifo, args=(self.fifo_paths[5],)),  # <-- add string thread
        ]
        for t in self.threads:
            t.daemon = True
            t.start()

    def stop(self):
        self.running = False
        time.sleep(self.interval + 0.1)  # Let threads finish
        self.remove_fifos()

    def write_float_fifo(self, path):
        while self.running:
            with open(path, 'w') as f:
                value = random.uniform(-1000, 1000)
                f.write(f"{value}\n")
                f.flush()
            time.sleep(self.interval)

    def write_int_fifo(self, path):
        while self.running:
            with open(path, 'w') as f:
                value = random.randint(-1000, 1000)
                f.write(f"{value}\n")
                f.flush()
            time.sleep(self.interval)

    def write_array_fifo(self, path):
        while self.running:
            with open(path, 'w') as f:
                arr = [random.uniform(-1000, 1000) for _ in range(self.array_length)]
                arr_str = ','.join(f"{x}" for x in arr)
                f.write(f"{arr_str}\n")
                f.flush()
            time.sleep(self.interval)

    def write_string_fifo(self, path):
        while self.running:
            with open(path, 'w') as f:
                rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                f.write(f"{rand_str}\n")
                f.flush()
            time.sleep(self.interval)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test program to fill FIFOs with random data.")
    parser.add_argument('--config', type=str, default='fifo_writer_config.json', help='Path to config JSON file')
    args = parser.parse_args()

    # Load config from JSON
    with open(args.config, 'r') as f:
        config = json.load(f)
    base_path = config.get('base_path', '.')
    interval = config.get('interval', 1.0)
    array_length = config.get('array_length', 100)
    fifo_names = config.get('fifo_names', [
        'float1.fifo',
        'float2.fifo',
        'int1.fifo',
        'int2.fifo',
        'array.fifo',
        'string.fifo'  # <-- include string fifo in config
    ])

    writer = FifoWriter(base_path, interval, array_length, fifo_names)

    def cleanup(signum=None, frame=None):
        print("\nCleaning up FIFOs...")
        writer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    writer.start()
    print(f"FIFOs created in {base_path}. Writing random data every {interval} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
