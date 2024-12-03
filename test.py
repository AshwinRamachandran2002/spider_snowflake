# # import re

# # # regex = r'''
# # # SNOWFLAKE_EXEC_SQL\(
# # #     \s*sql_query\s*=\s*
# # #     (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
# # #     (?P<sql_query>.*?)
# # #     (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
# # #     ,\s*column_table_info\s*=\s*
# # #     (?P<column_table_info>.*?)
# # #     ,\s*conditional_clauses\s*=\s*
# # #     (?P<conditional_clauses>.*?)
# # #     ,\s*is_save\s*=\s*
# # #     (?P<is_save>True|False)
# # #     (?:,\s*save_path\s*=\s*
# # #         (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
# # #         (?P<save_path>.*?)
# # #         (?<!\\)(?P=quote_path)                     # Match closing quote for save_path
# # #     )?
# # #     \s*\)
# # # '''

# # # test_string = '''
# # # SNOWFLAKE_EXEC_SQL(
# # #     sql_query="""
# # #         SELECT 
# # #             L."repo_name" AS "repository_name", 
# # #             COUNT(SC."commit") AS "commit_count"
# # #         FROM 
# # #             GITHUB_REPOS.GITHUB_REPOS.LANGUAGES L
# # #         JOIN 
# # #             GITHUB_REPOS.GITHUB_REPOS.SAMPLE_COMMITS SC
# # #         ON 
# # #             L."repo_name" = SC."repo_name"
# # #         WHERE 
# # #             JSON_EXTRACT_PATH_TEXT(L."language", 'primary') = 'JavaScript'
# # #         GROUP BY 
# # #             L."repo_name"
# # #         ORDER BY 
# # #             "commit_count" DESC
# # #         LIMIT 2
# # #     """,
# # #     column_table_info={
# # #         "GITHUB_REPOS.GITHUB_REPOS.LANGUAGES": {
# # #             "repo_name": {"type": "TEXT", "single_sample_value": "debjyoti385/awesome-data-mining-datasets"},
# # #             "language": {"type": "VARIANT", "single_sample_value": "[]"}
# # #         },
# # #         "GITHUB_REPOS.GITHUB_REPOS.SAMPLE_COMMITS": {
# # #             "commit": {"type": "TEXT", "single_sample_value": "76cdd58e558669366adfaded436fda01b30cce3e"},
# # #             "repo_name": {"type": "TEXT", "single_sample_value": "torvalds/linux"}
# # #         }
# # #     },
# # #     conditional_clauses=[("language", "ILIKE", "'%JavaScript%'")],
# # #     is_save=True,
# # #     save_path="/workspace/top_two_repos.csv"
# # # )'''

# # # match = re.search(regex, test_string.strip(), re.VERBOSE | re.DOTALL)
# # # print("Valid" if match else "Invalid")









# # # a = """
# # # [
# # #         ["passenger_count", ">", "3"],
# # #         ["trip_distance", ">=", "10"],
# # #         ["pickup_datetime", ">=", "1454302800000000"],
# # #         ["dropoff_datetime", "<", "1454907600000000"],
# # #         ["pickup_location_id", "IN", "(SELECT \"location_id\" FROM NEW_YORK_PLUS.NEW_YORK_TAXI_TRIPS.TAXI_ZONE_GEOM WHERE \"borough\" = 'Brooklyn')"]
# # #     ]
# # # """
# # # import json

