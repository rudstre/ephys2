import os
import yaml
import time

EPHYS_FOLDERS = [
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_16_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_18_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_19_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_20_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_22_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_23_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_24_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_25_1/ephys",
    "/n/home02/daldarondo/LabDir/Everyone/dannce_rig/dannce_ephys/duke/2022_02_26_1/ephys",
]
BASE_CONFIG_PATH = "/n/holylfs02/LABS/olveczky_lab/Diego/code/ephys2/base_config.yaml"


def load_config(config_path: str) -> list:
    """Load ephys2 config

    Args:
        config_path (str): Path to ephys2 config.yaml

    Returns:
        list: List of stages in ephys2 config
    """
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def modify_config(base_config_path: str, modifiers: list):
    """Modify specific values in a base config.

    Args:
        base_config_path (str): Path to base config
        modifiers (list): List of dictionaries containing desired ephys2 stages and parameters
            Example: modifiers = [{"snippet.fast_threshold":{"detect_threshold": 20}}]
    """
    config = load_config(base_config_path)
    for mod in modifiers:
        mod_stage_name = list(mod.keys())[0]
        params = mod[mod_stage_name]
        for stage in config:
            if isinstance(stage, dict):
                if mod_stage_name in list(stage.keys()):
                    for param, val in params.items():
                        stage[mod_stage_name][param] = val
    return config


def modify_config_paths(base_config_path: str, ephys_path: str):
    """Clone a base ephys2 config to operate on a single session.

    Args:
        base_config_path (str): Path to the base config.yaml
        ephys_path (str): Path to folder containing ephys data (.RHD files)
    """
    config = load_config(base_config_path)

    # Handle the input parameters
    for stage in config:
        if isinstance(stage, dict):
            if "input.rhd2000" in list(stage.keys()):
                stage["input.rhd2000"]["files"] = os.path.join(
                    ephys_path, os.path.basename(stage["input.rhd2000"]["files"])
                )
            if "checkpoint" in list(stage.keys()):
                stage["checkpoint"]["file"] = os.path.join(
                    ephys_path, os.path.basename(stage["checkpoint"]["file"])
                )
    return config


def launch_e2(base_config_path: str, ephys_path: str, job_name: str):
    """Launch an e2 sorting job using the base config on data in ephys path.

    Args:
        base_config_path (str): Path to the base config.yaml
        ephys_path (str): Path to folder containing ephys data (.RHD files)
    """
    config = modify_config_paths(base_config_path, ephys_path)
    config_path = os.path.join(ephys_path, "ephys2_config.yaml")
    with open(config_path, "w") as file:
        yaml.dump(config, file)
    cmd = (
        "CFG=%s sbatch -J %s --partition olveczky,shared,serial_requeue --ntasks-per-node 32 --mem 112000 --time 0-08:00 -o $EPHYS2_JOBS/%s.out -e $EPHYS2_JOBS/%s.err $EPHYS2_PATH/slurm/launch.sh"
        % (config_path, job_name, job_name, job_name)
    )
    print(cmd)
    os.system(cmd)


if __name__ == "__main__":
    for folder in EPHYS_FOLDERS:
        job_name = folder.split("/")[-2]
        launch_e2(BASE_CONFIG_PATH, folder, job_name)
        time.sleep(2)
