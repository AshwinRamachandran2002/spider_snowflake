import re

regex = r'''
SNOWFLAKE_MODIFY_CTE\(
                \s*sql_query\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<sql_query>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query,
                ,\s*reason\s*=\s*
                    (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
                    (?P<save_path>.*?)
                    (?<!\\)(?P=quote_path) 
                \s*\)
'''

test_string = '''
SNOWFLAKE_MODIFY_CTE(sql_query="
    SELECT 
        "application_number",
        "filing_date",
        assignee_harmonized.value:name AS "assignee_name",
        ipc_code.value:code AS "ipc_code"
    FROM 
        PATENTS.PATENTS.PUBLICATIONS,
        LATERAL FLATTEN(input => "ipc") AS ipc_code,
        LATERAL FLATTEN(input => "assignee_harmonized") AS assignee_harmonized
    WHERE 
        ipc_code.value:code LIKE 'A61%'
)", reason="")'''

match = re.search(regex, test_string.strip(), re.VERBOSE | re.DOTALL)
print("Valid" if match else "Invalid")
print(match)



print(re.findall(regex, test_string, flags=re.DOTALL | re.VERBOSE))




# # # # # a = """
# # # # # [
# # # # #         ["passenger_count", ">", "3"],
# # # # #         ["trip_distance", ">=", "10"],
# # # # #         ["pickup_datetime", ">=", "1454302800000000"],
# # # # #         ["dropoff_datetime", "<", "1454907600000000"],
# # # # #         ["pickup_location_id", "IN", "(SELECT \"location_id\" FROM NEW_YORK_PLUS.NEW_YORK_TAXI_TRIPS.TAXI_ZONE_GEOM WHERE \"borough\" = 'Brooklyn')"]
# # # # #     ]
# # # # # """
# # # # # import json

# # # # # print(json.loads(a))
# # # # text = """ SNOWFLAKE_EXEC_SQL(
# # # #     sql_query="
# # # #     SELECT "address", COUNT("address") AS frequency
# # # #     FROM GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS
# # # #     WHERE "block_timestamp" >= 1672531200
# # # #     AND "address" IS NOT NULL
# # # #     AND "block_number" > 4096
# # # #     GROUP BY "address"
# # # #     ORDER BY frequency DESC
# # # #     LIMIT 1
# # # #     ",
# # # #     conditional_clauses=[
# # # #         {"column_name": "block_timestamp", "condition_type": ">=", "keyword_or_pattern": "1672531200", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"},
# # # #         {"column_name": "address", "condition_type": "IS NOT NULL", "keyword_or_pattern": "", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"},
# # # #         {"column_name": "block_number", "condition_type": ">", "keyword_or_pattern": "4096", "table_name": "GOOG_BLOCKCHAIN.GOOG_BLOCKCHAIN_ARBITRUM_ONE_US.LOGS"}
# # # #     ],
# # # #     is_relevant: "True")
# # # # """
# # # # main_pattern = r'''
# # # #     SNOWFLAKE_EXEC_SQL\(
# # # #         \s*sql_query\s*=\s*
# # # #         (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
# # # #         (?P<sql_query>.*?)
# # # #         (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
# # # #         ,\s*conditional_clauses\s*=\s*
# # # #         (?P<conditional_clauses>.*?)
# # # #         ,\s*save_path\s*=\s*
# # # #             (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
# # # #             (?P<save_path>.*?)
# # # #             (?<!\\)(?P=quote_path)                     # Match closing quote for save_path
# # # #         \s*\)
# # # # '''
# # # # column_name = re.findall(r'"column_name"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # # # condition_type = re.findall(r'"condition_type"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # # # keyword_or_pattern = re.findall(r'"keyword_or_pattern"\s*:\s*"([^"]+?)"', text, flags=re.DOTALL | re.VERBOSE)
# # # # is_relevant = re.findall(r'is_relevant:\s*(.+?)\s*\)', text)
# # # # print(is_relevant)

# # # # conditional_clauses = []
# # # # for column_name, condition_type, pattern in zip(column_name, condition_type, keyword_or_pattern):
# # # #     conditional_clauses.append([column_name, condition_type, pattern])
# # # # print(conditional_clauses)
# # import os
# # import json

# # MAX_OBS_LENGTH = 20000
# # MAX_COLUMN_LENGTH = 40

# # source_data_dir = "examples"

