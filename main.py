from collectors.process_collector import collect_one_process_event
from storage.writer import write_event

def main():
    event = collect_one_process_event()
    if event is not None:
        write_event(event)
        print("✔ Telemetry event written")

if __name__ == "__main__":
    main()
