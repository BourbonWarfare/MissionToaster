import sys
import os
import subprocess
import logging

# file paths
path_project = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
path_mission_pbos = os.path.join(path_project, "mission_pbos")
path_bankrev_exe = os.path.join(path_project, "bin", "BankRev.exe")


def main():
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG)
    if (not os.path.isfile(path_bankrev_exe)): raise Exception(f"Missing {path_bankrev_exe}")

    with os.scandir(path_mission_pbos) as it:
        for file in it:
            if file.is_file() and file.name.endswith(".pbo"):
                cmd_depbo = [path_bankrev_exe]
                cmd_depbo.extend(["-f", os.path.join(path_project, "missions")])
                cmd_depbo.extend([file.path])
                result = subprocess.run(cmd_depbo, capture_output=True, text=True, timeout=10)
                logging.info(f"{file.name} extracted [{result.returncode}]")


if __name__ == "__main__":
    sys.exit(main())