# # first_illegal = 0
# # second_illegal = 0
# # select_ids = []
# # db_to = {}
# # to_db = {}
# # for instance_id in os.listdir(source_data_dir):    
# #     src_dir = os.path.join(source_data_dir, instance_id)
# #     if not os.path.isdir(src_dir):
# #         continue

# #     inside_dirs = os.listdir(src_dir)

# #     ok = 1

# #     # Assumption 1: .md file not very big
# #     for dir in inside_dirs:
# #         if dir.endswith(".md"):
# #             with open(os.path.join(src_dir, dir), "r") as f:
# #                 content = f.read()
# #                 if len(content) > MAX_OBS_LENGTH:
# #                     first_illegal += 1
# #                     ok = 0
# #                     break
# #     if ok == 0:
# #         continue

# #     # Assumption 2: DDL files not very big
# #     db = ""
# #     for dir in inside_dirs:
# #         if os.path.isdir(os.path.join(src_dir, dir)) and not dir == "spider":
# #             db = dir

# #             for ddl in os.listdir(os.path.join(src_dir, dir)):
# #                 db_dir = os.path.join(src_dir, dir, ddl)
# #                 files = os.listdir(db_dir)
# #                 num_jsons = 0
# #                 for file in files:
# #                     if file.endswith(".csv"):
# #                         with open(os.path.join(db_dir, file), "r") as f:
# #                             content = f.read()
# #                             print(instance_id, len(content))
# #                             if len(content) > MAX_OBS_LENGTH:
# #                                 ok = 0
# #                                 second_illegal += 1
# #                                 break
# #                 if ok == 0:
# #                     break
# #     if ok == 1:
# #         select_ids.append(instance_id)
# #         if db not in db_to:
# #             db_to[db] = []
# #         db_to[db].append(instance_id)
# #     to_db[instance_id] = db

