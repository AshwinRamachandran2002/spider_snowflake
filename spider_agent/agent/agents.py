import base64
import json
import logging
import os
import re
import time
import uuid
from http import HTTPStatus
from io import BytesIO
from typing import Dict, List
from spider_agent.agent.prompts import BIGQUERY_SYSTEM, LOCAL_SYSTEM, DBT_SYSTEM, SNOWFLAKE_SYSTEM, REFERENCE_PLAN_SYSTEM, SNOWFLAKE_SYSTEM_CONSISTENCY
from spider_agent.agent.action import Action, Terminate, SNOWFLAKE_EXEC_SQL, SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON, SNOWFLAKE_READ_SCHEMA_FROM_DDL, SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE, SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE, SNOWFLAKE_JUSTIFY_DDL_RELEVANCE,SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE, SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE, PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS, SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK, SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN
from spider_agent.envs.spider_agent import Spider_Agent_Env
from spider_agent.agent.models import call_llm


from openai import AzureOpenAI
from typing import Dict, List, Optional, Tuple, Any, TypedDict




logger = logging.getLogger("spider_agent")


class PromptAgent:
    def __init__(
        self,
        model="gpt-4",
        max_tokens=1500,
        top_p=0.9,
        temperature=0.5,
        max_memory_length=10,
        max_steps=15,
        use_plan=False,
        consistency=False
    ):
        
        self.instruction_id = 0
        self.model = model
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.max_memory_length = max_memory_length
        self.max_steps = max_steps
        
        self.thoughts = []
        self.responses = []
        self.actions = []
        self.observations = []
        self.system_message = ""
        self.history_messages = []
        self.env = None
        self.codes = []
        self.work_dir = "/workspace"
        self.use_plan = use_plan
        
        self.consistency = consistency
        
    def set_env_and_task(self, env: Spider_Agent_Env):
        self.env = env
        self.thoughts = []
        self.responses = []
        self.actions = []
        self.observations = []
        self.codes = []
        self.history_messages = []
        self.instruction = self.env.task_config['instruction']
        # if 'plan' in self.env.task_config:
        #     self.reference_plan = self.env.task_config['plan']

        self._AVAILABLE_ACTION_CLASSES = [Terminate, SNOWFLAKE_EXEC_SQL, SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK, SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON, SNOWFLAKE_READ_SCHEMA_FROM_DDL, PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS,SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE, SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE, SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN, SNOWFLAKE_JUSTIFY_DDL_RELEVANCE, SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE, SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE]
        action_space = "".join([action_cls.get_action_description() for action_cls in self._AVAILABLE_ACTION_CLASSES])
        if self.consistency:
            self.system_message = SNOWFLAKE_SYSTEM_CONSISTENCY.format(work_dir=self.work_dir, action_space=action_space, task=self.instruction, max_steps=self.max_steps)
        else:
            self.system_message = SNOWFLAKE_SYSTEM.format(work_dir=self.work_dir, action_space=action_space, task=self.instruction, max_steps=self.max_steps)

        
        self.history_messages.append({
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": self.system_message 
                },
            ]
        })
        
    def predict(self, obs: Dict=None) -> List:
        """
        Predict the next action(s) based on the current observation.
        """    
        
        assert len(self.observations) == len(self.actions) and len(self.actions) == len(self.thoughts) \
            , "The number of observations and actions should be the same."

        status = False
        while not status:
            messages = self.history_messages.copy()
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Observation: {}\n".format(str(obs))
                    }
                ]
            })
            status, response = call_llm({
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "temperature": self.temperature
            })
            response = response.strip()
            if not status:
                if response in ["context_length_exceeded","rate_limit_exceeded","max_tokens","unknown_error"]:
                    self.history_messages = [self.history_messages[0]] + self.history_messages[3:]
                else:
                    raise Exception(f"Failed to call LLM, response: {response}")
        
        try:
            action = self.parse_action(response)

        except ValueError as e:
            print("Failed to parse action from response", e)
            observation = "Failed to parse action from your response, make sure you provide a valid action."
            
            action = None
        
        thought = re.search(r'Thought:(.*?)Action', response, flags=re.DOTALL)
        if thought:
            thought = thought.group(1).strip()
        else:
            thought = response

        logger.info("Observation: %s", obs)
        logger.info("Response: %s", response)

        self._add_message(obs, thought, action)
        self.observations.append(obs)
        self.thoughts.append(thought)
        self.responses.append(response)
        self.actions.append(action)

        return response, action
        
    
    def _add_message(self, observations: str, thought: str, action: Action):
        self.history_messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Observation: {}\n\n".format(observations)
                }
            ]
        })
        self.history_messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Thought: {}\n\nAction: {}".format(thought, str(action))
                }
            ]
        })
        if len(self.history_messages) > self.max_memory_length*2+1:
            self.history_messages = [self.history_messages[0]] + self.history_messages[-self.max_memory_length*2:]
    
    def parse_action(self, output: str) -> Action:
        """ Parse action from text """
        if output is None or len(output) == 0:
            pass
        action_string = ""
        patterns = [r'["\']?Action["\']?:? (.*?)Observation',r'["\']?Action["\']?:? (.*?)Thought', r'["\']?Action["\']?:? (.*?)$', r'^(.*?)Observation']

        for p in patterns:
            match = re.search(p, output, flags=re.DOTALL)
            if match:
                action_string = match.group(1).strip()
                break
        if action_string == "":
            action_string = output.strip()
        
        output_action = None
        for action_cls in self._AVAILABLE_ACTION_CLASSES:
            action = action_cls.parse_action_from_text(action_string)
            if action is not None:
                output_action = action
                break
        if output_action is None:
            action_string = action_string.replace("\_", "_").replace("'''","```")
            for action_cls in self._AVAILABLE_ACTION_CLASSES:
                action = action_cls.parse_action_from_text(action_string)
                if action is not None:
                    output_action = action
                    break
        
        return output_action



    def run(self):
        assert self.env is not None, "Environment is not set."
        result = ""
        done = False
        step_idx = 0
        self.model = "gpt-4o"

        if self.consistency:    
            obs = "You are in the folder now. Following is the directory tree structure:\n\n" + self.env.get_directory_tree() + "\n\n. Start by predicting a very very minimal set of column names and example rows that should be present in the final .csv file.\n"
            obs += "\nFunction Signature: \n" + PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS.get_action_description() + "\n"
            obs += "\n\nThe task is: " + self.instruction + "\n"
        else:
            obs = "You are in the folder now."

        retry_count = 0
        loaded_ok = 0
        while not done and step_idx < self.max_steps:
            
            # if obs and self.history_messages are saved for resuming the conversation then load them here
            import pickle
            if loaded_ok == 0 and os.path.exists(f"data_dump/{self.instruction_id}.pkl"):
                with open(f"data_dump/{self.instruction_id}.pkl", "rb") as f:
                    loaded = pickle.load(f)
                    loaded_ok = 1
                    obs = loaded["obs"]
                    self.history_messages = loaded["history_messages"]
                    self.env.registered_json = loaded["registered_json"]
                    self.env.md_files_content = loaded["md_files_content"]
                    self.env.instruction = loaded["instruction"]
                    self.env.predicted_obs = loaded["predicted_obs"]
                    obs = self.env.exec_sql_prompt()
                    obs += "\nTry to break down SQL into as many small and complete CTEs for better error handling\n\n"
                    # self.model = "o1"
                    

            _, action = self.predict(
                obs,
            )
            if action is None:
                logger.info("Failed to parse action from response, try again.")
                retry_count += 1
                if retry_count > 3:
                    logger.info("Failed to parse action from response, stop.")
                    break
                obs = "Failed to parse action from your response, make sure you provide a valid action."
            else:
                logger.info("Step %d: %s", step_idx + 1, action)
                obs, done, refresh = self.env.step(action)
                if refresh == "Go back to JSON justification":
                    self.history_messages = self.history_messages[:-2]
                elif refresh == "Go back to System Message(DUMP)":
                    self.history_messages = [self.history_messages[0]]
                    if os.path.exists(f"data_dump/{self.instruction_id}.pkl"):
                        os.remove(f"data_dump/{self.instruction_id}.pkl")
                    if not os.path.exists("data_dump"):
                        os.makedirs("data_dump")
                    with open(f"data_dump/{self.instruction_id}.pkl", "wb") as f:
                        pickle.dump({"obs": obs, "history_messages": self.history_messages, "registered_json": self.env.registered_json, "md_files_content": self.env.md_files_content, "instruction": self.env.instruction, "predicted_obs": self.env.predicted_obs}, f)
                elif refresh == "Go back to System Message":
                    self.history_messages = [self.history_messages[0]]
                    # self.model = "o1"
                elif refresh == "Go back to DDL justification":
                    self.history_messages = [self.history_messages[:-4]]
                    obs = "You are in the folder now."

            if done:
                if isinstance(action, Terminate):
                    result = action.output
                elif isinstance(action, SNOWFLAKE_EXEC_SQL):
                    result = action.save_path
                logger.info("The task is done.")
                break
            step_idx += 1

        # save history messages to work_dir

        return done, result, self.history_messages

    def get_trajectory(self):
        trajectory = []
        for i in range(len(self.observations)):
            trajectory.append({
                "observation": self.observations[i],
                "thought": self.thoughts[i],
                "action": str(self.actions[i]),
                # "code": self.codes[i],
                "response": self.responses[i]
            })
        trajectory_log = {
            "Task": self.instruction,
            "system_message": self.system_message,
            "trajectory": trajectory
        }
        return trajectory_log


