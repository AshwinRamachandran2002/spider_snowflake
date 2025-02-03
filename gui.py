import os
import pickle
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from io import StringIO
import pandas as pd
import json

# Add this near the top with your layout
loading_component = dcc.Loading(
    id="loading-content",
    children=[html.Div(id="main-content")],
    type="circle",
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Function to load data
def get_info_instance_id(instance_id):
    run_dump_directory = "data_dump/"
    data_dump_path = os.path.join(run_dump_directory, instance_id + ".pkl")
    with open(data_dump_path, "rb") as f:
        loaded = pickle.load(f)

    registered_json = loaded["registered_json"]
    instruction = loaded["instruction"]
    predicted_obs = loaded["predicted_obs"]

    sql_dump_directory = "sql_dump/"
    data_dump_path = os.path.join(sql_dump_directory, instance_id + ".pkl")
    with open(data_dump_path, "rb") as f:
        loaded = pickle.load(f)

    indi_sqls = loaded["indi_sqls"]
    tables = loaded["tables"]
    last_major_sql = loaded["last_major_sql"]
    final_exec = loaded["final_exec"]
    indi_sqls_exec = loaded["indi_sqls_exec"]

    gold_exec_directory = "../../../Spider2-new/spider2-snow/evaluation_suite/gold/exec_result/"
    gold_exec_path = os.path.join(gold_exec_directory, instance_id.split(".")[0] + ".csv")
    gold_exec = pd.read_csv(gold_exec_path) if os.path.exists(gold_exec_path) else None
    
    if gold_exec is not None:
        condition_cols_content = open("../../../Spider2-new/spider2-snow/evaluation_suite/gold/spider2snow_eval.jsonl")
        condition_cols_content = [json.loads(line) for line in condition_cols_content.readlines()]

        condition_cols_collection = {}
        for item in condition_cols_content:
            condition_cols_collection[item["instance_id"]] = item["condition_cols"]

        condition_cols = condition_cols_collection[instance_id]

        if condition_cols != []:
            gold_exec = gold_exec.iloc[:, condition_cols]
            
    messages_directory = "output/gpt-4o-agent-o1-temp/"
    messages_path = os.path.join(messages_directory, instance_id, "spider", "history_messages.json")
    with open(messages_path, "r") as f:
        history_messages = json.load(f)

    return history_messages, registered_json, instruction, predicted_obs, indi_sqls, tables, last_major_sql, final_exec, indi_sqls_exec, gold_exec

# Function to load comments
def load_comments(instance_id):
    comments_file = f"comments/{instance_id}.txt"
    if os.path.exists(comments_file):
        with open(comments_file, "r") as f:
            return f.read()
    return ""

# Get instance IDs
examples_dict = "examples/spider2-snow.jsonl"
instance_metadata = {}
with open(examples_dict, "r") as f:
    for line in f:
        data = json.loads(line)
        instance_metadata[data["instance_id"]] = data


instance_ids = list(os.listdir("output/gpt-4o-agent-o1-temp/"))
minghang = {'sf001': 1, 'sf002': 0, 'sf003': 0, 'sf006': 0, 'sf008': 0, 'sf009': 0, 'sf010': 1, 'sf011': 0, 'sf012': 0, 'sf013': 0, 'sf014': 1, 'sf018': 0, 'sf029': 0, 'sf035': 0, 'sf037': 0, 'sf040': 0, 'sf044': 1, 'sf_bq001': 0, 'sf_bq002': 0, 'sf_bq003': 0, 'sf_bq004': 0, 'sf_bq005': 0, 'sf_bq006': 1, 'sf_bq007': 0, 'sf_bq008': 0, 'sf_bq009': 0, 'sf_bq010': 1, 'sf_bq011': 1, 'sf_bq012': 0, 'sf_bq014': 0, 'sf_bq015': 0, 'sf_bq016': 0, 'sf_bq018': 1, 'sf_bq019': 0, 'sf_bq021': 1, 'sf_bq022': 0, 'sf_bq025': 1, 'sf_bq026': 0, 'sf_bq027': 0, 'sf_bq028': 0, 'sf_bq029': 0, 'sf_bq030': 0, 'sf_bq031': 0, 'sf_bq032': 1, 'sf_bq033': 0, 'sf_bq034': 1, 'sf_bq035': 1, 'sf_bq036': 0, 'sf_bq037': 0, 'sf_bq038': 0, 'sf_bq039': 0, 'sf_bq040': 0, 'sf_bq041': 0, 'sf_bq042': 0, 'sf_bq045': 0, 'sf_bq047': 0, 'sf_bq048': 0, 'sf_bq049': 0, 'sf_bq050': 0, 'sf_bq051': 0, 'sf_bq052': 0, 'sf_bq053': 0, 'sf_bq054': 0, 'sf_bq055': 0, 'sf_bq056': 1, 'sf_bq057': 0, 'sf_bq059': 0, 'sf_bq060': 1, 'sf_bq061': 1, 'sf_bq062': 1, 'sf_bq063': 0, 'sf_bq064': 0, 'sf_bq065': 0, 'sf_bq066': 1, 'sf_bq067': 0, 'sf_bq069': 0, 'sf_bq071': 0, 'sf_bq072': 0, 'sf_bq073': 0, 'sf_bq074': 0, 'sf_bq075': 0, 'sf_bq076': 1, 'sf_bq077': 1, 'sf_bq078': 0, 'sf_bq079': 0, 'sf_bq080': 0, 'sf_bq081': 0, 'sf_bq083': 0, 'sf_bq084': 0, 'sf_bq085': 1, 'sf_bq086': 0, 'sf_bq087': 0, 'sf_bq088': 1, 'sf_bq089': 0, 'sf_bq090': 1, 'sf_bq091': 1, 'sf_bq092': 0, 'sf_bq093': 0, 'sf_bq094': 0, 'sf_bq095': 0, 'sf_bq096': 0, 'sf_bq097': 1, 'sf_bq098': 0, 'sf_bq099': 1, 'sf_bq101': 0, 'sf_bq102': 0, 'sf_bq103': 1, 'sf_bq104': 0, 'sf_bq108': 0, 'sf_bq109': 1, 'sf_bq110': 0, 'sf_bq112': 0, 'sf_bq113': 0, 'sf_bq114': 0, 'sf_bq115': 1, 'sf_bq116': 0, 'sf_bq117': 0, 'sf_bq118': 0, 'sf_bq119': 0, 'sf_bq120': 0, 'sf_bq121': 1, 'sf_bq123': 0, 'sf_bq124': 0, 'sf_bq126': 1, 'sf_bq127': 0, 'sf_bq128': 0, 'sf_bq130': 1, 'sf_bq131': 0, 'sf_bq135': 1, 'sf_bq136': 0, 'sf_bq137': 0, 'sf_bq143': 0, 'sf_bq144': 0, 'sf_bq147': 0, 'sf_bq148': 0, 'sf_bq150': 1, 'sf_bq151': 1, 'sf_bq153': 0, 'sf_bq154': 0, 'sf_bq155': 0, 'sf_bq156': 0, 'sf_bq157': 0, 'sf_bq158': 0, 'sf_bq159': 0, 'sf_bq160': 0, 'sf_bq161': 1, 'sf_bq162': 0, 'sf_bq166': 0, 'sf_bq167': 0, 'sf_bq169': 0, 'sf_bq170': 0, 'sf_bq171': 0, 'sf_bq172': 1, 'sf_bq175': 0, 'sf_bq176': 1, 'sf_bq177': 0, 'sf_bq180': 0, 'sf_bq181': 0, 'sf_bq184': 0, 'sf_bq185': 0, 'sf_bq186': 0, 'sf_bq187': 0, 'sf_bq188': 0, 'sf_bq189': 0, 'sf_bq190': 0, 'sf_bq191': 0, 'sf_bq192': 0, 'sf_bq194': 0, 'sf_bq195': 0, 'sf_bq197': 0, 'sf_bq198': 0, 'sf_bq199': 0, 'sf_bq202': 0, 'sf_bq203': 0, 'sf_bq204': 0, 'sf_bq207': 0, 'sf_bq208': 0, 'sf_bq209': 0, 'sf_bq210': 1, 'sf_bq211': 1, 'sf_bq212': 0, 'sf_bq213': 1, 'sf_bq214': 1, 'sf_bq215': 0, 'sf_bq216': 1, 'sf_bq217': 0, 'sf_bq218': 0, 'sf_bq219': 0, 'sf_bq220': 0, 'sf_bq221': 0, 'sf_bq222': 0, 'sf_bq223': 0, 'sf_bq224': 1, 'sf_bq225': 0, 'sf_bq226': 0, 'sf_bq227': 1, 'sf_bq228': 1, 'sf_bq229': 0, 'sf_bq230': 0, 'sf_bq232': 0, 'sf_bq233': 0, 'sf_bq234': 0, 'sf_bq235': 1, 'sf_bq236': 0, 'sf_bq247': 0, 'sf_bq248': 0, 'sf_bq249': 0, 'sf_bq250': 0, 'sf_bq252': 1, 'sf_bq255': 1, 'sf_bq256': 0, 'sf_bq258': 0, 'sf_bq259': 0, 'sf_bq260': 0, 'sf_bq261': 0, 'sf_bq262': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq266': 0, 'sf_bq268': 0, 'sf_bq269': 0, 'sf_bq270': 0, 'sf_bq271': 0, 'sf_bq272': 0, 'sf_bq273': 0, 'sf_bq275': 0, 'sf_bq276': 0, 'sf_bq278': 0, 'sf_bq279': 1, 'sf_bq280': 1, 'sf_bq281': 1, 'sf_bq282': 1, 'sf_bq283': 0, 'sf_bq284': 0, 'sf_bq285': 1, 'sf_bq286': 1, 'sf_bq287': 0, 'sf_bq288': 0, 'sf_bq289': 1, 'sf_bq290': 0, 'sf_bq292': 0, 'sf_bq293': 0, 'sf_bq294': 0, 'sf_bq295': 0, 'sf_bq300': 1, 'sf_bq301': 0, 'sf_bq302': 1, 'sf_bq303': 0, 'sf_bq304': 0, 'sf_bq305': 0, 'sf_bq306': 0, 'sf_bq307': 0, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq320': 0, 'sf_bq321': 0, 'sf_bq323': 0, 'sf_bq324': 0, 'sf_bq326': 0, 'sf_bq327': 1, 'sf_bq328': 1, 'sf_bq330': 1, 'sf_bq331': 0, 'sf_bq333': 0, 'sf_bq334': 0, 'sf_bq335': 0, 'sf_bq338': 0, 'sf_bq339': 0, 'sf_bq341': 1, 'sf_bq342': 0, 'sf_bq345': 1, 'sf_bq346': 0, 'sf_bq347': 0, 'sf_bq349': 0, 'sf_bq350': 0, 'sf_bq352': 1, 'sf_bq354': 0, 'sf_bq355': 1, 'sf_bq356': 0, 'sf_bq357': 1, 'sf_bq358': 0, 'sf_bq359': 1, 'sf_bq360': 0, 'sf_bq361': 1, 'sf_bq362': 1, 'sf_bq363': 0, 'sf_bq366': 0, 'sf_bq374': 0, 'sf_bq375': 1, 'sf_bq376': 0, 'sf_bq377': 1, 'sf_bq379': 1, 'sf_bq380': 0, 'sf_bq383': 0, 'sf_bq389': 0, 'sf_bq390': 0, 'sf_bq392': 1, 'sf_bq393': 0, 'sf_bq394': 1, 'sf_bq395': 0, 'sf_bq396': 1, 'sf_bq397': 0, 'sf_bq398': 1, 'sf_bq399': 1, 'sf_bq400': 0, 'sf_bq402': 0, 'sf_bq403': 0, 'sf_bq406': 1, 'sf_bq407': 0, 'sf_bq410': 0, 'sf_bq411': 0, 'sf_bq413': 0, 'sf_bq414': 1, 'sf_bq415': 0, 'sf_bq416': 0, 'sf_bq417': 0, 'sf_bq418': 0, 'sf_bq419': 0, 'sf_bq420': 0, 'sf_bq421': 1, 'sf_bq423': 0, 'sf_bq424': 0, 'sf_bq425': 0, 'sf_bq426': 1, 'sf_bq427': 0, 'sf_bq428': 0, 'sf_bq429': 0, 'sf_bq430': 0, 'sf_bq432': 0, 'sf_bq441': 0, 'sf_bq442': 0, 'sf_bq444': 0, 'sf_bq445': 0, 'sf_bq450': 0, 'sf_bq451': 0, 'sf_bq452': 0, 'sf_bq453': 0, 'sf_bq454': 0, 'sf_bq455': 0, 'sf_bq456': 0, 'sf_bq457': 0, 'sf_bq458': 0, 'sf_bq459': 0, 'sf_bq460': 0, 'sf_bq461': 0, 'sf_bq462': 0, 'sf_ga001': 1, 'sf_ga002': 1, 'sf_ga003': 1, 'sf_ga004': 1, 'sf_ga006': 0, 'sf_ga007': 0, 'sf_ga008': 0, 'sf_ga009': 0, 'sf_ga010': 1, 'sf_ga011': 0, 'sf_ga012': 0, 'sf_ga013': 0, 'sf_ga014': 0, 'sf_ga017': 0, 'sf_ga019': 0, 'sf_ga020': 0, 'sf_ga021': 0, 'sf_ga022': 0, 'sf_ga025': 0, 'sf_ga028': 0, 'sf_ga030': 0, 'sf_ga031': 0, 'sf_local002': 0, 'sf_local003': 0, 'sf_local004': 0, 'sf_local007': 0, 'sf_local008': 0, 'sf_local009': 0, 'sf_local010': 0, 'sf_local015': 0, 'sf_local017': 1, 'sf_local018': 0, 'sf_local019': 1, 'sf_local020': 0, 'sf_local021': 0, 'sf_local022': 1, 'sf_local023': 1, 'sf_local024': 0, 'sf_local025': 0, 'sf_local026': 0, 'sf_local028': 1, 'sf_local029': 0, 'sf_local030': 0, 'sf_local031': 1, 'sf_local032': 0, 'sf_local034': 0, 'sf_local035': 0, 'sf_local037': 0, 'sf_local038': 0, 'sf_local039': 1, 'sf_local040': 0, 'sf_local041': 1, 'sf_local049': 0, 'sf_local050': 0, 'sf_local054': 1, 'sf_local055': 0, 'sf_local056': 1, 'sf_local058': 1, 'sf_local059': 0, 'sf_local060': 0, 'sf_local061': 0, 'sf_local062': 0, 'sf_local063': 0, 'sf_local064': 0, 'sf_local065': 1, 'sf_local066': 0, 'sf_local067': 1, 'sf_local068': 0, 'sf_local070': 0, 'sf_local071': 1, 'sf_local072': 1, 'sf_local073': 0, 'sf_local074': 1, 'sf_local075': 1, 'sf_local077': 0, 'sf_local078': 1, 'sf_local081': 0, 'sf_local085': 0, 'sf_local096': 0, 'sf_local097': 0, 'sf_local098': 0, 'sf_local099': 0, 'sf_local114': 0, 'sf_local128': 0, 'sf_local130': 0, 'sf_local131': 1, 'sf_local132': 0, 'sf_local133': 0, 'sf_local141': 1, 'sf_local152': 0, 'sf_local156': 0, 'sf_local157': 0, 'sf_local163': 1, 'sf_local167': 0, 'sf_local168': 0, 'sf_local169': 0, 'sf_local170': 0, 'sf_local171': 0, 'sf_local193': 0, 'sf_local194': 0, 'sf_local195': 0, 'sf_local196': 0, 'sf_local197': 1, 'sf_local198': 1, 'sf_local199': 1, 'sf_local201': 0, 'sf_local202': 0, 'sf_local209': 0, 'sf_local210': 1, 'sf_local212': 1, 'sf_local218': 1, 'sf_local219': 0, 'sf_local220': 0, 'sf_local221': 1, 'sf_local228': 0, 'sf_local229': 0, 'sf_local230': 0, 'sf_local244': 1, 'sf_local253': 0, 'sf_local258': 0, 'sf_local259': 0, 'sf_local262': 0, 'sf_local263': 0, 'sf_local264': 0, 'sf_local269': 0, 'sf_local270': 0, 'sf_local272': 0, 'sf_local273': 0, 'sf_local274': 1, 'sf_local277': 0, 'sf_local279': 0, 'sf_local283': 0, 'sf_local284': 1, 'sf_local285': 0, 'sf_local286': 0, 'sf_local297': 0, 'sf_local298': 0, 'sf_local299': 0, 'sf_local300': 0, 'sf_local301': 1, 'sf_local302': 0, 'sf_local309': 1, 'sf_local310': 0, 'sf_local311': 0, 'sf_local329': 1, 'sf_local330': 0, 'sf_local331': 0, 'sf_local335': 0, 'sf_local336': 0, 'sf_local344': 0, 'sf_local354': 0, 'sf_local355': 0, 'sf_local356': 0, 'sf_local358': 0, 'sf_local360': 0}
current_ashwin = {'sf009': 0, 'sf013': 0, 'sf_bq005': 0, 'sf_bq014': 0, 'sf_bq022': 1, 'sf_bq025': 1, 'sf_bq027': 0, 'sf_bq029': 0, 'sf_bq035': 0, 'sf_bq036': 0, 'sf_bq039': 0, 'sf_bq040': 0, 'sf_bq041': 0, 'sf_bq059': 0, 'sf_bq060': 1, 'sf_bq076': 0, 'sf_bq077': 1, 'sf_bq080': 0, 'sf_bq081': 0, 'sf_bq084': 0, 'sf_bq091': 1, 'sf_bq092': 0, 'sf_bq098': 0, 'sf_bq104': 0, 'sf_bq110': 0, 'sf_bq116': 0, 'sf_bq118': 0, 'sf_bq121': 0, 'sf_bq123': 0, 'sf_bq126': 1, 'sf_bq130': 0, 'sf_bq135': 1, 'sf_bq136': 0, 'sf_bq160': 0, 'sf_bq167': 0, 'sf_bq169': 0, 'sf_bq171': 1, 'sf_bq172': 1, 'sf_bq180': 0, 'sf_bq185': 0, 'sf_bq187': 0, 'sf_bq188': 0, 'sf_bq189': 0, 'sf_bq192': 0, 'sf_bq193': 0, 'sf_bq195': 0, 'sf_bq197': 0, 'sf_bq199': 0, 'sf_bq203': 0, 'sf_bq204': 1, 'sf_bq211': 0, 'sf_bq212': 1, 'sf_bq218': 0, 'sf_bq225': 0, 'sf_bq228': 1, 'sf_bq229': 0, 'sf_bq234': 0, 'sf_bq235': 1, 'sf_bq247': 1, 'sf_bq248': 0, 'sf_bq249': 0, 'sf_bq252': 1, 'sf_bq255': 1, 'sf_bq256': 0, 'sf_bq258': 0, 'sf_bq259': 0, 'sf_bq260': 0, 'sf_bq261': 0, 'sf_bq263': 0, 'sf_bq264': 0, 'sf_bq265': 0, 'sf_bq266': 0, 'sf_bq271': 0, 'sf_bq272': 0, 'sf_bq273': 0, 'sf_bq279': 0, 'sf_bq280': 1, 'sf_bq281': 0, 'sf_bq283': 0, 'sf_bq284': 1, 'sf_bq293': 0, 'sf_bq294': 0, 'sf_bq295': 0, 'sf_bq301': 0, 'sf_bq303': 0, 'sf_bq304': 0, 'sf_bq305': 0, 'sf_bq306': 0, 'sf_bq307': 0, 'sf_bq308': 0, 'sf_bq309': 0, 'sf_bq310': 1, 'sf_bq327': 0, 'sf_bq328': 0, 'sf_bq331': 0, 'sf_bq333': 0, 'sf_bq339': 0, 'sf_bq341': 0, 'sf_bq342': 0, 'sf_bq348': 0, 'sf_bq363': 0, 'sf_bq375': 1, 'sf_bq377': 1, 'sf_bq380': 0, 'sf_bq393': 0, 'sf_bq395': 0, 'sf_bq398': 1, 'sf_bq400': 0, 'sf_bq402': 0, 'sf_bq406': 0, 'sf_bq411': 0, 'sf_bq412': 0, 'sf_bq413': 0, 'sf_bq415': 0, 'sf_bq432': 0, 'sf_bq442': 0, 'sf_bq444': 1, 'sf_local003': 0, 'sf_local004': 0, 'sf_local009': 1, 'sf_local015': 0, 'sf_local019': 1, 'sf_local020': 0, 'sf_local021': 0, 'sf_local022': 0, 'sf_local023': 0, 'sf_local024': 0, 'sf_local025': 0, 'sf_local030': 0, 'sf_local031': 1, 'sf_local034': 0, 'sf_local035': 0, 'sf_local039': 1, 'sf_local041': 1, 'sf_local049': 1, 'sf_local050': 0, 'sf_local054': 0, 'sf_local056': 0, 'sf_local058': 1, 'sf_local059': 1, 'sf_local061': 0, 'sf_local062': 0, 'sf_local063': 0, 'sf_local065': 1, 'sf_local066': 0, 'sf_local068': 0, 'sf_local074': 1, 'sf_local075': 0, 'sf_local078': 1, 'sf_local096': 0, 'sf_local097': 0, 'sf_local098': 0, 'sf_local100': 0, 'sf_local130': 0, 'sf_local131': 0, 'sf_local132': 0, 'sf_local141': 1, 'sf_local152': 0, 'sf_local156': 0, 'sf_local163': 0, 'sf_local167': 0, 'sf_local168': 0, 'sf_local169': 0, 'sf_local170': 0, 'sf_local171': 0, 'sf_local193': 0, 'sf_local194': 0, 'sf_local198': 0, 'sf_local199': 1, 'sf_local209': 0, 'sf_local212': 1, 'sf_local219': 0, 'sf_local229': 1, 'sf_local230': 0, 'sf_local244': 1, 'sf_local262': 0, 'sf_local263': 0, 'sf_local264': 0, 'sf_local269': 0, 'sf_local272': 0, 'sf_local273': 0, 'sf_local283': 0, 'sf_local284': 1, 'sf_local286': 0, 'sf_local297': 0, 'sf_local298': 0, 'sf_local299': 0, 'sf_local302': 0, 'sf_local310': 0, 'sf_local311': 0, 'sf_local329': 0, 'sf_local330': 0, 'sf_local335': 0, 'sf_local354': 0, 'sf_local356': 0, 'sf_local358': 0, 'sf_local360': 0}
instance_ids = [instance_id for instance_id in instance_ids if instance_id.split(".")[0] not in current_ashwin or current_ashwin[instance_id.split(".")[0]] == 0]
instance_ids = [instance_id + ".pkl" for instance_id in instance_ids if instance_id.split(".")[0] not in minghang or minghang[instance_id.split(".")[0]] == 0]
print(len(instance_ids))

sql_dump_ids = list(os.listdir("sql_dump"))
instance_ids = [instance_id for instance_id in instance_ids if instance_id in sql_dump_ids]
# instance_ids = ['sf_local075', 'sf_local285', 'sf_local064', 'sf_local299', 'sf_local157', 'sf_local300']#['sf_local297', 'sf_local302', 'sf_local156', 'sf_local298', 'sf_local074', 'sf_local077', 'sf_local078', 'sf_local301', 'sf_local284'] +  ['sf_local075', 'sf_local285', 'sf_local064', 'sf_local299', 'sf_local157', 'sf_local300']
# print(len(instance_ids))
# Group instance IDs by db_id
db_instance_map = {}
for instance_id in instance_ids:
    instance_id = instance_id.split(".")[0]
    db_id = instance_metadata[instance_id]["db_id"]
    if db_id not in db_instance_map:
        db_instance_map[db_id] = []
    db_instance_map[db_id].append(instance_id)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H4("🔍 Choose Database"),
            dcc.Dropdown(
                id="db-dropdown",
                options=[{"label": db, "value": db} for db in sorted(db_instance_map.keys())],
                value=sorted(db_instance_map.keys())[0],
                clearable=False,
                style={"width": "100%"}
            ),
            html.H4("🔍 Choose Instance ID"),
            dcc.Dropdown(
                id="instance-id-dropdown",
                options=[],
                value=None,
                clearable=False,
                style={"width": "100%"}
            ),
            html.H4("📝 Comments"),
            dbc.Card([
                dbc.CardHeader("Comments"),
                dbc.CardBody([
                    dcc.Textarea(
                        id="comment-textarea",
                        value="",
                        style={"width": "100%", "height": 100},
                    ),
                    html.Button("Save Comment", id="save-comment-button", n_clicks=0)
                ])
            ], style={"margin-top": "20px"})
        ], width=3),  # Sidebar
        dbc.Col([
            loading_component
        ], width=9),  # Main Content
    ])
], fluid=True)