# # print(len(select_ids))
# # bruce = {'sf001': 1, 'sf002': 0, 'sf011': 0, 'sf012': 0, 'sf014': 0, 'sf040': 0, 'sf044': 1, 'sf_bq001': 1, 'sf_bq008': 0, 'sf_bq010': 1, 'sf_bq011': 1, 'sf_bq012': 0, 'sf_bq015': 0, 'sf_bq017': 1, 'sf_bq022': 0, 'sf_bq025': 1, 'sf_bq028': 0, 'sf_bq031': 0, 'sf_bq032': 1, 'sf_bq033': 1, 'sf_bq034': 1, 'sf_bq035': 1, 'sf_bq037': 0, 'sf_bq040': 0, 'sf_bq041': 0, 'sf_bq057': 0, 'sf_bq060': 1, 'sf_bq061': 1, 'sf_bq066': 1, 'sf_bq070': 0, 'sf_bq072': 0, 'sf_bq076': 1, 'sf_bq077': 1, 'sf_bq078': 1, 'sf_bq079': 0, 'sf_bq081': 1, 'sf_bq083': 0, 'sf_bq085': 0, 'sf_bq091': 1, 'sf_bq093': 0, 'sf_bq099': 0, 'sf_bq100': 0, 'sf_bq102': 0, 'sf_bq104': 0, 'sf_bq108': 0, 'sf_bq109': 0, 'sf_bq112': 0, 'sf_bq114': 0, 'sf_bq115': 1, 'sf_bq119': 0, 'sf_bq121': 1, 'sf_bq126': 1, 'sf_bq127': 0, 'sf_bq128': 0, 'sf_bq130': 1, 'sf_bq150': 1, 'sf_bq153': 0, 'sf_bq155': 0, 'sf_bq158': 0, 'sf_bq159': 0, 'sf_bq161': 1, 'sf_bq166': 0, 'sf_bq167': 0, 'sf_bq172': 1, 'sf_bq176': 1, 'sf_bq185': 0, 'sf_bq187': 0, 'sf_bq193': 0, 'sf_bq194': 0, 'sf_bq198': 0, 'sf_bq200': 0, 'sf_bq203': 0, 'sf_bq208': 0, 'sf_bq209': 0, 'sf_bq210': 0, 'sf_bq213': 1, 'sf_bq216': 0, 'sf_bq219': 0, 'sf_bq221': 0, 'sf_bq222': 0, 'sf_bq223': 0, 'sf_bq224': 1, 'sf_bq226': 0, 'sf_bq229': 0, 'sf_bq235': 1, 'sf_bq236': 0, 'sf_bq248': 0, 'sf_bq250': 0, 'sf_bq252': 0, 'sf_bq255': 1, 'sf_bq260': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq270': 0, 'sf_bq271': 0, 'sf_bq273': 0, 'sf_bq275': 0, 'sf_bq276': 0, 'sf_bq278': 0, 'sf_bq279': 1, 'sf_bq280': 1, 'sf_bq281': 1, 'sf_bq282': 1, 'sf_bq284': 1, 'sf_bq285': 1, 'sf_bq286': 1, 'sf_bq294': 0, 'sf_bq295': 1, 'sf_bq300': 1, 'sf_bq301': 0, 'sf_bq303': 1, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq320': 0, 'sf_bq321': 0, 'sf_bq328': 1, 'sf_bq334': 0, 'sf_bq338': 0, 'sf_bq339': 0, 'sf_bq341': 1, 'sf_bq345': 1, 'sf_bq346': 1, 'sf_bq347': 0, 'sf_bq349': 0, 'sf_bq350': 1, 'sf_bq354': 0, 'sf_bq355': 1, 'sf_bq358': 0, 'sf_bq359': 1, 'sf_bq362': 1, 'sf_bq363': 1, 'sf_bq374': 0, 'sf_bq376': 0, 'sf_bq377': 0, 'sf_bq379': 1, 'sf_bq383': 0, 'sf_bq390': 0, 'sf_bq392': 1, 'sf_bq395': 0, 'sf_bq396': 0, 'sf_bq397': 0, 'sf_bq398': 1, 'sf_bq399': 1, 'sf_bq412': 0, 'sf_bq414': 1, 'sf_bq419': 0, 'sf_bq421': 0, 'sf_bq422': 0, 'sf_bq424': 0, 'sf_bq425': 0, 'sf_bq429': 0, 'sf_bq430': 0, 'sf_bq432': 0, 'sf_bq441': 0, 'sf_bq442': 1, 'sf_bq444': 1, 'sf_bq451': 0, 'sf_bq455': 0, 'sf_bq457': 0, 'sf_ga001': 1, 'sf_ga002': 1, 'sf_ga004': 1, 'sf_ga008': 0, 'sf_ga010': 1, 'sf_ga012': 0, 'sf_ga017': 0, 'sf_ga018': 0, 'sf_ga019': 0, 'sf_ga020': 0, 'sf_ga021': 0, 'sf_ga022': 0, 'sf_ga028': 0, 'sf_local002': 0, 'sf_local003': 0, 'sf_local004': 1, 'sf_local008': 1, 'sf_local009': 0, 'sf_local010': 0, 'sf_local015': 0, 'sf_local017': 1, 'sf_local019': 1, 'sf_local022': 1, 'sf_local026': 1, 'sf_local028': 1, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local035': 0, 'sf_local038': 1, 'sf_local039': 1, 'sf_local041': 1, 'sf_local049': 0, 'sf_local054': 1, 'sf_local056': 1, 'sf_local058': 1, 'sf_local059': 0, 'sf_local063': 0, 'sf_local064': 0, 'sf_local065': 0, 'sf_local067': 0, 'sf_local071': 1, 'sf_local072': 1, 'sf_local073': 0, 'sf_local075': 1, 'sf_local081': 0, 'sf_local099': 1, 'sf_local131': 1, 'sf_local132': 0, 'sf_local141': 1, 'sf_local152': 1, 'sf_local156': 0, 'sf_local157': 0, 'sf_local168': 0, 'sf_local194': 0, 'sf_local195': 1, 'sf_local199': 1, 'sf_local209': 0, 'sf_local210': 1, 'sf_local218': 1, 'sf_local244': 1, 'sf_local259': 0, 'sf_local263': 0, 'sf_local269': 0, 'sf_local273': 0, 'sf_local274': 1, 'sf_local283': 0, 'sf_local285': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local309': 0, 'sf_local311': 1, 'sf_local329': 1, 'sf_local336': 0, 'sf_local354': 0, 'sf_local355': 0, 'sf_local360': 0}

