import argparse
import datetime
import json
import logging
import os
import sys
import glob
import dotenv

dotenv.load_dotenv()

from spider_agent.envs.spider_agent import Spider_Agent_Env
from spider_agent.agent.agents import PromptAgent


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
    
    parser.add_argument("--max_steps", type=int, default=30)
    
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

    for task_config in task_configs:
        # try:
            instance_id = experiment_id +"/"+ task_config["instance_id"]
            
            not_ids = [
                "sf_bq130", "sf_ga004", "sf_local131", "sf044", "sf_bq109", "sf_bq398", "sf_bq442", 
                "sf_bq279", "sf_local132", "sf001", "sf_bq085", "sf_local058", "sf_bq213", "sf_local099", 
                "sf_local065", "sf_bq285", "sf_bq399", "sf_local075", "sf_bq362", "sf_bq295", "sf_bq115", 
                "sf_local329", "sf_local028", "sf_bq328", "sf_bq121", "sf_bq076", "sf_bq300", "sf_local039", 
                "sf_bq350", "sf_bq025", "sf_bq355", "sf_local072", "sf_bq198", "sf_ga017", "sf_bq034", 
                "sf_bq077", "sf_bq161", "sf_local274", "sf_bq341", "sf_local309", "sf_bq033", "sf_bq091", 
                "sf_bq280", "sf_bq126", "sf_local041", "sf_bq286", "sf_local004", "sf_local022", "sf_local141", 
                "sf_ga001", "sf_bq284", "sf_bq396", "sf_bq010", "sf_bq112", "sf_bq359", "sf_local218", 
                "sf_bq035", "sf_local054", "sf_local210", "sf_bq392", "sf_local071", "sf_bq224", "sf_bq081", 
                "sf_bq310", "sf_bq159", "sf_bq255", "sf_bq060", "sf_bq282", "sf_local008", "sf_local056", 
                "sf_bq172", "sf_local244", "sf_bq210", "sf_bq216", "sf_bq158", "sf_local019", "sf_bq379", 
                "sf_local199", "sf_local049", "sf_local031", "sf_bq022", "sf_local059", "sf_bq032", "sf_bq281", 
                "sf_local067", "sf_local009", "sf_bq056", "sf_bq377", "sf_ga010"
            ]
            
            
            to_run = [
                'sf_local034', 'sf_local035', 'sf_local030', 'sf_bq226', 'sf_bq223', 'sf_bq221', 'sf_bq222', 'sf_local017',
                'sf_local015', 'sf_local259', 'sf_local026', 'sf_bq294', 'sf_bq339', 'sf_bq376', 'sf_bq363', 'sf_bq219', 'sf_bq349',
                'sf_bq253', 'sf_bq254', 'sf_bq041', 'sf_bq308', 'sf_bq303', 'sf_bq309', 'sf_local269', 'sf_local273', 'sf_bq263', 'sf_bq271',
                'sf_bq264', 'sf_bq273', 'sf_bq265', 'sf_bq260', 'sf_bq424', 'sf_bq444', 'sf_bq057', 'sf_bq093', 'sf_bq068', 'sf_bq334', 'sf_bq083',
                'sf_bq065', 'sf_bq193', 'sf_bq194', 'sf_bq248', 'sf_bq100', 'sf_bq233', 'sf_local063', 'sf_local360', 'sf_local300', 'sf_local299',
                'sf_local064', 'sf_local285', 'sf_local157', 'sf_local156', 'sf_bq128', 'sf_bq052', 'sf_bq246', 'sf_local003', 'sf_local002', 'sf_local336',
                'sf_local354', 'sf_local311', 'sf_local355', 'sf_bq278', 'sf_local073', 'sf014', 'sf_local195', 'sf_local194', 'sf_bq391', 'sf_local263',
                'sf_local081', 'sf_local209', 'sf_bq414', 'sf_bq420', 'sf_bq078', 'sf_bq229', 'sf_bq015', 'sf_bq104', 'sf_bq127', 'sf_local010',
                'sf_local168', 'sf_bq412', 'sf_bq397', 'sf_bq012', 'sf_bq187', 'sf_local283', 'sf_local152', 'sf_bq276', 'sf_bq452', 'sf_bq451',
                'sf_bq458', 'sf_bq167', 'sf_bq150', 'sf_bq457', 'sf_bq291', 'sf_bq200', 'sf_bq028', 'sf011', 'sf_bq072']

            bruce = {'sf001': 1, 'sf002': 0, 'sf011': 0, 'sf012': 0, 'sf014': 0, 'sf040': 0, 'sf044': 1, 'sf_bq001': 1, 'sf_bq008': 0, 'sf_bq010': 1, 'sf_bq011': 1, 'sf_bq012': 0, 'sf_bq015': 0, 'sf_bq017': 1, 'sf_bq022': 0, 'sf_bq025': 1, 'sf_bq028': 0, 'sf_bq031': 0, 'sf_bq032': 1, 'sf_bq033': 1, 'sf_bq034': 1, 'sf_bq035': 1, 'sf_bq037': 0, 'sf_bq040': 0, 'sf_bq041': 0, 'sf_bq057': 0, 'sf_bq060': 1, 'sf_bq061': 1, 'sf_bq066': 1, 'sf_bq070': 0, 'sf_bq072': 0, 'sf_bq076': 1, 'sf_bq077': 1, 'sf_bq078': 1, 'sf_bq079': 0, 'sf_bq081': 1, 'sf_bq083': 0, 'sf_bq085': 0, 'sf_bq091': 1, 'sf_bq093': 0, 'sf_bq099': 0, 'sf_bq100': 0, 'sf_bq102': 0, 'sf_bq104': 0, 'sf_bq108': 0, 'sf_bq109': 0, 'sf_bq112': 0, 'sf_bq114': 0, 'sf_bq115': 1, 'sf_bq119': 0, 'sf_bq121': 1, 'sf_bq126': 1, 'sf_bq127': 0, 'sf_bq128': 0, 'sf_bq130': 1, 'sf_bq150': 1, 'sf_bq153': 0, 'sf_bq155': 0, 'sf_bq158': 0, 'sf_bq159': 0, 'sf_bq161': 1, 'sf_bq166': 0, 'sf_bq167': 0, 'sf_bq172': 1, 'sf_bq176': 1, 'sf_bq185': 0, 'sf_bq187': 0, 'sf_bq193': 0, 'sf_bq194': 0, 'sf_bq198': 0, 'sf_bq200': 0, 'sf_bq203': 0, 'sf_bq208': 0, 'sf_bq209': 0, 'sf_bq210': 0, 'sf_bq213': 1, 'sf_bq216': 0, 'sf_bq219': 0, 'sf_bq221': 0, 'sf_bq222': 0, 'sf_bq223': 0, 'sf_bq224': 1, 'sf_bq226': 0, 'sf_bq229': 0, 'sf_bq235': 1, 'sf_bq236': 0, 'sf_bq248': 0, 'sf_bq250': 0, 'sf_bq252': 0, 'sf_bq255': 1, 'sf_bq260': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq270': 0, 'sf_bq271': 0, 'sf_bq273': 0, 'sf_bq275': 0, 'sf_bq276': 0, 'sf_bq278': 0, 'sf_bq279': 1, 'sf_bq280': 1, 'sf_bq281': 1, 'sf_bq282': 1, 'sf_bq284': 1, 'sf_bq285': 1, 'sf_bq286': 1, 'sf_bq294': 0, 'sf_bq295': 1, 'sf_bq300': 1, 'sf_bq301': 0, 'sf_bq303': 1, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq320': 0, 'sf_bq321': 0, 'sf_bq328': 1, 'sf_bq334': 0, 'sf_bq338': 0, 'sf_bq339': 0, 'sf_bq341': 1, 'sf_bq345': 1, 'sf_bq346': 1, 'sf_bq347': 0, 'sf_bq349': 0, 'sf_bq350': 1, 'sf_bq354': 0, 'sf_bq355': 1, 'sf_bq358': 0, 'sf_bq359': 1, 'sf_bq362': 1, 'sf_bq363': 1, 'sf_bq374': 0, 'sf_bq376': 0, 'sf_bq377': 0, 'sf_bq379': 1, 'sf_bq383': 0, 'sf_bq390': 0, 'sf_bq392': 1, 'sf_bq395': 0, 'sf_bq396': 0, 'sf_bq397': 0, 'sf_bq398': 1, 'sf_bq399': 1, 'sf_bq412': 0, 'sf_bq414': 1, 'sf_bq419': 0, 'sf_bq421': 0, 'sf_bq422': 0, 'sf_bq424': 0, 'sf_bq425': 0, 'sf_bq429': 0, 'sf_bq430': 0, 'sf_bq432': 0, 'sf_bq441': 0, 'sf_bq442': 1, 'sf_bq444': 1, 'sf_bq451': 0, 'sf_bq455': 0, 'sf_bq457': 0, 'sf_ga001': 1, 'sf_ga002': 1, 'sf_ga004': 1, 'sf_ga008': 0, 'sf_ga010': 1, 'sf_ga012': 0, 'sf_ga017': 0, 'sf_ga018': 0, 'sf_ga019': 0, 'sf_ga020': 0, 'sf_ga021': 0, 'sf_ga022': 0, 'sf_ga028': 0, 'sf_local002': 0, 'sf_local003': 0, 'sf_local004': 1, 'sf_local008': 1, 'sf_local009': 0, 'sf_local010': 0, 'sf_local015': 0, 'sf_local017': 1, 'sf_local019': 1, 'sf_local022': 1, 'sf_local026': 1, 'sf_local028': 1, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local035': 0, 'sf_local038': 1, 'sf_local039': 1, 'sf_local041': 1, 'sf_local049': 0, 'sf_local054': 1, 'sf_local056': 1, 'sf_local058': 1, 'sf_local059': 0, 'sf_local063': 0, 'sf_local064': 0, 'sf_local065': 0, 'sf_local067': 0, 'sf_local071': 1, 'sf_local072': 1, 'sf_local073': 0, 'sf_local075': 1, 'sf_local081': 0, 'sf_local099': 1, 'sf_local131': 1, 'sf_local132': 0, 'sf_local141': 1, 'sf_local152': 1, 'sf_local156': 0, 'sf_local157': 0, 'sf_local168': 0, 'sf_local194': 0, 'sf_local195': 1, 'sf_local199': 1, 'sf_local209': 0, 'sf_local210': 1, 'sf_local218': 1, 'sf_local244': 1, 'sf_local259': 0, 'sf_local263': 0, 'sf_local269': 0, 'sf_local273': 0, 'sf_local274': 1, 'sf_local283': 0, 'sf_local285': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local309': 0, 'sf_local311': 1, 'sf_local329': 1, 'sf_local336': 0, 'sf_local354': 0, 'sf_local355': 0, 'sf_local360': 0}
            # if task_config["instance_id"] not in ['sf_bq083']:
            # if task_config["instance_id"] not in ['sf011', 'sf014', 'sf_bq012', 'sf_bq015', 'sf_bq022', 'sf_bq028', 'sf_bq037', 'sf_bq041', 'sf_bq057', 'sf_bq072', 'sf_bq083', 'sf_bq093', 'sf_bq099', 'sf_bq100', 'sf_bq104', 'sf_bq109', 'sf_bq127', 'sf_bq128', 'sf_bq167', 'sf_bq187', 'sf_bq193', 'sf_bq194', 'sf_bq198', 'sf_bq200', 'sf_bq209', 'sf_bq210', 'sf_bq216', 'sf_bq219', 'sf_bq221', 'sf_bq222', 'sf_bq223', 'sf_bq226', 'sf_bq229', 'sf_bq248', 'sf_bq252', 'sf_bq260', 'sf_bq263', 'sf_bq264', 'sf_bq265', 'sf_bq271', 'sf_bq273', 'sf_bq276', 'sf_bq278', 'sf_bq294', 'sf_bq301', 'sf_bq308', 'sf_bq309', 'sf_bq334', 'sf_bq339', 'sf_bq349', 'sf_bq376', 'sf_bq377', 'sf_bq397', 'sf_bq412', 'sf_bq424', 'sf_bq451', 'sf_bq457', 'sf_local002', 'sf_local003', 'sf_local009', 'sf_local010', 'sf_local015', 'sf_local030', 'sf_local034', 'sf_local035', 'sf_local049', 'sf_local059', 'sf_local063', 'sf_local064', 'sf_local065', 'sf_local067', 'sf_local073', 'sf_local081', 'sf_local132', 'sf_local156', 'sf_local157', 'sf_local168', 'sf_local194', 'sf_local209', 'sf_local259', 'sf_local263', 'sf_local269', 'sf_local273', 'sf_local283', 'sf_local285', 'sf_local299', 'sf_local300', 'sf_local309', 'sf_local336', 'sf_local354', 'sf_local355', 'sf_local360']
            #     if task_config["instance_id"] not in ['sf_bq012','sf_bq017','sf_bq028','sf_bq033','sf_bq037','sf_bq043','sf_bq050','sf_bq052','sf_bq057','sf_bq068','sf_bq070','sf_bq072','sf_bq083','sf_bq091','sf_bq093','sf_bq099','sf_bq104','sf_bq121','sf_bq127','sf_bq128','sf_bq150','sf_bq153','sf_bq155','sf_bq158','sf_bq159','sf_bq166','sf_bq167','sf_bq176','sf_bq182','sf_bq187','sf_bq193','sf_bq209','sf_bq210','sf_bq213','sf_bq216','sf_bq219','sf_bq221','sf_bq222','sf_bq223','sf_bq224','sf_bq233','sf_bq236','sf_bq246','sf_bq248','sf_bq250','sf_bq252','sf_bq254','sf_bq255','sf_bq260','sf_bq263','sf_bq264','sf_bq265','sf_bq271','sf_bq273','sf_bq289','sf_bq291','sf_bq294','sf_bq295','sf_bq320','sf_bq321','sf_bq334','sf_bq341','sf_bq345','sf_bq346','sf_bq347','sf_bq349','sf_bq358','sf_bq359','sf_bq377','sf_bq390','sf_bq412','sf_bq421','sf_bq422','sf_bq429','sf_bq444','sf_bq455','sf_ga001','sf_local003','sf_local004','sf_local009','sf_local010','sf_local015','sf_local019','sf_local022','sf_local026','sf_local028','sf_local030','sf_local038','sf_local039','sf_local056','sf_local064','sf_local075','sf_local157','sf_local194','sf_local195','sf_local199','sf_local209','sf_local210','sf_local218','sf_local244','sf_local263','sf_local269','sf_local283','sf_local285','sf_local299','sf_local300','sf_local309','sf_local311','sf_local329','sf_local336','sf_local354','sf_local355','sf_local360']:
            if task_config["instance_id"] not in ["sf_bq093"]:
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
            agent.instruction_id = task_config['instance_id']
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

        # except Exception as e:
        #     logger.error("Error in %s: %s", task_config["instance_id"], e)
        #     continue

if __name__ == '__main__':
    args = config()
    
    test(args)