# # # print(json.loads(a))
# # text = """ SNOWFLAKE_EXEC_SQL(
# #     sql_query="
# #     SELECT "address", COUNT("address") AS frequency
# #     FROM GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS
# #     WHERE "block_timestamp" >= 1672531200
# #     AND "address" IS NOT NULL
# #     AND "block_number" > 4096
# #     GROUP BY "address"
# #     ORDER BY frequency DESC
# #     LIMIT 1
# #     ",
# #     conditional_clauses=[
# #         {"column_name": "block_timestamp", "condition_type": ">=", "keyword_or_pattern": "1672531200", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"},
# #         {"column_name": "address", "condition_type": "IS NOT NULL", "keyword_or_pattern": "", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"},
# #         {"column_name": "block_number", "condition_type": ">", "keyword_or_pattern": "4096", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"}
# #     ],
# #     is_relevant: "True")
# # """
# # main_pattern = r'''
# #     SNOWFLAKE_EXEC_SQL\(
# #         \s*sql_query\s*=\s*
# #         (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
# #         (?P<sql_query>.*?)
# #         (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
# #         ,\s*conditional_clauses\s*=\s*
# #         (?P<conditional_clauses>.*?)
# #         ,\s*save_path\s*=\s*
# #             (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
# #             (?P<save_path>.*?)
# #             (?<!\\)(?P=quote_path)                     # Match closing quote for save_path
# #         \s*\)
# # '''
# # column_name = re.findall(r'"column_name"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # condition_type = re.findall(r'"condition_type"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # keyword_or_pattern = re.findall(r'"keyword_or_pattern"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # is_relevant = re.findall(r'is_relevant:\s*(.+?)\s*\)', text)
# # print(is_relevant)

# # conditional_clauses = []
# # for column_name, condition_type, pattern in zip(column_name, condition_type, keyword_or_pattern):
# #     conditional_clauses.append([column_name, condition_type, pattern])
# # print(conditional_clauses)

import os
import json

MAX_OBS_LENGTH = 40000
MAX_COLUMN_LENGTH = 40

source_data_dir = "examples"
eval = "../../spider2-snow/evaluation_suite/all.json"
eval = json.load(open(eval, "r"))
eval_all = {}
for instance in eval:
    eval_all[instance["id"]] = instance["score"]

first_illegal = 0
second_illegal = 0
third_illegal = 0
fourth_illegal = 0

db_id = {}
db_score = {}
instance_db = {}
instance_score = {}
for instance_id in os.listdir(source_data_dir):    
    src_dir = os.path.join(source_data_dir, instance_id)
    if not os.path.isdir(src_dir):
        continue

    inside_dirs = os.listdir(src_dir)
    for dir in inside_dirs:

        if os.path.isdir(os.path.join(src_dir, dir)) and not dir == "spider":
            instance_db[instance_id] = dir

            if not len(os.listdir(os.path.join(src_dir, dir))) == 1:
                first_illegal += 1
                if len(os.listdir(os.path.join(src_dir, dir))) == 2:
                    print(instance_id)
                    exit()
                continue

            db_dir = os.path.join(src_dir, dir, os.listdir(os.path.join(src_dir, dir))[0])
            files = os.listdir(db_dir)
            num_jsons = 0
            for file in files:

                ok = 1
                if file.endswith(".csv"):
                    with open(os.path.join(db_dir, file), "r") as f:
                        content = f.read()
                        if len(content) > MAX_OBS_LENGTH:
                            ok = 0
                            second_illegal += 1
                            break

                elif file.endswith(".json"):
                    num_jsons += 1
                    with open(os.path.join(db_dir, file), "r") as f:
                        content = json.load(f)
                        column_names = content["column_names"]
                        if len(column_names) > MAX_COLUMN_LENGTH:
                            ok = 0
                            third_illegal += 1
                            break
            
            if num_jsons > MAX_COLUMN_LENGTH:
                fourth_illegal += 1
                ok = 0
            if ok == 1:
                db_id[dir] = db_id.get(dir, []) + [instance_id]
                db_score[dir] = db_score.get(dir, 0) + eval_all.get(instance_id, 0)
                instance_score[instance_id] = eval_all.get(instance_id, 0)
print(db_score)
print(db_id)
count = 0
score = 0
id_list = []
for key in db_id:
    count += len(db_id[key])
    id_list += db_id[key]
    score += db_score[key]
print(count)
print(score)
print(db_id.keys())
print(id_list)
print(first_illegal)
print(second_illegal)
print(third_illegal)
print(fourth_illegal)


