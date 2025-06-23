import os
import sys
import time
import threading
import json

def read_fifo(path, label):
    while True:
        try:
            with open(path, 'r') as f:
                for line in f:
                    print(f"[{label}] {line.strip()}")
        except Exception as e:
            print(f"[{label}] Error: {e}")
            time.sleep(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Watch and echo FIFO contents.")
    parser.add_argument('--config', type=str, default='fifo_writer_config.json', help='Path to config JSON file')
    args = parser.parse_args()

    # Load config from JSON
    with open(args.config, 'r') as f:
        config = json.load(f)
    base_path = config.get('base_path', '.')
    fifo_names = config.get('fifo_names', [
        'float1.fifo',
        'float2.fifo',
        'int1.fifo',
        'int2.fifo',
        'array.fifo'
    ])

    fifo_paths = [os.path.join(base_path, name) for name in fifo_names]

    print("Waiting for FIFOs to exist...")
    while not all(os.path.exists(p) for p in fifo_paths):
        time.sleep(0.5)

    threads = []
    for path, label in zip(fifo_paths, fifo_names):
        t = threading.Thread(target=read_fifo, args=(path, label), daemon=True)
        t.start()
        threads.append(t)

    print("Watching FIFOs. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
