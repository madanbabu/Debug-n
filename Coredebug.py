import subprocess
import re

def analyze_core_dump(core_file_path):
    """
    Analyzes a Linux core dump file using gdb.

    Args:
        core_file_path (str): The path to the core dump file.

    Returns:
        dict: A dictionary containing analysis results.
    """
    results = {
        "signal": None,
        "instruction_pointer": None,
        "stack_trace": [],
        "possible_memory_issues": [],
        "other_observations": []
    }

    try:
        # Use gdb to get basic information
        gdb_command = f"gdb -batch -ex 'info signals' -ex 'info registers' -ex 'bt' -ex 'quit' {core_file_path}"
        process = subprocess.run(gdb_command, shell=True, capture_output=True, text=True, check=True)
        gdb_output = process.stdout

        # Extract signal information
        signal_match = re.search(r"Program received signal (\w+),", gdb_output)
        if signal_match:
            results["signal"] = signal_match.group(1)

        # Extract instruction pointer
        ip_match = re.search(r"\* (?:0x[0-9a-f]+ in )?([^ ]+)", gdb_output) # More robust regex
        if ip_match:
            results["instruction_pointer"] = ip_match.group(1)

        # Extract stack trace
        stack_trace_lines = re.findall(r"#\d+ +0x[0-9a-f]+ in ([^(]+)\((.*)\) from (.+)", gdb_output)
        results["stack_trace"] = ["{} ({}) from {}".format(func.strip(), args.strip(), lib.strip()) for func, args, lib in stack_trace_lines]

        # --- More advanced analysis (requires deeper gdb interaction and parsing) ---
        # Example: Inspecting local variables in the crashing frame
        inspect_command = f"gdb -batch -ex 'frame 0' -ex 'info locals' -ex 'quit' {core_file_path}"
        inspect_process = subprocess.run(inspect_command, shell=True, capture_output=True, text=True, check=True)
        local_vars_output = inspect_process.stdout

        if "No locals." not in local_vars_output:
            results["other_observations"].append("Inspected local variables in the crashing frame.")
            # You would need to parse local_vars_output for suspicious values

        # Example: Examining memory around certain addresses (if you have hints)
        # memory_command = f"gdb -batch -ex 'x/20xw 0x...' -ex 'quit' {core_file_path}"
        # memory_process = subprocess.run(memory_command, shell=True, capture_output=True, text=True, check=True)
        # memory_output = memory_process.stdout
        # Parse memory_output for signs of corruption

    except subprocess.CalledProcessError as e:
        results["error"] = f"Error running gdb: {e}"
        results["gdb_output"] = e.stderr
    except FileNotFoundError:
        results["error"] = f"Core dump file not found: {core_file_path}"

    return results

if __name__ == "__main__":
    core_file = "/path/to/your/core.XXXX"  # Replace with the actual path
    analysis_result = analyze_core_dump(core_file)

    print("Core Dump Analysis:")
    for key, value in analysis_result.items():
        print(f"{key}:")
        if isinstance(value, list):
            for item in value:
                print(f"  - {item}")
        else:
            print(f"  {value}")