# result = {'sf_bq012': 0, 'sf_bq028': 0, 'sf_bq033': 0, 'sf_bq035': 1, 'sf_bq041': 0, 'sf_bq091': 0, 'sf_bq099': 0, 'sf_bq100': 0, 'sf_bq104': 0, 'sf_bq121': 0, 'sf_bq130': 1, 'sf_bq187': 0, 'sf_bq193': 0, 'sf_bq209': 0, 'sf_bq210': 0, 'sf_bq213': 1, 'sf_bq223': 0, 'sf_bq229': 0, 'sf_bq248': 0, 'sf_bq252': 0, 'sf_bq255': 1, 'sf_bq260': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq273': 0, 'sf_bq280': 1, 'sf_bq284': 0, 'sf_bq286': 1, 'sf_bq295': 0, 'sf_bq300': 0, 'sf_bq301': 1, 'sf_bq303': 0, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 0, 'sf_bq359': 1, 'sf_bq377': 0, 'sf_bq442': 0, 'sf_local002': 0, 'sf_local004': 1, 'sf_local009': 0, 'sf_local010': 0, 'sf_local019': 1, 'sf_local026': 0, 'sf_local028': 1, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local035': 0, 'sf_local038': 0, 'sf_local041': 0, 'sf_local049': 0, 'sf_local054': 0, 'sf_local056': 0, 'sf_local058': 0, 'sf_local059': 0, 'sf_local064': 0, 'sf_local065': 1, 'sf_local073': 0, 'sf_local075': 0, 'sf_local081': 0, 'sf_local099': 0, 'sf_local131': 0, 'sf_local132': 0, 'sf_local152': 0, 'sf_local157': 0, 'sf_local194': 0, 'sf_local195': 0, 'sf_local199': 1, 'sf_local244': 1, 'sf_local263': 0, 'sf_local285': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local329': 0, 'sf_local360': 0}
# before = instance_score

# before_total = 0
# after_total = 0
# incorrect = []
# correct = []
# total = 0
# for key in result:
#     if key not in before:
#         print(result[key])
#         continue
#     before_total += before[key]
#     after_total += result[key]
#     if result[key] != 1:
#         incorrect.append(key)
#     else:
#         correct.append(key)
#     total += 1
# print(before_total)
# print(after_total)
# print(total)
# print(sorted(incorrect))
# print(sorted(correct))


# reviewed_ids = [
#     'bq121', 'bq263', 'bq310', 'local049', 'local073',
#     'bq377', 'bq442', 'local026', 'local038', 'local081',
#     'local152', 'local157', 'local263', 'local329', 'bq193',
#     'bq223', 'bq248', 'bq252', 'bq210', 'bq284', 'bq308',
#     'local009', 'local041', 'local054', 'local058', 'local059',
#     'bq229', 'bq260', 'bq264', 'bq265', 'bq295', 'bq309',
#     'local030', 'local034', 'local056', 'local075', 'local099',
#     'local132', 'local194', 'local195', 'bq300', 'bq303',
#     'local035', 'local131', 'bq028', 'bq033', 'bq091', 'bq099', 'bq100', 'bq104', 
# ]
# for i, id in enumerate(reviewed_ids):
#     reviewed_ids[i] = f"sf_{id}"
# print(len(reviewed_ids))

# from tqdm import tqdm
# output_dir = "output/gpt-4o-column-o1-2"
# for id in tqdm(sorted(incorrect)):
#     if id in reviewed_ids:
#         continue
#     history_json = json.load(open(f"{output_dir}/{id}/spider/history_messages.json", "r"))
#     print("ID:", id)
#     print("Given", "\n".join(history_json[1]["content"][0]["text"].split("--------------------------------------------------")[1:]))    
#     for msg in history_json[2:]:
#         if msg["role"] == "user":
#             print("Output:")
#             print(msg["content"][0]["text"].split("```")[1])
#         else:
#             print("GPT:")
#             print(msg["content"][0]["text"])
#         input()