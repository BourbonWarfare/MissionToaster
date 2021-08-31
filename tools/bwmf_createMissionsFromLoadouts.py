# for all files in ../bwmf/loadouts, create a dummy mission in /missions

from genericpath import isfile
import sys
import os
import logging
import shutil

path_project = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
path_bwmf_loadouts = os.path.join(os.path.dirname(path_project), "bwmf", "loadouts")
path_test_mission = os.path.join(path_project, "tools", "bwmf_loadoutTestMission")


def main():
    loadout_files = []
    with os.scandir(path_bwmf_loadouts) as it:
        for file in it:
            if file.is_file() and os.stat(file).st_size > 5000:  # this is dumb
                loadout_files.append(file.path)
    logging.info(f"Checking {len(loadout_files)} loadout_files")
    # loadout_files = [loadout_files[0]]  # debug - just do first one

    for path_loadout in loadout_files:
        loadout_name = os.path.basename(path_loadout).split(".")[0]
        if (loadout_name == "blankForArsenal"): continue
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
