import subprocess
import sys
import re

def run_command(command, command_name):
    print(f"\n[{command_name}] Executing: {command}")
    print("-" * 50)
    
    process = subprocess.Popen(
        command, shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True
    )
    
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        output_lines.append(line)
        
    process.stdout.close()
    return_code = process.wait()
    
    full_output = "".join(output_lines)
    return return_code, full_output

def extract_python_coverage(output):
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if match:
        return f"{match.group(1)}%"
    return "N/A"

def extract_csharp_coverage(output):
    # Depending on how coverlet outputs to console, we might need a specific regex.
    # Currently XPlat Code Coverage outputs to an XML file. We will just check if tests passed.
    match = re.search(r'Passed:\s+(\d+),\s+Failed:\s+(\d+)', output)
    if match:
        return f"Passed: {match.group(1)}, Failed: {match.group(2)}"
    return "Coverage output available in TestResults"

def main():
    print("=" * 60)
    print("JALM TEST SUITE & COVERAGE RUNNER")
    print("=" * 60)

    # 1. Run Python Tests
    py_code, py_output = run_command("pytest --cov=app/core tests/", "Python Backend Tests")
    
    # 2. Run C# Tests
    cs_code, cs_output = run_command('dotnet test JALM.Service.Tests/JALM.Service.Tests.csproj --logger "console;verbosity=detailed"', "C# Backend Service Tests")

    print("\n" + "=" * 60)
    print("TEST REPORT SUMMARY")
    print("=" * 60)
    
    # Python Stats
    py_status = "PASS" if py_code == 0 else "FAIL"
    py_cov = extract_python_coverage(py_output)
    print(f"Python Backend Logic : [{py_status}] - Coverage: {py_cov}")
    
    # C# Stats
    cs_status = "PASS" if cs_code == 0 else "FAIL"
    cs_results = extract_csharp_coverage(cs_output)
    print(f"C# Background Service : [{cs_status}] - {cs_results}")
    print("=" * 60)

    if py_code != 0 or cs_code != 0:
        print("\nSome tests failed. Check the logs above for details.")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