# # now_ids = []
# # for id in select_ids:
# #     if id in bruce and bruce[id] == 0:
# #         now_ids.append(id)
# # print(now_ids)
# # exit()
# # eval_all = {'sf001': 1, 'sf012': 0, 'sf018': 0, 'sf040': 0, 'sf044': 0, 'sf_bq001': 0, 'sf_bq011': 0, 'sf_bq012': 0, 'sf_bq022': 0, 'sf_bq024': 0, 'sf_bq025': 1, 'sf_bq028': 0, 'sf_bq031': 0, 'sf_bq032': 0, 'sf_bq034': 1, 'sf_bq035': 0, 'sf_bq037': 0, 'sf_bq040': 0, 'sf_bq041': 0, 'sf_bq052': 0, 'sf_bq056': 0, 'sf_bq057': 0, 'sf_bq060': 1, 'sf_bq061': 0, 'sf_bq065': 0, 'sf_bq068': 0, 'sf_bq070': 0, 'sf_bq072': 0, 'sf_bq076': 1, 'sf_bq077': 1, 'sf_bq078': 0, 'sf_bq079': 0, 'sf_bq081': 1, 'sf_bq085': 0, 'sf_bq099': 0, 'sf_bq100': 0, 'sf_bq102': 0, 'sf_bq104': 0, 'sf_bq108': 0, 'sf_bq109': 0, 'sf_bq112': 0, 'sf_bq114': 0, 'sf_bq115': 1, 'sf_bq119': 0, 'sf_bq121': 1, 'sf_bq126': 0, 'sf_bq127': 0, 'sf_bq128': 0, 'sf_bq130': 1, 'sf_bq150': 0, 'sf_bq153': 0, 'sf_bq155': 0, 'sf_bq159': 0, 'sf_bq161': 0, 'sf_bq166': 0, 'sf_bq167': 0, 'sf_bq172': 1, 'sf_bq176': 0, 'sf_bq185': 0, 'sf_bq187': 0, 'sf_bq193': 0, 'sf_bq198': 0, 'sf_bq200': 0, 'sf_bq203': 0, 'sf_bq208': 0, 'sf_bq209': 0, 'sf_bq210': 1, 'sf_bq216': 1, 'sf_bq219': 0, 'sf_bq221': 0, 'sf_bq222': 0, 'sf_bq226': 0, 'sf_bq229': 0, 'sf_bq235': 0, 'sf_bq236': 0, 'sf_bq246': 0, 'sf_bq248': 0, 'sf_bq252': 1, 'sf_bq255': 0, 'sf_bq260': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq268': 0, 'sf_bq270': 0, 'sf_bq271': 0, 'sf_bq273': 0, 'sf_bq275': 0, 'sf_bq276': 0, 'sf_bq278': 0, 'sf_bq279': 0, 'sf_bq280': 1, 'sf_bq281': 1, 'sf_bq282': 1, 'sf_bq284': 1, 'sf_bq285': 1, 'sf_bq286': 1, 'sf_bq291': 0, 'sf_bq294': 0, 'sf_bq295': 0, 'sf_bq300': 0, 'sf_bq301': 0, 'sf_bq303': 0, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq320': 0, 'sf_bq321': 0, 'sf_bq328': 0, 'sf_bq339': 0, 'sf_bq341': 1, 'sf_bq346': 0, 'sf_bq350': 0, 'sf_bq354': 0, 'sf_bq355': 0, 'sf_bq359': 0, 'sf_bq362': 1, 'sf_bq374': 0, 'sf_bq377': 1, 'sf_bq379': 0, 'sf_bq383': 0, 'sf_bq392': 1, 'sf_bq395': 0, 'sf_bq396': 1, 'sf_bq397': 0, 'sf_bq398': 0, 'sf_bq399': 0, 'sf_bq412': 0, 'sf_bq414': 0, 'sf_bq419': 1, 'sf_bq422': 0, 'sf_bq424': 0, 'sf_bq425': 0, 'sf_bq429': 0, 'sf_bq432': 0, 'sf_bq441': 0, 'sf_bq442': 0, 'sf_bq444': 0, 'sf_bq452': 0, 'sf_bq455': 0, 'sf_bq457': 0, 'sf_ga003': 0, 'sf_ga004': 0, 'sf_ga008': 0, 'sf_ga010': 0, 'sf_ga017': 0, 'sf_ga018': 0, 'sf_ga020': 0, 'sf_ga021': 0, 'sf_local002': 0, 'sf_local003': 0, 'sf_local004': 1, 'sf_local008': 0, 'sf_local009': 1, 'sf_local015': 0, 'sf_local017': 0, 'sf_local019': 0, 'sf_local022': 0, 'sf_local026': 0, 'sf_local028': 0, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local035': 0, 'sf_local038': 0, 'sf_local039': 1, 'sf_local041': 1, 'sf_local054': 1, 'sf_local056': 0, 'sf_local058': 1, 'sf_local059': 0, 'sf_local063': 0, 'sf_local064': 0, 'sf_local065': 0, 'sf_local067': 0, 'sf_local071': 0, 'sf_local072': 0, 'sf_local075': 0, 'sf_local081': 0, 'sf_local099': 1, 'sf_local131': 1, 'sf_local132': 0, 'sf_local141': 0, 'sf_local152': 0, 'sf_local156': 0, 'sf_local157': 0, 'sf_local168': 0, 'sf_local199': 0, 'sf_local209': 0, 'sf_local210': 0, 'sf_local218': 0, 'sf_local244': 0, 'sf_local259': 0, 'sf_local263': 0, 'sf_local269': 0, 'sf_local273': 0, 'sf_local274': 0, 'sf_local283': 0, 'sf_local285': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local309': 0, 'sf_local311': 0, 'sf_local329': 0, 'sf_local336': 0, 'sf_local354': 0, 'sf_local355': 0, 'sf_local360': 0}
# # result = {'sf_bq012': 0, 'sf_bq017': 1, 'sf_bq022': 1, 'sf_bq041': 0, 'sf_bq057': 0, 'sf_bq076': 1, 'sf_bq077': 1, 'sf_bq091': 0, 'sf_bq093': 0, 'sf_bq100': 0, 'sf_bq104': 0, 'sf_bq121': 0, 'sf_bq130': 1, 'sf_bq187': 0, 'sf_bq209': 0, 'sf_bq213': 1, 'sf_bq037': 1, 'sf_bq223': 0, 'sf_bq226': 0, 'sf_bq229': 0, 'sf_bq248': 0, 'sf_bq252': 0, 'sf_bq255': 0, 'sf_bq260': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq278': 0, 'sf_bq280': 1, 'sf_bq281': 0, 'sf_bq282': 1, 'sf_bq284': 0, 'sf_bq286': 1, 'sf_bq295': 0, 'sf_bq300': 0, 'sf_bq303': 0, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq349': 0, 'sf_bq359': 1, 'sf_bq362': 1, 'sf_bq363': 0, 'sf_bq377': 1, 'sf_bq397': 0, 'sf_bq412': 0, 'sf_bq442': 0, 'sf_bq444': 0, 'sf_local002': 0, 'sf_local004': 1, 'sf_local010': 0, 'sf_local019': 1, 'sf_local026': 0, 'sf_local028': 1, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local038': 1, 'sf_local039': 1, 'sf_local041': 1, 'sf_local049': 0, 'sf_local054': 1, 'sf_local056': 0, 'sf_local058': 1, 'sf_local059': 1, 'sf_local063': 0, 'sf_local064': 0, 'sf_local067': 0, 'sf_local071': 0, 'sf_local072': 0, 'sf_local075': 0, 'sf_local131': 0, 'sf_local132': 0, 'sf_local141': 1, 'sf_local152': 0, 'sf_local156': 0, 'sf_local157': 0, 'sf_local194': 0, 'sf_local199': 0, 'sf_local209': 0, 'sf_local210': 0, 'sf_local244': 1, 'sf_local269': 0, 'sf_local273': 0, 'sf_local274': 0, 'sf_local285': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local309': 0, 'sf_local311': 0, 'sf_local329': 0, 'sf_local336': 0, 'sf_local354': 0, 'sf_local355': 0, 'sf_local360': 0}

