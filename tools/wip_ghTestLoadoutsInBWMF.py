import os
import sys
import shutil
import traceback
import subprocess as sp
from github import Github


LOADOUT_ISSUE = 1
REPOUSER = "BourbonWarfare"
REPONAME = "MissionToaster"
REPOPATH = f"{REPOUSER}/{REPONAME}"


def check_bwmf_loadouts(repo):
    diag = sp.check_output(["python3", "tools/testMissions.py"])
    diag = str(diag, "utf-8")
    issue = repo.get_issue(LOADOUT_ISSUE)
    issue.edit(body=diag)


def main():
    print("Obtaining token ...")
    try:
        token = os.environ["GH_TOKEN"]
        repo = Github(token).get_repo(REPOPATH)
    except:
        print("Could not obtain token.")
        print(traceback.format_exc())
        return 1
    else:
        print("Token sucessfully obtained.")

    print("\nUpdating translation issue ...")
    try:
        check_bwmf_loadouts(repo)
    except:
        print("Failed to update translation issue.")
        print(traceback.format_exc())
        return 1
    else:
        print("Translation issue successfully updated.")


if __name__ == "__main__":
    sys.exit(main())
