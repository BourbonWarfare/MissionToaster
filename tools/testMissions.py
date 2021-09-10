import sys
import os
from datetime import datetime
import json
import subprocess
import concurrent.futures
import timeit
import logging


bwmf_min_date = datetime(2015, 1, 1)

# file paths
path_project = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
path_sqfvm_exe = os.path.join(path_project, "bin", "sqfvm.exe")
path_cfgconvert_exe = os.path.join(path_project, "bin", "CfgConvert.exe")
path_extract_data_sqf = os.path.join(path_project, "tools", "extractMissionData.sqf")
# config path
path_config_data_current_json = os.path.join(path_project, "configs", "current.json")
config_data_current = None
path_config_data_staging_json = os.path.join(path_project, "configs", "staging.json")
config_data_staging = None


def init_data():
    # Check tools exist
    if (not os.path.isfile(path_sqfvm_exe)): raise Exception(f"Missing {path_sqfvm_exe}")
    if (not os.path.isfile(path_cfgconvert_exe)): raise Exception(f"Missing {path_cfgconvert_exe}")
    if (not os.path.isfile(path_extract_data_sqf)): raise Exception(f"Missing {path_extract_data_sqf}")
    # Load current (and optional staging) configs
    global config_data_current
    global config_data_staging
    if (os.path.isfile(path_config_data_current_json)):
        config_data_current = json.load(open(path_config_data_current_json))
    else:
        raise Exception(f"Missing current config: {path_config_data_current_json}")
    if (os.path.isfile(path_config_data_staging_json)):
        config_data_staging = json.load(open(path_config_data_staging_json))
    else:
        logging.warning(f"Missing staging config: {path_config_data_staging_json}")


def test_mission_get_mission_version(path_mission_sqm):
    raw_version = ""
    try:
        mission_sqm = open(path_mission_sqm, "r")
        for line in mission_sqm:
            if (line.startswith("version=") or line.startswith("version =")):
                raw_version = line
                break
    except Exception: pass
    finally: mission_sqm.close()
    return raw_version


def test_mission_prepare_files(mission_path):
    test_logs = []
    path_mission_sqm = os.path.join(mission_path, "mission.sqm")
    path_description_ext = os.path.join(mission_path, "description.ext")
    path_cleanup_bat = os.path.join(mission_path, "cleanup.bat")
    path_mission_txt = os.path.join(mission_path, "mission.sqm.txt")
    path_description_bin = os.path.join(mission_path, "description.ext.bin")
    path_description_txt = os.path.join(mission_path, "description.ext.txt")

    # Check if mission.sqm is binerized
    version = test_mission_get_mission_version(path_mission_sqm)
    if (version != ""): test_logs.append(f"Mission not binerized")

    # Check if cleanup.bat ran
    if os.path.isfile(path_cleanup_bat): test_logs.append(f"cleanup.bat not ran")

    cmd_cfgconvert = [path_cfgconvert_exe, "-txt", "-dst", path_mission_txt, path_mission_sqm]
    result = subprocess.run(cmd_cfgconvert, capture_output=True, text=True, timeout=6)
    logging.debug(f"converting mission.sqm {result.returncode}")
    # Convert description.ext to bin and then back to txt (fixes some pedantic macros)
    cmd_cfgconvert = [path_cfgconvert_exe, "-bin", "-dst", path_description_bin, path_description_ext]
    subprocess.run(cmd_cfgconvert, capture_output=True, text=True, timeout=6)
    cmd_cfgconvert = [path_cfgconvert_exe, "-txt", "-dst", path_description_txt, path_description_bin]
    subprocess.run(cmd_cfgconvert, capture_output=True, text=True, timeout=6)

    return test_logs


def test_mission_run_SQFVM(mission_path):
    # Create test adapter (#include's the mission.sqm and description.ext)
    # SQFVM doesn't like base level config entries, so we have to wrap in a dummy class
    #  https://github.com/SQFvm/runtime/issues/160
    path_test_adapter = os.path.join(mission_path, "test_adapter.hpp")
    if (os.path.isfile(path_test_adapter)):
        logging.warning(f"Cleaning up old adapter: {path_test_adapter}")
        os.remove(path_test_adapter)
    f = open(path_test_adapter, "x")
    f.write('class X_configEXT {\n  #include "description.ext.txt" \n};\n class X_configSQM {\n  #include "mission.sqm.txt"\n};')
    f.close()

    # Run SQFVM
    cmd_sqfvm = [path_sqfvm_exe, "--automated"]
    cmd_sqfvm.extend(["--input-config", path_test_adapter])
    cmd_sqfvm.extend(['--input-sqf', path_extract_data_sqf])

    logging.debug(f"SQFVM called with: {cmd_sqfvm}")
    result = subprocess.run(cmd_sqfvm, capture_output=True, text=True, timeout=120)
    logging.info(f"SQFVM returned: {result.returncode}")
    os.remove(path_test_adapter)  # cleanup adapter
    if(result.returncode != 0): logging.error(f"SQFVM error: {result.returncode}")

    # Parse output
    sqf_test_started = False
    test_payload = ""
    for line in result.stdout.splitlines():
        # print(f"~~~~{line}")
        if not sqf_test_started:
            if (line == "Executing..."):
                logging.info("Starting Tests")
                sqf_test_started = True
            elif (line.startswith("[ERR]")):
                raise Exception(f"[SQFVM Mission Parse Error] {line}")
            elif (line.startswith("[WRN]")):
                logging.warning(f"SQFVM: {line}")
            else:
                logging.info(f"SQFVM: {line}")
        else:
            if ("[HINT]" in line):
                test_payload = line.split("[HINT] ")[1]
                logging.info("SQFVM: payload from extractData.sqf")
            elif (line.startswith("[ERR]")):
                raise Exception(f"[SQFVM Mission Test Error] {line}")
            elif (line.startswith("[INF]")):
                logging.info(f"SQFVM: {line}")
            # else:
            #     logging.debug(f"SQFVM: {line}") # lot of warning noise with everything shown

    if (test_payload == ""): raise Exception("[No payload in SQFVM output]")
    return test_payload