# # # sf_bq391, sf_bq452, sf_bq253, sf_bq182, sf_bq420, sf_bq233, sf_ga003, sf_bq458, sf_bq043, sf_bq291, sf_bq024, sf018, sf_bq050, sf_bq430, sf_bq289, sf_bq065, sf_bq246, sf_bq254, sf_bq068 (exceeded), sf_bq052, sf_bq268, sf_bq445, sf_bq056
# # empty = [
# #     'sf_bq391', 'sf_bq452', 'sf_bq253', 'sf_bq182', 'sf_bq420', 'sf_bq233', 'sf_ga003', 'sf_bq458', 'sf_bq043', 'sf_bq291', 'sf_bq024', 'sf018', 'sf_bq050', 'sf_bq430', 'sf_bq289', 'sf_bq065', 'sf_bq246', 'sf_bq254', 'sf_bq068', 'sf_bq052', 'sf_bq268', 'sf_bq445', 'sf_bq056'
# # ]

# # for id in empty:
# #     print("Database", to_db[id], id)
# #     if id in eval_all and eval_all[id] == 1:
# #         print(id)
# #     if id in result and result[id] == 1:
# #         print(id)
# # exit()
# # only_mine_correct = []
# # for id in result:
# #     if result[id] == 1 and id not in bruce_correct:
# #         only_mine_correct.append(id)
# # for id in eval_all:
# #     if eval_all[id] == 1 and id not in bruce_correct:
# #         only_mine_correct.append(id)

