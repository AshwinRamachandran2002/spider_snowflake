import argparse
import datetime
import json
import logging
import os
import random
import sys
import glob
import dotenv

dotenv.load_dotenv()

from tqdm import tqdm

from spider_agent.envs.spider_agent import Spider_Agent_Env
from spider_agent.agent.agents import PromptAgent


#  Logger Configs {{{ #
logger = logging.getLogger("spider_agent")
logger.setLevel(logging.DEBUG)

datetime_str: str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

file_handler = logging.FileHandler(os.path.join("logs", "normal-{:}.log".format(datetime_str)), encoding="utf-8")
debug_handler = logging.FileHandler(os.path.join("logs", "debug-{:}.log".format(datetime_str)), encoding="utf-8")
stdout_handler = logging.StreamHandler(sys.stdout)
sdebug_handler = logging.FileHandler(os.path.join("logs", "sdebug-{:}.log".format(datetime_str)), encoding="utf-8")

file_handler.setLevel(logging.INFO)
debug_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)
sdebug_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s")
file_handler.setFormatter(formatter)
debug_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
sdebug_handler.setFormatter(formatter)

stdout_handler.addFilter(logging.Filter("spider_agent"))
sdebug_handler.addFilter(logging.Filter("spider_agent"))

logger.addHandler(file_handler)
logger.addHandler(debug_handler)
logger.addHandler(stdout_handler)
logger.addHandler(sdebug_handler)
#  }}} Logger Configs # 



def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end evaluation on the benchmark"
    )

    parser.add_argument("--consistency", type=bool, default=False)
    
    parser.add_argument("--max_steps", type=int, default=20)
    
    parser.add_argument("--max_memory_length", type=int, default=30)
    parser.add_argument("--suffix", '-s', type=str, default="gpt-4-try1")
    
    parser.add_argument("--model", type=str, default="claudesswee")
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--max_tokens", type=int, default=2500)
    parser.add_argument("--stop_token", type=str, default=None)
    
    # example config
    parser.add_argument("--test_path","-t", type=str, default="./examples/spider2-snow.jsonl")
    parser.add_argument("--example_index", "-i", type=str, default="all", help="index range of the examples to run, e.g., '0-10', '2,3', 'all'")
    parser.add_argument("--example_name", "-n", type=str, default="", help="name of the example to run")
    parser.add_argument("--overwriting", action="store_true", default=False)
    parser.add_argument("--retry_failed", action="store_true", default=False)

    # output related
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--bq_only", action="store_true")
    parser.add_argument("--local_only", action="store_true")
    parser.add_argument("--dbt_only", action="store_true")
    parser.add_argument("--sf_only", action="store_true")
    
    
    args = parser.parse_args()

    return args