# Callback to update instance ID dropdown based on selected database
@app.callback(
    Output("instance-id-dropdown", "options"),
    Output("instance-id-dropdown", "value"),
    Input("db-dropdown", "value")
)
def update_instance_dropdown(selected_db):
    instance_options = [{"label": i, "value": i} for i in sorted(db_instance_map[selected_db])]
    return instance_options, instance_options[0]["value"]

# Callback to update content based on selected instance ID
@app.callback(
    Output("main-content", "children"),
    Output("comment-textarea", "value"),
    Input("instance-id-dropdown", "value")
)
def update_content(instance_id):
    # Load metadata
    metadata = get_info_instance_id(instance_id)
    history_messages, registered_json, instruction, predicted_obs, indi_sqls, tables, last_major_sql, final_exec, indi_sqls_exec, gold_exec = metadata

    # Load comments
    comments = load_comments(instance_id)

    # Instruction Section
    instruction_section = dbc.Card([
        dbc.CardHeader("Instruction"),
        dbc.CardBody(html.P(instruction, className="text-danger"))
    ], style={"margin-bottom": "20px"})

    # Gold Execution Results
    gold_exec_section = dbc.Card([
        dbc.CardHeader("Gold Execution Results"),
        dbc.CardBody([
            dbc.Table.from_dataframe(gold_exec, striped=True, bordered=True, hover=True) if gold_exec is not None and not gold_exec.empty else html.P("No gold execution results available.")
        ])
    ], style={"margin-bottom": "20px"})
    
    cte_gpt_feedback = {}
    for cte in tables:
        cte_gpt_feedback[cte] = []

    cte_index = 0
    last_justify = ""
    for message in history_messages[3:]:
        if message["role"] == "assistant":
            text = message["content"][0]["text"]
            if "EXEC_SQL" in text:
                continue
            if cte_index == len(tables):
                last_justify = text.split("Action")[0]
                break
            if "REGISTER_CTE" in text:
                cte_gpt_feedback[tables[cte_index]].append(text.split("Action")[0])
                cte_index += 1
            else:
                cte_gpt_feedback[tables[cte_index]].append(text.split("Action")[0])



    # Individual SQL Queries
    print(registered_json)
    sql_sections = []
    for idx, (sql, exec_result) in enumerate(zip(indi_sqls, indi_sqls_exec)):

        # Create table and column details section
        tooltips = []
        sql_with_tooltips = []
        sql = sql.replace("\\n", "\n")
        for line in sql.splitlines():
            for part in line.split():
                for table in registered_json:
                    if table in sql or ".".join(['"' + part2 + '"' for part2 in table.split(".")]) in sql:
                        columns = registered_json[table]
                        for col in columns:
                            if col['column_name'] in part:
                                tooltip_id = f"tooltip-{instance_id}-{idx}-{col['column_name']}"
                                tooltips.append(
                                    dbc.Tooltip(
                                        [
                                            html.H6(f"Column Name: {col['column_name']}"),
                                            html.P(f"Type: {col['type']}"),
                                            html.P(f"Description: {col['description']}"),
                                            html.P(f"Sample Values: {col.get('sample_values', 'N/A')}"),
                                            html.P(f"Distinct Values: {col.get('distinct_values', 'N/A')}")
                                        ],
                                        target=tooltip_id,
                                        placement="top"
                                    )
                                )
                                sql_with_tooltips.append(html.Span(part, id=tooltip_id, style={"textDecoration": "underline", "cursor": "pointer"}))
                                break
                        else:
                            continue
                        break
                else:
                    sql_with_tooltips.append(part)
                sql_with_tooltips.append(" ")
            sql_with_tooltips.append(html.Br())

        try:
            exec_result_df = pd.read_csv(StringIO(exec_result), header=None)
        except:
            exec_result_df = None
        sql_sections.append(dbc.Card([
            dbc.CardHeader(f"Query for {tables[idx]}"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.P(sql_with_tooltips), width=6),
                    dbc.Col(html.P("\n".join(cte_gpt_feedback[tables[idx]])), width=6)
                ]),
                # html.P(sql_with_tooltips),
                dbc.Table.from_dataframe(exec_result_df, striped=True, bordered=True, hover=True) if exec_result_df is not None else html.P("No execution results available."),
                *tooltips
            ])
        ]))
    indi_sql_section = html.Div(sql_sections)

    # Last Major SQL Query
    try:
        final_exec_df = pd.read_csv(StringIO(final_exec), header=None)
    except:
        final_exec_df = None
    major_sql_section = dbc.Card([
        dbc.CardHeader("Last Major SQL Query"),
        dbc.CardBody([
            dbc.Row([
                    dbc.Col(html.P(f"SQL Query: {last_major_sql}"), width=6),
                    dbc.Col(html.P(last_justify), width=6)
                ]),
            dbc.Table.from_dataframe(final_exec_df, striped=True, bordered=True, hover=True) if final_exec_df is not None else html.P("No execution results available.")
        ])
    ])
                
    return html.Div([
        instruction_section,
        html.H5("🔗 SQL Queries"),
        indi_sql_section,
        html.H5("🔍 Last Major SQL Query"),
        major_sql_section,
        gold_exec_section
    ],
        id=f"instance-content-{instance_id}",
        key=f"refresh-{instance_id}"  # Forces DOM refresh
        ), comments

# Callback to save comments
@app.callback(
    Output("save-comment-button", "children"),
    Input("save-comment-button", "n_clicks"),
    State("instance-id-dropdown", "value"),
    State("comment-textarea", "value")
)
def save_comment(n_clicks, instance_id, comment):
    if n_clicks > 0:
        comments_dir = "comments"
        os.makedirs(comments_dir, exist_ok=True)
        comments_file = os.path.join(comments_dir, f"{instance_id}.txt")
        with open(comments_file, "w") as f:
            f.write(comment)
        return "Comment Saved"
    return "Save Comment"

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
