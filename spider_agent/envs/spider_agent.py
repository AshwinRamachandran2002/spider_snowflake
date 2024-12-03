import logging
import os
import subprocess
import tempfile
import time
from typing import Callable, Any, Optional, Tuple

from typing import List, Dict, Union
from docker.models.containers import Container
from docker.client import DockerClient
from docker.errors import ImageNotFound
import gymnasium as gym
import shutil, pathlib, docker, time, copy
from spider_agent.controllers.python import PythonController
from spider_agent.controllers.setup import SetupController
from spider_agent.envs.utils import *
from spider_agent import configs
from spider_agent.agent.action import Action, Terminate, SNOWFLAKE_EXEC_SQL, SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON, SNOWFLAKE_READ_SCHEMA_FROM_DDL, SNOWFLAKE_JUSTIFY_DDL_RELEVANCE, SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE, SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE, PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS, SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK, SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN
from spider_agent.agent.prompts import EXEC_SQL_SEMI_STRUCTURED
import signal

logger = logging.getLogger("spider_agent.env")

Metric = Callable[[Any, Any], float]
Getter = Callable[[gym.Env, Dict[str, Any]], Any]


# constants
START_UP_DELAY = 2 # start up delay for docker container
DEFAULT_TIME_OUT = 200 # default waiting time for each action
MAX_OBS_LENGTH = 40000
EMPTY_DATA_PATH = 'spider_agent/data/empty' # an empty data directory
DEFAULT_IMAGE_DIR = 'spider_agent/images' # default directory to store docker images
DEFAULT_WORK_DIR = '/workspace' # default working directory in the container
DEFAULT_MNT_DIR = 'spider_agent/mnt' # default directory to copy and mount data path, also the output directory
TASK_FINISHED = "task_finished" # infos key
ACTION_EXEC = "action_executed" # infos key