if __name__ == "__main__":
    agent = PromptAgent()
    response = """
BIGQUERY_EXEC_SQL(sql_query=\"\"\"
WITH purchase_users AS (
  SELECT DISTINCT user_pseudo_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE event_name = 'purchase' AND _TABLE_SUFFIX BETWEEN '20201201' AND '20201231'
),
pageviews AS (
  SELECT user_pseudo_id, COUNT(*) AS pageviews
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE event_name = 'page_view' AND _TABLE_SUFFIX BETWEEN '20201201' AND '20201231'
  GROUP BY user_pseudo_id
),
pageviews_by_user AS (
  SELECT 
    p.user_pseudo_id, 
    p.pageviews,
    CASE WHEN pu.user_pseudo_id IS NOT NULL THEN 'purchaser' ELSE 'non-purchaser' END AS user_type
  FROM pageviews p
  LEFT JOIN purchase_users pu ON p.user_pseudo_id = pu.user_pseudo_id
)
SELECT user_type, AVG(pageviews) AS avg_pageviews
FROM pageviews_by_user
GROUP BY user_type
\"\"\", is_save=True, save_path="avg_pageviews_dec_2020.csv")
"""

    response = """
BIGQUERY_EXEC_SQL(sql_query=\"\"\"
SELECT DISTINCT user_pseudo_id
FROM bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
WHERE event_name = 'purchase' AND _TABLE_SUFFIX BETWEEN '20201201' AND '20201231'
\"\"\", is_save=False)
"""


    action = agent.parse_action(response)
    print(action)