# # print(len(only_mine_correct))
# # print(only_mine_correct)

# # reviewed = [
# #     "sf_bq263",
# #     "sf_bq310",
# #     "sf_local049",
# #     "sf_local073",
# #     "sf_bq100",
# #     "sf_bq104",
# #     "sf_bq041",
# #     "sf_bq091",
# #     "sf_bq300",
# #     "sf_bq303",
# #     "sf_local035",
# #     "sf_local131",
# #     "sf_bq229",
# #     "sf_bq260",
# #     "sf_bq264",
# #     "sf_bq265",
# #     "sf_bq295",
# #     "sf_bq309",
# #     "sf_local030",
# #     "sf_local034",
# #     "sf_local056",
# #     "sf_local075",
# #     "sf_local099",
# #     "sf_local132",
# #     "sf_local194",
# #     "sf_local195",
# #     "sf_bq121",
# #     "sf_bq377",
# #     "sf_bq442",
# #     "sf_local026",
# #     "sf_local038",
# #     "sf_local081",
# #     "sf_local152",
# #     "sf_local157",
# #     "sf_local263",
# #     "sf_local329",
# #     "sf_bq091",
# #     "sf_bq260",
# # ]


# # incorrect_but_reviewed = list(set(reviewed))
# # print(len(incorrect_but_reviewed))

# # dont_see = ['sf001', 'sf044', 'sf_bq010', 'sf_bq017', 'sf_bq022', 'sf_bq025', 'sf_bq032', 'sf_bq033', 'sf_bq034',  'sf_bq035', 'sf_bq056', 'sf_bq060', 'sf_bq076', 'sf_bq077', 'sf_bq081', 'sf_bq085', 'sf_bq091',  'sf_bq099', 'sf_bq109', 'sf_bq112', 'sf_bq115', 'sf_bq121', 'sf_bq126', 'sf_bq130', 'sf_bq158',  'sf_bq159', 'sf_bq161', 'sf_bq172', 'sf_bq198', 'sf_bq209', 'sf_bq210', 'sf_bq213', 'sf_bq216',  'sf_bq224', 'sf_bq252', 'sf_bq255', 'sf_bq279', 'sf_bq280', 'sf_bq281', 'sf_bq282', 'sf_bq284',  'sf_bq285', 'sf_bq286', 'sf_bq295', 'sf_bq300', 'sf_bq301', 'sf_bq310', 'sf_bq328', 'sf_bq341',  'sf_bq350', 'sf_bq355', 'sf_bq359', 'sf_bq362', 'sf_bq377', 'sf_bq379', 'sf_bq392', 'sf_bq396',  'sf_bq398', 'sf_bq399', 'sf_bq419', 'sf_bq442', 'sf_ga001', 'sf_ga004', 'sf_ga010', 'sf_ga017', 'sf_local004',  'sf_local008', 'sf_local009', 'sf_local019', 'sf_local022', 'sf_local028', 'sf_local031',  'sf_local038', 'sf_local039', 'sf_local041', 'sf_local049', 'sf_local054', 'sf_local056',  'sf_local058', 'sf_local059', 'sf_local065', 'sf_local067', 'sf_local071', 'sf_local072',  'sf_local075', 'sf_local099', 'sf_local131', 'sf_local132', 'sf_local141', 'sf_local199',  'sf_local210', 'sf_local218', 'sf_local244', 'sf_local274', 'sf_local309', 'sf_local329']
# # incorrect_but_reviewed_and_minghang = list(set(incorrect_but_reviewed).union(set(dont_see)))
# # print(len(incorrect_but_reviewed_and_minghang))