def test(
    args: argparse.Namespace,
    test_all_meta: dict = None
) -> None:
    scores = []
    
    # log args
    logger.info("Args: %s", args)

    if args.suffix == "":
        logger.warning("No suffix is provided, the experiment id will be the model name.")
        experiment_id = args.model.split("/")[-1]
    else:
        experiment_id = args.model.split("/")[-1] + "-" + args.suffix

    if args.plan:
        experiment_id = f"{experiment_id}-plan"

    env_config = \
    {
        "image_name": "spider_agent-image",
        "init_args": {
            "name": experiment_id,
            "work_dir": "/workspace",
        }
    }
    
    agent = PromptAgent(
        model=args.model,
        max_tokens=args.max_tokens,
        top_p=args.top_p,
        temperature=args.temperature,
        max_memory_length=args.max_memory_length,
        max_steps=args.max_steps,
        use_plan=args.plan,
        consistency=args.consistency
    )
    valid_ids = []
    ## load task configs
    assert os.path.exists(args.test_path) and args.test_path.endswith(".jsonl"), f"Invalid test_path, must be a valid jsonl file: {args.test_path}"
    with open(args.test_path, "r") as f:
        task_configs = [json.loads(line) for line in f]


    if args.example_name != "":
        task_configs = [task for task in task_configs if args.example_name in task["id"]]
    else:
        if args.example_index != "all":
            if "-" in args.example_index:
                start, end = map(int, args.example_index.split("-"))
                task_configs = task_configs[start:end]
            else:
                indices = list(map(int, args.example_index.split(",")))
                task_configs = [task_configs[i] for i in indices]

    instance_db = json.load(open("instance_db.json", "r"))
    for task_config in task_configs:
        try:
            instance_id = experiment_id +"/"+ task_config["instance_id"]

            # if task_config["instance_id"] not in ['sf_local031', 'sf_local035', 'sf_local034', 'sf_local028', 'sf_local030', 'sf_bq226', 'sf_bq091', 'sf_bq222', 'sf_bq210', 'sf_bq033', 'sf_bq223', 'sf_bq099', 'sf_bq221', 'sf_bq209', 'sf_bq213', 'sf_local039', 'sf_local038', 'sf_local022', 'sf_local259', 'sf_local026', 'sf_bq219', 'sf_bq253', 'sf_bq254', 'sf_bq017', 'sf_bq349', 'sf_bq041', 'sf_bq303', 'sf_bq308', 'sf_bq121', 'sf_bq309', 'sf_bq310', 'sf_bq280', 'sf_bq301', 'sf_bq300', 'sf_local269', 'sf_local274', 'sf_local273', 'sf_bq273', 'sf_bq265', 'sf_bq263', 'sf_bq264', 'sf_bq260', 'sf_bq271', 'sf_bq233', 'sf_bq194', 'sf_bq295', 'sf_bq377', 'sf_bq100', 'sf_bq252', 'sf_bq359', 'sf_bq193', 'sf_bq255', 'sf_bq248', 'sf_local063', 'sf_local067', 'sf_local360', 'sf_local329', 'sf_local075', 'sf_local285', 'sf_local300', 'sf_local299', 'sf_local157', 'sf_local064', 'sf_local156', 'sf_local099', 'sf_local019', 'sf_local141', 'sf_local132', 'sf_local131', 'sf_local003', 'sf_local002', 'sf_local004', 'sf_local336', 'sf_local355', 'sf_local354', 'sf_local309', 'sf_local311', 'sf_bq278', 'sf_local049', 'sf_local065', 'sf_local073', 'sf_local041', 'sf014', 'sf_local194', 'sf_local199', 'sf_local195', 'sf_local056', 'sf_bq286', 'sf_local263', 'sf_local081', 'sf_local209', 'sf_local210', 'sf_bq229', 'sf_bq104', 'sf_bq035', 'sf_bq216', 'sf_bq127', 'sf_local009', 'sf_local010', 'sf_local244', 'sf_local168', 'sf_local071', 'sf_local072', 'sf_local054', 'sf_bq130', 'sf_bq284', 'sf_bq412', 'sf_bq397', 'sf_bq012', 'sf_bq187', 'sf_local152', 'sf_bq442', 'sf_bq458', 'sf_local058', 'sf_local059', 'sf_bq028', 'sf011', 'sf_bq072']:
            #     continue
            # if task_config["instance_id"] not in ['sf_bq193', 'sf_bq223', 'sf_bq248', 'sf_bq028', 'sf_bq033', 'sf_bq091', 'sf_bq099']:
            #     continue
            # if task_config["instance_id"] not in [ "sf_bq035", "sf_bq255", "sf_bq130", "sf_bq213", "sf_bq280", "sf_bq286", "sf_bq301", "sf_bq359", "sf_local004", "sf_local019", "sf_local028", "sf_local031", "sf_local065", "sf_local199", "sf_local244"]:
            #     continue
            if task_config["instance_id"] not in ["sf_bq263", "sf_bq310", "sf_local049", "sf_local073", "sf_bq100", "sf_bq104", "sf_bq193", "sf_bq223", "sf_bq248", "sf_bq252", "sf_bq028", "sf_bq033", "sf_bq091", "sf_bq099", "sf_bq210", "sf_bq284", "sf_bq308", "sf_local009", "sf_local041", "sf_local054", "sf_local058", "sf_local059"]:             
                continue
            
            output_dir = os.path.join(args.output_dir, instance_id)
            result_json_path =os.path.join(output_dir, "spider/result.json")


            task_type = None
            if task_config["instance_id"].startswith("bq") or task_config["instance_id"].startswith("ga"):
                task_type = 'bq'
            elif task_config["instance_id"].startswith("local"):
                task_type = 'local'
            elif task_config["instance_id"].startswith("sf"):
                task_type = 'sf'
            else:
                task_type = 'dbt'

            valid_types = set()
            if args.local_only: valid_types.add('local')
            if args.bq_only: valid_types.add('bq')
            if args.sf_only: valid_types.add('sf')
            if args.dbt_only: valid_types.add('dbt')
            
            if  (args.local_only or args.bq_only or args.sf_only or args.dbt_only):
                if task_type not in valid_types: continue
            else:
                pass

            valid_ids.append(task_config["instance_id"])
            
            if not args.overwriting and os.path.exists(result_json_path):
                logger.info("Skipping %s", instance_id)
                continue
            elif os.path.exists(result_json_path):
                logger.info("Overwriting %s", instance_id)
            else:
                logger.info("Running %s", instance_id)
            if args.retry_failed and os.path.exists(result_json_path):
                with open(result_json_path, "r") as f:
                    result = json.load(f)
                    if result["finished"] and (not "FAIL" in result["result"]) and (not "error" in result["result"].lower()):
                        logger.info("Skipping %s", instance_id)
                        continue
                logger.info("Retrying %s", instance_id)

            if os.path.exists(output_dir):
                os.system(f"rm -rf {output_dir}")
                logger.info("Removed existing %s", output_dir)

            os.makedirs(output_dir, exist_ok=True)

            env_config["init_args"]["name"] = experiment_id +"-"+ task_config["instance_id"]

            
            source_data_dir = os.path.dirname(args.test_path)        
            task_config['config'] = [{"type": "copy_all_subfiles", "parameters": {"dirs": [os.path.join(source_data_dir, task_config["instance_id"])]}}]

            env = Spider_Agent_Env(
                env_config=env_config,
                task_config=task_config,
                cache_dir="./cache",
                mnt_dir=output_dir
            )
            agent.set_env_and_task(env)
        
            logger.info('Task input:' + task_config['instruction'])
            done, result_output, history_messages = agent.run()
            trajectory = agent.get_trajectory()

            os.makedirs(os.path.join(output_dir, "spider"), exist_ok=True)
            result_files = env.post_process()
            spider_result = {"finished": done, "steps": len(trajectory["trajectory"]),
                            "result": result_output,"result_files": result_files, **trajectory}
            with open(os.path.join(output_dir, "spider/result.json"), "w") as f:
                json.dump(spider_result, f, indent=2)
            
            with open(os.path.join(output_dir, "spider/history_messages.json"), "w") as f:
                json.dump(history_messages, f, indent=2)
            
            # Delete sqlite files
            if task_type == 'local':
                sqlite_files = glob.glob(os.path.join(output_dir, '*.sqlite')) + glob.glob(os.path.join(output_dir, '*.duckdb'))

                for file_path in sqlite_files:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
            
            
            logger.info("Finished %s", instance_id)
            # env.close()
        except Exception as e:
            logger.error("Error in %s: %s", task_config["instance_id"], e)
            # env.close()
            continue

if __name__ == '__main__':
    args = config()
    
    test(args)