def test_mission_payload_get_info(payload):
    info = json.loads(payload)
    mission_author = info["author"]
    mission_objectCount = info["objectCount"]
    mission_onLoadName = info["onLoadName"]
    logging.debug(f"[Author: {mission_author}] [Objects: {mission_objectCount}] [{mission_onLoadName}]")
    return (mission_author, mission_objectCount, mission_onLoadName)


def test_mission_get_folder_size(mission_path):
    # Get the folder's size - ToDo: size should be binned sqm, could do cfgConvert on sqm?
    size = 0
    for f in os.scandir(mission_path):
        if (not (f.name.endswith(".sqm.txt") or f.name.endswith(".ext.txt") or f.name.endswith(".ext.bin"))):
            size += os.path.getsize(f)
    for f in os.scandir(os.path.join(mission_path, "loadouts")): size += os.path.getsize(f)
    return (size / 1024)


def test_mission_run_checks(config, mission_world, test_payload):
    missionError = False
    missionWarning = False
    missionLogs = []

    CfgWeapons = config["CfgWeapons"]
    CfgMagazines = config["CfgMagazines"]
    CfgVehicles = config["CfgVehicles"]
    CfgPatches = config["CfgPatches"]
    CfgWorlds = config["CfgWorlds"]

    # Make sure map Exists
    if (not (mission_world) in CfgWorlds):
        missionError = True
        missionLogs.append(f"[Missing Map] {mission_world}")

    # get results from payload
    info = json.loads(test_payload)
    mission_bwmfDate = info["bwmfDate"]
    mission_addons = info["addons"]
    mission_entities = info["entities"]
    mission_loadouts = info["loadouts"]

    # mission_weapons = info["weapons"]
    # mission_items = info["items"]
    # mission_attachments = info["attachments"]
    # mission_magazines = info["magazines"]
    # mission_backpacks = info["backpacks"]
    logging.debug(f"mission_bwmfDate: {mission_bwmfDate}")
    logging.debug(f"mission [addons {len(mission_addons)}] [entities: {len(mission_entities)}] [loadouts: {len(mission_loadouts)}]")

    # Check BWMF date
    if (mission_bwmfDate == ""): raise Exception("[BWMF version unknown]")
    if (mission_bwmfDate.startswith("2020/20")): mission_bwmfDate = "2020/12/20"  # WTF
    if (datetime.strptime(mission_bwmfDate, "%Y/%m/%d") < bwmf_min_date):
        missionError = True
        missionLogs.append(f"[BWMF version unsupported] {mission_bwmfDate} < {bwmf_min_date}")

    for addon in mission_addons:
        if (not addon in CfgPatches):
            missionError = True
            missionLogs.append(f"[Missing addon] {addon}")
    for entity in mission_entities:
        if (not entity in CfgVehicles):
            missionError = True
            missionLogs.append(f"[Missing entity] {entity}")
    # Check all loadouts are valid
    for loadoutname, loadout in mission_loadouts.items():
        for weapon in loadout["weapons"]:
            if (not weapon in CfgWeapons):
                missionError = True
                missionLogs.append(f"[Missing weapon] {loadoutname}: {weapon}")
            else:
                compatibleMags = CfgWeapons[weapon]["compatibleMagazines"]
                # check we have at least 1 compatible mag (ignore 0/1 mag weapons, probably single use launcher)
                if (len(compatibleMags) > 2) and (len(set(loadout["magazines"]).intersection(set(compatibleMags))) == 0):
                    if (not loadoutname.endswith("spotter")):
                        missionLogs.append(f"[No compatible mags] {loadoutname}: {weapon}")
                        missionError = True  # spotter weapon can be ignored in most cases
                    else:
                        missionLogs.append(f"[No compatible mags] {loadoutname}: {weapon} [ignored]")
        for item in loadout["items"]:
            if (not (item in CfgMagazines or item in CfgWeapons)):
                missionError = True
                missionLogs.append(f"[Missing item] {loadoutname}: {item}")
        for attachment in loadout["attachments"]:
            if (not attachment in CfgWeapons):
                missionWarning = True
                missionLogs.append(f"[Missing attachment] {loadoutname}: {attachment}")
        for magazine in loadout["magazines"]:
            if (not (magazine in CfgMagazines or magazine in CfgWeapons)):
                missionError = True
                missionLogs.append(f"[Missing magazine] {loadoutname}: {magazine}")
        for backpack in loadout["backpacks"]:
            if (not backpack in CfgVehicles):
                missionError = True
                missionLogs.append(f"[Missing backpack] {loadoutname}: {backpack}")

    icon = ":green_circle:"
    if (missionError):
        icon = ":red_circle:"
    elif (missionWarning):
        icon = ":yellow_circle:"

    return icon, missionLogs


