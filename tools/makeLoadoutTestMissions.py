# for all files in /loadouts, create a dummy mission in /missions

import sys
import os
import logging
import shutil

path_project = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def main():
    path_test_mission = os.path.join(path_project, "loadouts", "tester")
    loadout_files = [f.path for f in os.scandir(os.path.join(path_project, "loadouts")) if f.is_file()]
    logging.info(f"Checking {len(loadout_files)} loadout_files")
    # loadout_files = [loadout_files[0]]  # debug - just do first one

    for path_loadout in loadout_files:
        loadout_name = os.path.basename(path_loadout).split(".")[0]
        print(f"loadout: {loadout_name}")
        path_loadout_mission = os.path.join(path_project, "missions", f"{loadout_name}.Stratis")
        if os.path.isdir(path_loadout_mission):
            print(f"  cleaning old mission: {path_loadout_mission}")
            shutil.rmtree(path_loadout_mission)
        destination = shutil.copytree(path_test_mission, path_loadout_mission)
        path_target_loadout = os.path.join(destination, "Loadouts", "_targetLoadout.hpp")
        shutil.copyfile(path_loadout, path_target_loadout)

        print(f"  made mission: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