# # incorrect_ids = []
# # db_to_corr = {}
# # for id in select_ids:
# #     if id in eval_all and eval_all[id] == 1:
# #         if to_db[id] not in db_to_corr:
# #             db_to_corr[to_db[id]] = []
# #         db_to_corr[to_db[id]].append(id)
# #         continue
# #     if id in result and result[id] == 1:
# #         if to_db[id] not in db_to_corr:
# #             db_to_corr[to_db[id]] = []
# #         db_to_corr[to_db[id]].append(id)
# #         continue
# #     incorrect_ids.append(id)

# # print(len(incorrect_ids))

# # diss = {}
# # tots = 0
# # sss = []
# # for db in db_to:
# #     if db in db_to_corr:
# #         diss[db] = [db, len(set(db_to_corr[db]) - set(dont_see)), len(set(db_to[db]) - set(dont_see)), set(db_to[db]) - set(db_to_corr[db]) - set(dont_see)]
# #         sss.extend(list(set(db_to[db]) - set(db_to_corr[db]) - set(dont_see)))
# #         tots += len(list(set(db_to[db]) - set(db_to_corr[db]) - set(dont_see)))
# #     else:
# #         diss[db] = [db, 0, len(set(db_to[db]) - set(dont_see)), 0, set(set(db_to[db]) - set(dont_see))]
# #         sss.extend(list(set(set(db_to[db]) - set(dont_see))))
# #         tots += len(list(set(set(db_to[db]) - set(dont_see))))
        
# # print(tots)
# # # sort diss by the third element of the list value
# # diss = dict(sorted(diss.items(), key=lambda item: item[1][2], reverse=True))
# # for key in diss:
# #     print(diss[key])

# # exit(0)
# # from tqdm import tqdm
# # output_dir_1 = "output/gpt-4o-agent-o1"
# # output_dir_2 = "output/gpt-4o-agent-o1-2"
# # for id in tqdm(sorted(sss)):
# #     try:
# #         print("ID:", id)

# #         if not os.path.exists(f"{output_dir_2}/{id}/spider/history_messages.json"):
# #             continue

# #         history_json = json.load(open(f"{output_dir_2}/{id}/spider/history_messages.json", "r"))
# #         print("ID:", id)
# #         print("Given", "\n".join(history_json[1]["content"][0]["text"].split("--------------------------------------------------")[1:]))    
# #         for msg in history_json[2:]:
# #             if msg["role"] == "user":
# #                 print("Output:")
# #                 print(msg["content"][0]["text"].split("```")[1])
# #             else:
# #                 print("GPT:")
# #                 print(msg["content"][0]["text"])
# #             input()
# #     except:
# #         continue


# import os
# import json
# import pandas as pd
# import snowflake.connector
# import csv
# import io

# # Load Snowflake credentials
# snowflake_credential = json.load(open("./snowflake_credential.json"))

# # Connect to Snowflake
# conn = snowflake.connector.connect(
#     **snowflake_credential
# )
# cursor = conn.cursor()

# # Define the SQL query
# sql_query = """
# SELECT distinct "cpc" from PATENTS.PATENTS.PUBLICATIONS limit 1;
# """

# # Execute the SQL query
# cursor.execute(sql_query)

# try:
#     # Fetch the results
#     results = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]
#     df = pd.DataFrame(results, columns=columns)
#     pd.set_option('display.max_colwidth', None)  # Show full column width

#     # Check if the result is empty
#     if df.empty:
#         print("No data found for the specified query.")
#     else:
#         # Save or print the results based on the is_save flag
#             csv_string = (df.to_csv(index=False, header=False))
#             rows = list(csv.reader(io.StringIO(csv_string)))
#             rows = [",".join([cell.replace('\\n', '') for cell in row]) for row in rows]
#             print("\\n".join(rows))
#             import json
#             # convert into JSON:
#             json_ting = (json.loads("\\n".join(rows)))
            
#             structure = ""
#             def go_in(obj):
#                 print(obj)
#                 if isinstance(obj, list):
#                     if len(obj) > 0:
#                         return "list of " + go_in(obj[0])
#                     else:
#                         return "list"
#                 elif isinstance(obj, dict):
#                     answer = "a dict consisting of keys: " + ", ".join([f"{key} of type {go_in(obj[key])}" for key in obj])
#                     return answer
#                 else:
#                     return str(type(obj))
#             print(go_in(json_ting))

# except Exception as e:
#     print("Error occurred while fetching data: ", e)
# finally:
#     cursor.close()
#     conn.close()