def test_mission(mission_path):
    folder_name = os.path.basename(mission_path)
    logging.info(f"Checking {folder_name} from {mission_path}")

    results_log = []
    icon_current = ":purple_circle:"
    icon_staging = "" if (config_data_staging is None) else ":brown_circle:"

    mission_size = 0  # may not be availble if error happens in parsing
    mission_world_description = "?"  # may not be availble if error happens in parsing
    mission_author = "?"  # may not be availble if error happens in parsing
    mission_objectCount = "-"  # may not be availble if error happens in parsing
    mission_onLoadName = "?"  # may not be availble if error happens in parsing

    try:
        # Get Mission.Map name
        folder_split = folder_name.split(".")
        if (len(folder_split) != 2): raise Exception(f"[bad folder naming???] {folder_name}")
        mission_world = (folder_split[1]).lower()
        if ((mission_world) in config_data_current["CfgWorlds"]):
            mission_world_description = config_data_current["CfgWorlds"][mission_world]["description"]
        # Get Folder Size
        mission_size = test_mission_get_folder_size(mission_path)
        # Debin Mission.sqm
        test_logs = test_mission_prepare_files(mission_path)
        results_log.extend([f"  {line}" for line in test_logs])
        # Run SQFVM
        test_payload = test_mission_run_SQFVM(mission_path)
        # Get info from SQFVM output
        mission_author, mission_objectCount, mission_onLoadName = test_mission_payload_get_info(test_payload)

        # tests on current config
        icon_current, test_logs = test_mission_run_checks(config_data_current, mission_world, test_payload)
        results_log.extend([f"  {line}" for line in test_logs])

        # try tests on staging config if it exists
        if (config_data_staging is not None):
            icon_staging, test_logs = test_mission_run_checks(config_data_staging, mission_world, test_payload)
            results_log.extend([f"  {line} [STAGING]" for line in test_logs])

    except Exception as e:
        logging.error(f"{folder_name} threw {e}")
        results_log.append(f"  threw {e}!")
        icon_current = ":brown_circle:"
    else:
        logging.info(f"Mission [{folder_name}] Finished Tests")

    if (len(results_log) > 0): results_log.insert(0, f"{folder_name}:")

    formated_line = f"| {folder_name} | {mission_world_description} | {mission_author} | {mission_objectCount} | {mission_size:1.0f}kB | {icon_current} |"
    if (icon_staging != ""): formated_line += f" {icon_staging} |"

    # logging.debug(formated_line)
    if (len(results_log) > 10):
        note = f"+ {5-len(results_log)} more"
        results_log = results_log[:10]
        results_log.append(note)
    return results_log, formated_line


def main():
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
    time_start = timeit.default_timer()

    # load pseudo configs
    init_data()

    # Get all folders inside /missions
    mission_folders = [f.path for f in os.scandir(os.path.join(path_project, "missions")) if f.is_dir()]
    # mission_folders = [mission_folders[0]]  # debug - just do first one
    logging.info(f"Checking {len(mission_folders)} mission folder")

    body_table = ["Test results", ""]
    body_details = ["", "", "```"]

    if (config_data_staging is None):
        body_table.append("| Mission | World | Author | Objects | Size | Result |")
        body_table.append("|------------|------|------|------|------|------------|")
    else:
        body_table.append("| Mission | World | Author | Objects | Size | Result | Result-Staging |")
        body_table.append("|------------|------|------|------|------|------------|------------|")

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for error_output, formated_line in executor.map(test_mission, mission_folders):
            body_table.append(formated_line)
            body_details.extend(error_output)

    time_end = timeit.default_timer()
    body_details.extend(
        ["", f"Tested {len(mission_folders)} missions in {(time_end - time_start):.1f}s @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "```"])
    issue_body = os.linesep.join(body_table + body_details)
    logging.info(f"issue_body = \n {issue_body}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