class Spider_Agent_Env(gym.Env):
    """
    DesktopEnv with OpenAI Gym interface.
    Fixme: refactor the logic when implementing the multi-process version
    """
    def __init__(self, env_config, task_config, cache_dir, mnt_dir):
        """
        Args:
            path_to_vm (str): path to .vmx file
            action_space (str): "computer_13" | "pyautogui"

            task_config (Dict[str, Any]): manages task configs integratedly,
              including
              * base snapshot
              * task id (uuid)
              * instruction
              * setup config

            tmp_dir (str): temporary directory to store trajectory stuffs like
              the extracted screenshots
            cache_dir (str): cache directory to cache task-related stuffs like
              reference file for evaluation
        """
        super().__init__()
        self.task_config = task_config
        self.cache_dir_base = cache_dir
        self.container_name = env_config['init_args']['name']
        self.image_name = env_config['image_name']
        self.mnt_dir = mnt_dir
        self.work_dir = DEFAULT_WORK_DIR
        self.kwargs = env_config['init_args']

        self._set_task_info(task_config)
        logger.info("Initializing...")
        # self._construct_container()
        
        self.controller = PythonController(container=task_config["instance_id"], work_dir=self.work_dir)
        self.setup_controller = SetupController(container=task_config["instance_id"], cache_dir=self.cache_dir)
        
        logger.info("Setting up environment...")
        
        self.setup_controller.setup(self.config)
        self.init_files_hash = self._get_env_files_hash()
        time.sleep(2)
        logger.info("Environment setup complete.")
        
        
        
    def _set_task_info(self, task_config: Dict[str, Any]):
        self.task_id: str = task_config['instance_id']
        self.cache_dir: str = os.path.join(self.cache_dir_base, self.task_id)
        # os.makedirs(self.cache_dir, exist_ok=True)
        self.instruction = task_config["instruction"]

        self.config = task_config["config"] if "config" in task_config else []
        self.post_process_func = task_config["post_process"] if "post_process" in task_config else []
        
    def close(self):
        self.container.stop()
        self.container.remove()
        logger.info(f"Container {self.container_name} stopped and removed.")
        
    def _construct_container(self):
        
        client = docker.from_env()
        container_name = self.container_name
        #### delete existing container
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
            print(f"Container {container_name} stopped and removed.")
        except docker.errors.NotFound:
            pass
        except docker.errors.APIError as e:
            pass
        
        create_folder_if_not_exists(self.mnt_dir)
        src_dir = pathlib.Path(self.mnt_dir).absolute().__str__()
        delete_files_in_folder(self.mnt_dir)

        volumes = {src_dir: {'bind': self.work_dir, 'mode': 'rw'}}
        allowed_params = ['command', 'ports', 'restart_policy', 'entrypoint', 'hostname', 'domainname', 'name', 'user', 'mac_address', 'platform', 'network_mode', 'network_disabled', 'healthcheck', "environment"]
        kwargs = {k: self.kwargs[k] for k in self.kwargs if k in allowed_params}
        extra_params = {'detach': True, 'tty': True, 'stdout': True, 'stderr': True, 'stdin_open': True, **kwargs}

        try:
            client: DockerClient = docker.from_env()
            image = client.images.get(self.image_name)
            self.container: Container = client.containers.run(image=image, volumes=volumes, **extra_params)
        except ImageNotFound as e:
            dockerfile_path = os.path.join(DEFAULT_IMAGE_DIR, self.image_name)
            if os.path.exists(dockerfile_path):
                logger.info(f"Image {self.image_name} not found, try to build from dockerfile {dockerfile_path} ...")
                image = client.images.build(path=dockerfile_path, tag=self.image_name, rm=True)[0]
            else:
                logger.info(f"Image {self.image_name} not found, try to pull from Dockerhub ...")
                image = client.images.pull(self.image_name)[0]
            self.container: Container = client.containers.run(image=image, volumes=volumes, **extra_params)
        except Exception as e:
            logger.info(f"Failed to construct container from image {self.image_name} with error: {e}")
            raise e

        time.sleep(START_UP_DELAY)
        logger.info(f"Connected to container[name={self.container.name}, id={self.container.id}] from image {self.image_name} ...")    
        
        return self.container

    def _get_env_files_hash(self) -> Dict[str, str]:
        """
        Returns:
            Dict[str, str]: a dictionary of the hash of the files in the
              environment
        """
        files_hash = {}
        for root, dirs, files in os.walk(self.mnt_dir):
            for f in files:
                file_path = os.path.join(root, f)
                files_hash[file_path] = calculate_sha256(file_path)
        return files_hash
    

    def post_process(self):
        """
        Evaluate whether the task is successfully completed.
        """
        diff_files = self._find_diff_files_init(self.init_files_hash)

        post_process_files = []
        errors = []
        for post_process_f in self.post_process_func:
            process_function = getattr(configs, post_process_f, None)
            post_files, error = process_function(self.mnt_dir, self.controller)
            post_files = post_files if isinstance(post_files, list) else list(post_files)
            post_process_files.extend(post_files)
            errors.append(error)

        return {**diff_files, "post_process_files": post_process_files, "error": errors}

    def _find_diff_files_init(self, init_file_dict)-> Dict:
        init_file_paths = init_file_dict.keys()
        added_files_list = []
        changed_files_list = []
        for root, dirs, files in os.walk(self.mnt_dir):
            for f in files:
                file_path = os.path.join(root, f)
                if file_path not in init_file_paths:
                    added_files_list.append(file_path)
                else:
                    if init_file_dict[file_path] != calculate_sha256(file_path):
                        changed_files_list.append(file_path)
        return {"added_files": added_files_list, "changed_files": changed_files_list}

    def get_directory_tree(self):

        output = self.controller.get_directory_tree()
        output_contents = output.split("<DELIMITER>")
        tree_structure = output_contents[0]

        md_files_list = output_contents[1].split("\n")
        self.md_files = []
        for md_file in md_files_list:
            if md_file:
                self.md_files.append(md_file)
        self.md_files_content = ""
        for md_file in self.md_files:
            md_file = self.controller.get_real_file_path(md_file)
            content = open(md_file, "r").read()
            self.md_files_content += f"\n\n{md_file}:\n{content}\n\n"

        self.json_files = output_contents[2].split("\n")
        
        self.ddl_files = []
        for ddl_file in output_contents[3].split("\n"):
            if ddl_file:                
                self.ddl_files.append(ddl_file)

        self.registered_json = {}
        self.inspected_tables = {}
        self.inspected_clauses = []
        self.distinct_columns = []

        self.not_reminded = True
        self.not_reminded_clause = True
        
        self.clause_check_done = True
        
        self.action_counter = {}
        self.retries = 0
        
        self.last_sql = ""
        
        return tree_structure


    # Assumptions: All markdown files are relevant and are to be read
    # Instruction hierarchy of initial actions set using prompts

    def step(self, action: Action):
        try:
            with timeout(DEFAULT_TIME_OUT,"Action execution time exceeded!"):
                done = False
                refresh = "Nothing"
                
                
                def represent_registered_info():
                    observation = "\n\nFollowing is list of tables and columns present.\n"
                    observation = "\n\nThe tables and columns provided are probably all relevant to the fina SQL query.\n"
                    observation += "\n\nFor each column, the type and description is given.\n"
                    observation += "\n\nCarefully look at the sample values given to each column. Use this information when writing conditional clauses.\n"
                    observation += "\n\nImportant: The sample value can provide information about the structure of the data, for example if it is a list or dictonary. It can also provide information about the what values are in the column.\n"
                    for table_name in self.registered_json:
                        observation += "-"*50
                        observation += "\n\n\nTable: " + table_name + "\n"
                        for row in self.registered_json[table_name]:
                            observation += '\nThe column, "' + row["column_name"]
                            observation += '" of type, ' + row["type"]
                            if row["description"]:
                                observation += " with description, " + row["description"]
                            # observation += " is relevant because " + row["reason"] + "\n"
                            observation += "\n"
                            if row["sample_values"] != []:
                                observation += "Sample values drawn from the column: " + "\n--> " + str(row["sample_values"]) + "\n"
                            if "distinct_values" in row:
                                observation += "The column has the following values: " + str(row["distinct_values"]) + "\n"
                    return observation + "-"*50 + "\n\n\n"

                def read_json_prompt():
                    json_file_path = self.json_files[0]
                    self.json_files.remove(json_file_path)

                    json_content = self.controller.execute_sf_inspect_table_json(json_file_path)

                    if json_content["table_fullname"] not in self.inspected_tables:
                        self.inspected_tables[json_content["table_fullname"]] = {}
                    for column in json_content:
                        self.inspected_tables[json_content["table_fullname"]][column] = json_content[column]

                    observation = ""#represent_registered_info()
                    observation += "\n\nFollowing is the " + json_file_path + " content:\n\n"
                    observation += json.dumps(json_content) + "\n\nNow, justify the relevance for all columns for the table: " + json_file_path + "using SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE\n\n"
                    observation += "\nThe justification must be why or why not it is relevant for the current task: " + self.instruction + "\n\n"
                    observation += "\nTake care to include columns that may be foreign keys for JOIN operations with other relevant tables.\n\n"
                    observation += "\nFunction Signature: \n" + SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE.get_action_description() + "\n"
                    observation += "\n\nTask is: " + self.instruction + "\n\n"

                    return observation


                def exec_sql_prompt():
                    observation = "\nNow, you can generate the SQL query using SNOWFLAKE_EXEC_SQL\n\n"
                    observation += "\nFunction Signature: \n" + SNOWFLAKE_EXEC_SQL.get_action_description() + "\n"
                    observation += "\nYou can terminate using: \n" + Terminate.get_action_description() + "\n"
                    observation += represent_registered_info()
                    observation = EXEC_SQL_SEMI_STRUCTURED + observation
                    observation = "\n\nExternal Information:\n" + self.md_files_content + "\n\n" + observation
                    observation += "\n\nTask is: " + self.instruction + "\n\n"
                    return observation


                def ddl_file_prompt():
                    observation = "\n\nFollowing is the DDL file\n\n"
                    observation += self.controller.execute_sf_inspect_ddl(self.ddl_files[0]) + "\n\n"
                    observation += "\n\nWhat tables do you think are relevant to the task?\n\n"
                    observation += "\n\nUsing SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE write down all JSON files, description of the JSON files and why it is or is not relevant for the task.\n\n"
                    observation += "\nThe justification must be why it is or why it is not relevant for the current task: " + self.instruction + "\n\n"
                    observation += "\nFunction Signature: \n" + SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE.get_action_description() + "\n"
                    observation += "\n\nTable JSON files are: " + ", ".join(self.json_files) + "\n\n"
                    observation += "\n\nJustificaion must be made for all JSON files\n\n"
                    observation += "\n\nTask is: " + self.instruction + "\n\n"
                    return observation

                if isinstance(action, PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS):
                    observation = self.controller.execute_PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(action)
                    self.predicted_obs = observation

                    if len(self.md_files):
                        observation += "\n\nFollowing is the content of the markdown files:\n" + self.md_files_content + "\n\n"
                        observation += "\n\nWhat information do you think is relevant to the task?\n\n"

                    if len(self.ddl_files) == 1:
                        observation += ddl_file_prompt()
                    else:
                        table_per_ddl = self.controller.execute_sf_info_ddl(self.ddl_files)
                        observation += "\n\nDDL files are: \n"
                        for ddl in table_per_ddl:
                            observation += ddl + "\n"
                            observation += "Tables in the DDL file are: " + ", ".join(table_per_ddl[ddl]) + "\n\n"
                        observation += "\n\nWhat DDL files do you think are relevant to the task?\n\n"
                        observation += "\n\nUsing SNOWFLAKE_JUSTIFY_DDL_RELEVANCE write down all DDL files, description of the DDL files and why it is or is not relevant for the task.\n\n"
                        observation += "\nThe justification must be why it is or why it is not relevant for the current task: " + self.instruction + "\n\n"
                        observation += "\nFunction Signature: \n" + SNOWFLAKE_JUSTIFY_DDL_RELEVANCE.get_action_description() + "\n"
                        observation += "\n\nJustification must be made for all DDL files\n\n"
                        observation += "\n\nTask is: " + self.instruction + "\n\n"


                elif isinstance(action, SNOWFLAKE_JUSTIFY_DDL_RELEVANCE):
                    ddl_desc = action.ddl_reason
                    self.ddl_files = []
                    for desc in ddl_desc:
                        if desc["is_relevant"]:
                            self.ddl_files.append(desc["ddl_path"])
                    observation = ddl_file_prompt()

                elif isinstance(action, SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE):
                    json_desc = action.json_reason
                    self.json_files = []
                    for desc in json_desc:
                        self.json_files.append(desc["json_path"])
                        
                    observation = read_json_prompt()


                elif isinstance(action, SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE):
                    relevance = action.column_justify
                    table_name = action.table_name
                    
                    if table_name not in self.registered_json:
                        self.registered_json[table_name] = []

                    for column_reason in relevance:
                        column = column_reason["column_name"]
                        reason = column_reason["reason"]
                        type_ = self.inspected_tables[table_name][column]["type"]
                        if type_ == "TEXT" or type_ == "VARIANT":
                            distinct_values = self.controller.execute_sf_exec_sql_query_special3(column, table_name)
                            if type_ == "TEXT":
                                if len(distinct_values[0]) > 100:
                                    distinct_values = [distinct_values[0][:100] + "..."]
                            if len(distinct_values) == 20:
                                distinct_values = distinct_values[:5]
                            distinct_values = "\n--> " + "\n--> ".join(distinct_values)
                            self.registered_json[table_name].append(
                                {
                                    "column_name": column,
                                    "reason": reason,
                                    "type": type_,
                                    "sample_values": [],
                                    "description": self.inspected_tables[table_name][column]["description"],
                                    "distinct_values": distinct_values
                                }
                            )
                        else:
                            self.registered_json[table_name].append(
                                {
                                    "column_name": column,
                                    "reason": reason,
                                    "type": type_,
                                    "sample_values": self.inspected_tables[table_name][column]["sample_values"] if "sample_values" in self.inspected_tables[table_name][column] else [],
                                    "description": self.inspected_tables[table_name][column]["description"]
                                }
                            )

                    if len(self.json_files):
                        observation = read_json_prompt()
                        refresh = "Go back to JSON justification"
                    elif len(self.ddl_files) > 1:
                        self.ddl_files = self.ddl_files[1:]
                        observation = ddl_file_prompt()
                        refresh = "Go back to DDL justification"
                    else:
                        observation = exec_sql_prompt()
                        refresh = "Go back to System Message"


                elif isinstance(action, SNOWFLAKE_EXEC_SQL):
                    self.retries += 1
                    # if self.retries > 3:
                    #     done = True
                    # if self.last_sql == action.sql_query:
                    #     done = True

                    self.last_sql = action.sql_query
                    observation = self.controller.execute_sf_exec_sql_query(action)
                    observation = "Output of the SQL execution:\n\n```\n" + observation + "\n```\n\n"

                    if "Error" in observation or observation == "" or "No data found" in observation:
                        # observation = EXEC_SQL_SEMI_STRUCTURED + observation
                        # observation += represent_registered_info()
                        observation += "\n\nThe SQL is erroneous. Check again."
                        observation += "\n\nTask is: " + self.instruction + "\n\n"

                    else:
                        # observation += represent_registered_info()
                        # observation += "\n\nCarefully go through the initial instruction and the prediction. Analyze if results satisfy the instruction.\n\nTask:\n" + self.instruction + "\n\nPrediction:\n" + self.predicted_obs + "\n\nFirst, break down the question noting every detail about the question. Then, verify every detail is satisfied. Are you sure about the number of rows? Isn't the question asking something else? Are you surethe conditional clauses are correct and in right place?\n\n"
                        observation += "\n\nCarefully go through the initial instruction. Analyze if results satisfy the instruction.\n\nTask:\n" + self.instruction + "\n\nFirst, break down the question noting every detail about the question. Then, verify every detail is satisfied.\n\n"
                        observation += "\n\nThe results must satisfy" + self.predicted_obs + "\n\n"
                        observation += "\n\nMake sure there are no repetitions among rows, there are no null values in columns\n\n"
                        observation += "If output is not as expected, try to understand why and try a different query. If the output is fully correct and as expected, only then terminate.\n\n"

                elif isinstance(action, Terminate):
                    observation = action.output
                    done = True
                else:
                    raise ValueError(f"Unrecognized action type {action.action_type} !")

        except TimeoutError as e:
            observation = str(e)

        observation = self._handle_observation(observation)
        # logger.info("Observation: %s", observation)
        return observation, done, refresh
    
    def _handle_observation(self, observation):
        max_length = MAX_OBS_LENGTH  
        if len(observation) > max_length:
            truncated_observation = observation[:max_length] + "\n[Observation too long, truncated; Try other commands to get the left part.]"
            raise ValueError("Observation too long, shutting down the environment.")
            return truncated_observation
        return observation
