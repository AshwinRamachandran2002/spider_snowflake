#coding=utf8
import re
from dataclasses import dataclass, field
from typing import Optional, Any, Union, List, Dict
from abc import ABC

def remove_quote(text: str) -> str:
    """ 
    If the text is wrapped by a pair of quote symbols, remove them.
    In the middle of the text, the same quote symbol should remove the '/' escape character.
    """
    for quote in ['"', "'", "`"]:
        if text.startswith(quote) and text.endswith(quote):
            text = text[1:-1]
            text = text.replace(f"\\{quote}", quote)
            break
    return text.strip()


@dataclass
class Action(ABC):
    
    action_type: str = field(
        repr=False,
        metadata={"help": 'type of action, e.g. "exec_code", "create_file", "terminate"'}
    )


    @classmethod
    def get_action_description(cls) -> str:
        return """
Action: action format
Description: detailed definition of this action type.
Usage: example cases
Observation: the observation space of this action type.
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional[Any]:
        raise NotImplementedError

@dataclass
class PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(Action):
    action_type: str = field(default="predicted_column_names_and_rows", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    column_names: List[str] = field(metadata={"help": 'List of column names'})
    example_rows: List[List[str]] = field(metadata={"help": 'List of example rows'})
    number_of_rows: str = field(metadata={"help": 'Number of rows predicted'})
    depends_on: str = field(default=None, metadata={"help": 'Dependency of the number of rows predicted'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS Action
* Signature: PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(column_names=["column_name1", "column_name2"], example_rows=["example_row1_column1", "example_row1_column2"], number_of_rows="CANNOT_BE_PREDICTED", depends_on="Dependency of the number of rows")
* Description: Predicts the column names and example rows based on the SQL query. Predicts the number of rows based on the query execution if it can be predicted.
Think very carefully if the rows can be predicted. If not, then what might it depend on.
* Examples:
  - Example1: PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(column_names=["collector_group", "debt_amount"], example_rows=["debt_collector", "1000"], number_of_rows="10", depends_on="Since the question asks for within each category, it is 10")
  - Example1: PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(column_names=["id"], example_rows=["2"], number_of_rows="CANNOT_BE_PREDICTED", depends_on="Number of rows depends on the nmber of distinct people since the question asks for each person")
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS']:
        pattern = r'''
            PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS\(
                \s*column_names\s*=\s*\[\s*(?P<columns>(?:(?:'[^']*'|"[^"]*"|[^,])*?)\s*(?:,\s*(?:'[^']*'|"[^"]*"|[^,])*?)*)\s*\]
                \s*,\s*example_rows\s*=\s*\[\s*(?P<rows>(?:(?:'[^']*'|"[^"]*"|[^,])*?)\s*(?:,\s*(?:'[^']*'|"[^"]*"|[^,])*?)*)\s*\]
                \s*,\s*number_of_rows\s*=\s*(?P<number_of_rows>.*?)
                \s*,\s*depends_on\s*=\s*(?P<depends_on>.*?)
                \s*\)
        '''
        # Use re.VERBOSE to allow multiline and commented pattern
        match = re.search(pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            column_names_to_inspect_raw = match.group('columns')
            column_names_to_inspect = [col.strip() for col in column_names_to_inspect_raw.split(',')]   

            example_rows_raw = match.group('rows')
            example_rows = [col.strip() for col in example_rows_raw.split(',')]
            
            number_of_rows = match.group('number_of_rows').strip()
            
            depends_on = match.group('depends_on').strip()
            return cls(column_names=column_names_to_inspect, example_rows=example_rows, number_of_rows=number_of_rows, depends_on=depends_on)
        return None


    def __repr__(self) -> str:
        column_names_str = ', '.join([f'"{col}"' for col in self.column_names])
        example_rows_str = ', '.join([f'"{col}"' for col in self.example_rows])
        return f'PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(column_names=[{column_names_str}], example_rows=[{example_rows_str}], number_of_rows="{self.number_of_rows}", depends_on="{self.depends_on}")'


@dataclass
class INSPECT_MARKDOWN(Action):
    action_type: str = field(default="inspect_data_in_markdown", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    markdown_file_path: str = field(metadata={"help": 'markdown file path'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## INSPECT_MARKDOWN Action
* Signature: INSPECT_MARKDOWN(markdown_file_path="markdown_name.md")
* Description: Inspects the markdown file.
* Examples:
  - Example1: INSPECT_MARKDOWN(markdown_file_path="HOUSEHOLD/COLLECTION.md")
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['INSPECT_MARKDOWN']:
        pattern = r'''
            INSPECT_MARKDOWN\(
                \s*markdown_file_path\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<markdown_file_path>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                \s*\)
        '''
        # Use re.VERBOSE to allow multiline and commented pattern
        match = re.search(pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            markdown_file_path = match.group('markdown_file_path')
            markdown_file_path = markdown_file_path.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(markdown_file_path=markdown_file_path)
        return None


    def __repr__(self) -> str:
        return f'INSPECT_MARKDOWN(markdown_file_path="{self.markdown_file_path}")'

@dataclass
class SNOWFLAKE_READ_SCHEMA_FROM_DDL(Action):
    action_type: str = field(default="inspect_data_in_ddl_csv_file", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    ddl_file_path: str = field(metadata={"help": 'DDL csv file path of the schema'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_READ_SCHEMA_FROM_DDL Action
* Signature: SNOWFLAKE_READ_SCHEMA_FROM_DDL(ddl_file_path="database_name/schema_name/DDL.csv")
* Description: Inspects the CSV file of the DDL schemas on Snowflake and retrieves the table and column names.
* Examples:
  - Example1: SNOWFLAKE_READ_SCHEMA_FROM_DDL(ddl_file_path="HOUSEHOLD/HOUSE_GROUP/DDL.csv")
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_READ_SCHEMA_FROM_DDL']:
        pattern = r'''
            SNOWFLAKE_READ_SCHEMA_FROM_DDL\(
                \s*ddl_file_path\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<ddl_file_path>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                \s*\)
        '''
        # Use re.VERBOSE to allow multiline and commented pattern
        match = re.search(pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            ddl_file_path = match.group('ddl_file_path')
            ddl_file_path = ddl_file_path.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(ddl_file_path=ddl_file_path)
        return None

    def __repr__(self) -> str:
        return f'SNOWFLAKE_READ_SCHEMA_FROM_DDL(ddl_file_path="{self.ddl_file_path}")'

@dataclass
class SNOWFLAKE_JUSTIFY_DDL_RELEVANCE(Action):
    action_type: str = field(default="justify_json_file", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    ddl_reason: list[str] = field(metadata={"help": 'dictionary containing the reason for the relevance of each ddl file'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_JUSTIFY_DDL_RELEVANCE Action
* Signature: SNOWFLAKE_JUSTIFY_DDL_RELEVANCE(ddl_reason=[{"ddl_path": "database_name/schema_name/DDL.csv", "desciption": "What is purpose of database", "relevance_reason': "Reason for the relevance of the ddl file", "is_relevant": "True/False"}])
* Description: Justifies the relevance of the ddl files based on the provided reasons and provides descriptions for each ddl file.
* Examples:
  - Example1: SNOWFLAKE_JUSTIFY_DDL_RELEVANCE(ddl_reason=[{"ddl_path": "HOUSEHOLD/HOUSE_GROUP/DDL.csv", "desciption": "This DDL contains information about the houses in the household", "relevance_reason": "HOUSE may contain information about doors as asked in the question.", "is_relevant": "True"}, {"ddl_path": "HOUSEHOLD/COLLECTION/DDL.csv", "desciption": "This table contains information about the collection in the household", "relevance_reason": "COLLECTION may contain information about the collection as asked in the question.", "is_relevant": "True"}])
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_JUSTIFY_DDL_RELEVANCE']:
        main_pattern = r'''
            SNOWFLAKE_JUSTIFY_DDL_RELEVANCE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        ddl_path = re.findall(r'"ddl_path":\s*"([^"]+?)"', text)
        desciption = re.findall(r'"desciption":\s*"([^"]+?)"', text)
        relevance_reason = re.findall(r'"relevance_reason":\s*"([^"]+?)"', text)
        is_relevant = re.findall(r'"is_relevant":\s*(.+?)\s*\}', text)
        
        clause_tuple = []
        for i in range(len(ddl_path)):
            if "true" in is_relevant[i].lower():
                clause_tuple.append({"ddl_path": ddl_path[i], "desciption": desciption[i], "relevance_reason": relevance_reason[i], "is_relevant": True})
        return cls(ddl_reason=clause_tuple)

    def __repr__(self) -> str:
        ddl_reason_str = ', '.join([f'{{"ddl_path": "{col["ddl_path"]}", "desciption": "{col["desciption"]}", "relevance_reason": "{col["relevance_reason"]}", "is_relevant": "{col["is_relevant"]}"}}' for col in self.ddl_reason])
        return f'SNOWFLAKE_JUSTIFY_DDL_RELEVANCE(ddl_reason={ddl_reason_str})'


@dataclass
class SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE(Action):
    action_type: str = field(default="justify_json_file", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    json_reason: list[str] = field(metadata={"help": 'dictionary containing the reason for the relevance of each JSON file'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE Action
* Signature: SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE(json_reason=[{"json_path": "database_name/schema_name/table_name.json", "desciption": "What is purpose of table in the database", "relevance_reason': "Reason for the relevance of the JSON file", "is_relevant": "True/False"}])
* Description: Justifies the relevance of the JSON files based on the provided reasons and provides descriptions for each JSON file.
* Examples:
  - Example1: SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE(json_reason=[{"json_path": "HOUSEHOLD/HOUSE_GROUP/HOUSE.json", "desciption": "This table contains information about the houses in the household", "relevance_reason": "HOUSE may contain information about doors as asked in the question.", "is_relevant": "True"}, {"json_path": "HOUSEHOLD/HOUSE_GROUP/COLLECTION.json", "desciption": "This table contains information about the collection in the household", "relevance_reason": "COLLECTION may contain information about the collection as asked in the question.", "is_relevant": "True"}])
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE']:
        main_pattern = r'''
            SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        json_path = re.findall(r'"json_path":\s*"([^"]+?)"', text)
        desciption = re.findall(r'"desciption":\s*"([^"]+?)"', text)
        relevance_reason = re.findall(r'"relevance_reason":\s*"([^"]+?)"', text)
        is_relevant = re.findall(r'"is_relevant":\s*(.+?)\s*\}', text)
        
        clause_tuple = []
        for i in range(len(json_path)):
            if "true" in is_relevant[i].lower():
                clause_tuple.append({"json_path": json_path[i], "desciption": desciption[i], "relevance_reason": relevance_reason[i], "is_relevant": True})
        return cls(json_reason=clause_tuple)

    def __repr__(self) -> str:
        json_reason_str = ', '.join([f'{{"json_path": "{col["json_path"]}", "desciption": "{col["desciption"]}", "relevance_reason": "{col["relevance_reason"]}", "is_relevant": "{col["is_relevant"]}"}}' for col in self.json_reason])
        return f'SNOWFLAKE_JUSTIFY_JSON_FILE_RELEVANCE(json_reason={json_reason_str})'


@dataclass
class SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE(Action):
    action_type: str = field(default="justify_json_file", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    json_reason: list[str] = field(metadata={"help": 'dictionary containing the reason for the relevance of only relevant JSON file'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE Action
* Signature: SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE(json_reason=[{"json_path": "database_name/schema_name/table_name.json"}])
* Description: Justifies the relevance of the JSON files.
* Examples:
  - Example1: SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE(json_reason=[{"json_path": "HOUSEHOLD/HOUSE_GROUP/HOUSE.json"}, {"json_path": "HOUSEHOLD/HOUSE_GROUP/COLLECTION.json"}])
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE']:
        main_pattern = r'''
            SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        json_path = re.findall(r'"json_path":\s*"([^"]+?)"', text)

        clause_tuple = []
        for i in range(len(json_path)):
            clause_tuple.append({"json_path": json_path[i], "desciption": "", "relevance_reason": "", "is_relevant": True})
        return cls(json_reason=clause_tuple)

    def __repr__(self) -> str:
        json_reason_str = ', '.join([f'{{"json_path": "{col["json_path"]}", "desciption": "{col["desciption"]}", "relevance_reason": "{col["relevance_reason"]}", "is_relevant": "{col["is_relevant"]}"}}' for col in self.json_reason])
        return f'SNOWFLAKE_JUSTIFY_RELEVANT_JSON_FILE_RELEVANCE(json_reason={json_reason_str})'

@dataclass
class SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON(Action):
    action_type: str = field(default="inspect_data_in_json_file_of_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    json_file_path: str = field(metadata={"help": 'json file path of the table schema'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON Action
* Signature: SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON(json_file_path="database_name/schema_name/table_name.json")
* Description: Inspects the JSON file of the table schema on Snowflake and retrieves the column names.
* Examples:
  - Example1: SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON(json_file_path="HOUSEHOLD/HOUSE_GROUP/COLLECTION.json")
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON']:
        pattern = r'''
            SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON\(
                \s*json_file_path\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<json_file_path>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                \s*\)
        '''
        # Use re.VERBOSE to allow multiline and commented pattern
        match = re.search(pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            json_file_path = match.group('json_file_path')
            json_file_path = json_file_path.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(json_file_path=json_file_path)
        return None


    def __repr__(self) -> str:
        return f'SNOWFLAKE_READ_TABLE_SCHEMA_FROM_JSON(json_file_path="{self.json_file_path}")'

@dataclass
class SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES(Action):
    action_type: str = field(default="justify_json_file", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    table_reason: list[str] = field(metadata={"help": 'dictionary containing the reason for the relevance of each table'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES Action
* Signature: SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES(table_reason=[{"table_name": "database_name.schema_name.table_name", "desciption": "What is purpose of table in the database", "relevance_reason': "Reason for the relevance of the JSON file", "is_relevant": "True/False"}])
* Description: Justifies the relevance of the Tables based on the provided reasons and provides descriptions for each table.
* Examples:
  - Example1: SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES(table_reason=[{"table_name": "HOUSEHOLD.HOUSE_GROUP.HOUSE", "desciption": "This table contains information about the houses in the household", "relevance_reason": "HOUSE has information about doors as asked in the question.", "is_relevant": "True"}, {"table_name": "HOUSEHOLD.HOUSE_GROUP.COLLECTION", "desciption": "This table contains information about the collection in the household", "relevance_reason": "COLLECTION may contain information about the collection as asked in the question.", "is_relevant": "True"}])
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES']:
        main_pattern = r'''
            SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        table_name = re.findall(r'"table_name":\s*"([^"]+?)"', text)
        desciption = re.findall(r'"desciption":\s*"([^"]+?)"', text)
        relevance_reason = re.findall(r'"relevance_reason":\s*"([^"]+?)"', text)
        is_relevant = re.findall(r'"is_relevant":\s*(.+?)\s*\}', text)
        
        clause_tuple = []
        for i in range(len(table_name)):
            if "true" in is_relevant[i].lower():
                clause_tuple.append({"table_name": table_name[i], "desciption": desciption[i], "relevance_reason": relevance_reason[i], "is_relevant": True})
        return cls(table_reason=clause_tuple)

    def __repr__(self) -> str:
        table_reason_str = ', '.join([f'{{"table_name": "{col["table_name"]}", "desciption": "{col["desciption"]}", "relevance_reason": "{col["relevance_reason"]}", "is_relevant": "{col["is_relevant"]}"}}' for col in self.table_reason])
        return f'SNOWFLAKE_REGISTER_RELEVANCE_OF_TABLES(table_reason={table_reason_str})'

@dataclass
class SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE(Action):
    action_type: str = field(default="inspect__distinct_column_data_in_snowflake_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    table_name: str = field(metadata={"help": 'table name'})
    column_justify: list[dict] = field(metadata={"help": 'list of dict of relevant column names and why they are relevant in the table'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE Action
* Signature: SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE(table_name="table_name", column_justify=[{"column_name": "your_column_name1", "desciption": "What is purpose of this column in table",  "relevance_reason': "Reason for the relevance of the column", "is_relevant": "True/False"}, {"column_name": "your_column_name2", "desciption": "What is purpose of this column in table",  "relevance_reason': "Reason for the relevance of the column", "is_relevant": "True/False"}])
* Description: Register all columns for a table on Snowflake. Include the column names and the reason why they are relevant or why they are not in the table with a description.
* Examples:
  - Example1: SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE(table_name="HOUSEHOLD.HOUSE_GROUP.COLLECTION", column_justify=[{"column_name": "collector_group", "desciption": "identifies what is the name of the collector group", "relevance_reason": "task does not involve any grouping of collectors", "is_relevant": "False"}, {"column_name": "dome_id", "desciption": "dome_id is the id of the dome", "relevance_reason": "question requires id to select correct architectures", "is_relevant": "True"}])
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE']:
        main_pattern = r'''
            SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        
        table_names = re.findall(r'table_name=\s*"([^"]+?)"', text)
        column_names = re.findall(r'"column_name":\s*"([^"]+?)"', text)  
        reasons = re.findall(r'"relevance_reason":\s*"([^"]+?)"', text)
        is_relevant = re.findall(r'"is_relevant":\s*(.+?)\s*\}', text)

        # if len(is_relevant) != len(column_names):
            # exit(0)
        column_justify = []
        for i in range(len(column_names)):
            if "true" in is_relevant[i].lower():            
                column_justify.append({"column_name": column_names[i], "reason": ""})

        return cls(table_name=table_names[0], column_justify=column_justify)

    def __repr__(self) -> str:
        table_column_justify_str = ', '.join([f'{{"column_name": "{col["column_name"]}"}}' for col in self.column_justify])
        return f'SNOWFLAKE_REGISTER_RELEVANCE_OF_ALL_COLUMNS_FOR_TABLE(table_name="{self.table_name}", column_justify=[{table_column_justify_str}])'



@dataclass
class SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE(Action):
    action_type: str = field(default="inspect__distinct_column_data_in_snowflake_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    table_name: str = field(metadata={"help": 'table name'})
    column_justify: list[dict] = field(metadata={"help": 'list of dict of relevant column names'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE Action
* Signature: SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE(table_name="table_name", column_justify=[{"column_name": "your_column_name1"}])
* Description: Register relevant columns for a table on Snowflake
* Examples:
  - Example1: SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE(table_name="HOUSEHOLD.HOUSE_GROUP.COLLECTION", column_justify=[{"column_name": "dome_id"}])
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE']:
        main_pattern = r'''
            SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        table_names = re.findall(r'table_name=\s*"([^"]+?)"', text)
        column_names = re.findall(r'"column_name":\s*"([^"]+?)"', text)  

        column_justify = []
        for i in range(len(column_names)):
            column_justify.append({"column_name": column_names[i], "reason": ""})

        return cls(table_name=table_names[0], column_justify=column_justify)

    def __repr__(self) -> str:
        table_column_justify_str = ', '.join([f'{{"column_name": "{col["column_name"]}", "relevance_reason": "{col["reason"]}"}}' for col in self.column_justify])
        return f'SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_TABLE(table_name="{self.table_name}", column_justify=[{table_column_justify_str}])'



@dataclass
class SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE(Action):
    action_type: str = field(default="inspect__distinct_column_data_in_snowflake_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    cte_name: str = field(metadata={"help": 'CTE name'})
    table_column_justify: list[dict] = field(metadata={"help": 'list of dict of relevant column names'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE Action
* Signature: SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTES(cte_column_justify=[{"cte_name": "your_cte_name", "column_justify" : [{"table_column_name": "your_table_name.your_column_name1", "relevance_reason": "Reason for the relevance of the column"}, {"table_column_name": "your_table_name.your_column_name2", "relevance_reason": "Reason for the relevance of the column"}]}])
* Description: Register relevant columns for all CTES on Snowflake
* Examples:
  - Example1: SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTES(cte_column_justify=[{"cte_name": "CollectionTable", "column_justify" : [{"table_column_name": "HOUSEHOLD.HOUSE_GROUP.COLLECTION.dome_id", "relevance_reason": "dome_id is required for CTE since it identifies domes for filter"}]})
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE']:
        main_pattern = r'''
            SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        return cls(cte_name="", table_column_justify=[{}])

    def __repr__(self) -> str:
        return f'SNOWFLAKE_REGISTER_RELEVANCE_OF_RELEVANT_COLUMNS_FOR_CTE(table_name="", column_justify=[])'



@dataclass
class SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN(Action):
    action_type: str = field(default="inspect__distinct_column_data_in_snowflake_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    clause_tuple: list[dict] = field(metadata={"help": 'list of tuples containing column name to inspect, condition type to use for pattern matching, keyword or pattern to match in the column, and table name to inspect'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN Action
* Signature: SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN(clause_tuple = [{"column_name":"column_name", "table_name":"table_name"}])
* Description: Find distinct values in the column of a table on Snowflake. Use this when you want to know what values are present in a column to use them in the conditional clause.
For every tuple provided, executes SELECT DISTINCT <column_name> FROM <table_name>
* Examples:
  - Example1: SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN(clause_tuple=[{"column_name":"collector_group", "table_name":"HOUSEHOLD.HOUSE_GROUP.COLLECTION"}, {"column_name":"dome_id", "table_name":"ADMINISTRATOR.DOME"}])
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN']:
        main_pattern = r'''
            SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        column_names = re.findall(r'"column_name":\s*"([^"]+?)"', text)  
        table_names = re.findall(r'"table_name":\s*"([^"]+?)"', text)
        clause_tuple = []
        for i in range(len(column_names)):
            clause_tuple.append({"column_name": column_names[i], "table_name": table_names[i]})
        return cls(clause_tuple=clause_tuple)

    def __repr__(self) -> str:
        clause_tuple_str = ', '.join([f'{{"column_name": "{col["column_name"]}", "table_name": "{col["table_name"]}"}}' for col in self.clause_tuple])
        return f'SNOWFLAKE_FIND_DISTINCT_VALUES_IN_THE_COLUMN(clause_tuple=[{clause_tuple_str}])'


@dataclass
class SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK(Action):
    action_type: str = field(default="inspect_data_in_snowflake_table", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    clause_tuple: list[dict] = field(metadata={"help": 'list of tuples containing column name to inspect, condition type to use for pattern matching, keyword or pattern to match in the column, and table name to inspect'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK Action
* Signature: SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK(clause_tuple = [{"column_name":"column_name", "condition_type":"ILIKE", "keyword_or_pattern":"pattern_to_match", "table_name":"table_name"}])
* Description: Execute SQLs based on given attributes to inspect data entries in database table on Snowflake.
For every tuple provided, executes SELECT DISTINCT <column_name> FROM <table_name> WHERE <column_name> <condition_type> <pattern_to_match>
Example of conditions:
    - column_name IN ("value1", "value2") -> {"column_name": "column_name", "condition_type": "IN", "keyword_or_pattern": "('value1', 'value2')", "table_name": "table_name"}
    - column_name ILIKE "%pattern%" -> {"column_name": "column_name", "condition_type": "ILIKE", "keyword_or_pattern": "'%pattern%'", "table_name": "table_name"}
    - column_name = "value" -> {"column_name": "column_name", "condition_type": "=", "keyword_or_pattern": "'value'", "table_name": "table_name"}
    - column_name > 10 -> {"column_name": "column_name", "condition_type": ">", "keyword_or_pattern": "10", "table_name": "table_name"}
    - column_name < 10 -> {"column_name": "column_name", "condition_type": "<", "keyword_or_pattern": "10", "table_name": "table_name"}
    - column_name >= 10 -> {"column_name": "column_name", "condition_type": ">=", "keyword_or_pattern": "10", "table_name": "table_name"}
    - column_name <= 10 -> {"column_name": "column_name", "condition_type": "<=", "keyword_or_pattern": "10", "table_name": "table_name"}
    - column_name != "value" -> {"column_name": "column_name", "condition_type": "!=", "keyword_or_pattern": "'value'", "table_name": "table_name"}
    - column_name IS NULL -> {"column_name": "column_name", "condition_type": "IS NULL", "keyword_or_pattern": "", "table_name": "table_name"}
    - column_name IS NOT NULL -> {"column_name": "column_name", "condition_type": "IS NOT NULL", "keyword_or_pattern": "", "table_name": "table_name"}
    - column_name BETWEEN 10 AND 20 -> {"column_name": "column_name", "condition_type": "BETWEEN", "keyword_or_pattern": "(10, 20)", "table_name": "table_name"}
    - column_name NOT BETWEEN 10 AND 20 -> {"column_name": "column_name", "condition_type": "NOT BETWEEN", "keyword_or_pattern": "(10, 20)", "table_name": "table_name"}
    - column_name LIKE "%pattern%" -> {"column_name": "column_name", "condition_type": "LIKE", "keyword_or_pattern": "'%pattern%'", "table_name": "table_name"}
    - column_name NOT LIKE "%pattern%" -> {"column_name": "column_name", "condition_type": "NOT LIKE", "keyword_or_pattern": "'%pattern%'", "table_name": "table_name"}
    - column_name IN (SELECT column_name FROM table_name WHERE column_name = "value") -> {"column_name": "column_name", "condition_type": "IN", "keyword_or_pattern": "(SELECT column_name FROM table_name WHERE column_name = 'value')", "table_name": "table_name"}
* Examples:
  - Example1: SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK(clause_tuple=[{"column_name":"collector_group", "condition_type":"ILIKE", "keyword_or_pattern":"'%debt%'", "table_name":"HOUSEHOLD.HOUSE_GROUP.COLLECTION"}, {"column_name":"dome_id", "condition_type":">:", "keyword_or_pattern":"'%joker%'", "table_name":"ADMINISTRATOR.DOME"}])
"""

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK']:
        main_pattern = r'''
            SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK\(
                (.+)
                \)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if not match:
            return None
        if '"' not in text:
            text = text.replace("'", '"')
        column_names = re.findall(r'"column_name":\s*"([^"]+?)"', text)  
        condition_types = re.findall(r'"condition_type":\s*"([^"]+?)"', text)
        keyword_or_patterns = re.findall(r'"keyword_or_pattern":\s*"([^"]*?)"', text)
        table_names = re.findall(r'"table_name":\s*"([^"]+?)"', text)
        clause_tuple = []
        # for i in range(len(column_names)):
        #     clause_tuple.append({"column_name": column_names[i], "condition_type": condition_types[i], "keyword_or_pattern": keyword_or_patterns[i], "table_name": table_names[i]})
        return cls(clause_tuple=clause_tuple)

    def __repr__(self) -> str:
        clause_tuple_str = ', '.join([f'{{"column_name": "{col["column_name"]}", "condition_type": "{col["condition_type"]}", "keyword_or_pattern": "{col["keyword_or_pattern"]}", "table_name": "{col["table_name"]}"}}' for col in self.clause_tuple])
        return f'SNOWFLAKE_CHECK_IF_CONDITIONAL_CLAUSES_WORK(clause_tuple=[{clause_tuple_str}])'



@dataclass
class SNOWFLAKE_EXEC_SQL(Action):
    action_type: str = field(default="execute_snowflake_SQL", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    sql_query: str = field(metadata={"help": 'SQL query to execute'})
    save_path: str = field(default=None, metadata={"help": 'path where the output CSV file is saved if is_save is True'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_EXEC_SQL Action
* Signature: SNOWFLAKE_EXEC_SQL(sql_query="SELECT your_column_1, your_column_2 FROM your_table_1", save_path="/workspace/output_file.csv")
* Description: Executes a SQL query on Snowflake. Please follow the syntax of action very very strictly
The `save_path` CSV must be under the `/workspace` directory. 
* Examples:
  - Example1: SNOWFLAKE_EXEC_SQL(sql_query="SELECT count(*) FROM DOMES.GROUP.SALES", save_path="/workspace/result.csv")
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_EXEC_SQL']:
        main_pattern = r'''
            SNOWFLAKE_EXEC_SQL\(
                \s*sql_query\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<sql_query>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                ,\s*save_path\s*=\s*
                    (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
                    (?P<save_path>.*?)
                    (?<!\\)(?P=quote_path)                     # Match closing quote for save_path
                \s*\)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            sql_query_raw = match.group('sql_query')
            sql_query = sql_query_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            # Extracting save_path if present
            save_path = ""
            if match.group('save_path'):
                save_path_raw = match.group('save_path')
                save_path = save_path_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(sql_query=sql_query, save_path=save_path)
        return None

    def __repr__(self) -> str:
        return f'SNOWFLAKE_EXEC_SQL(sql_query="{self.sql_query}", save_path="{self.save_path}")'



@dataclass
class SNOWFLAKE_MODIFY_CTE(Action):
    action_type: str = field(default="execute_snowflake_SQL", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    sql_query: str = field(metadata={"help": 'SQL query to execute'})
    cte_name: str = field(metadata={"help": 'CTE name'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_MODIFY_CTE Action
* Signature: SNOWFLAKE_MODIFY_CTE(sql_query="CTE1 AS (\nSELECT your_column_1, your_column_2\nFROM your_table_1\n)", cte_name="CTE1", reason="reason for modifying the CTE")
* Description: Executes a SQL query on Snowflake. Please follow the syntax of action very very strictly. The sql query must follow the same format of the CTE it is modifying.
* Examples:
  - Example1: SNOWFLAKE_MODIFY_CTE(sql_query="CTE1 AS (\nSELECT count(*)\nFROM DOMES.GROUP.SALES\n)", cte_name="CTE1", reason="CTE had error before")
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_MODIFY_CTE']:
        main_pattern = r'''
            SNOWFLAKE_MODIFY_CTE\(
                \s*sql_query\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<sql_query>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                ,\s*cte_name\s*=\s*
                (?P<quote_cte>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<cte_name>.*?)
                (?<!\\)(?P=quote_cte)                      # Match closing quote for sql_query
                ,\s*reason\s*=\s*
                    (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
                    (?P<save_path>.*?)
                    (?<!\\)(?P=quote_path) 
                \s*\)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            sql_query_raw = match.group('sql_query')
            sql_query = sql_query_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')
            
            # Extracting cte_name
            cte_name_raw = match.group('cte_name')
            cte_name = cte_name_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(sql_query=sql_query, cte_name=cte_name)
        return None

    def __repr__(self) -> str:
        return f'SNOWFLAKE_MODIFY_CTE(sql_query="{self.sql_query}", cte_name="{self.cte_name}")'





@dataclass
class SNOWFLAKE_Yes_NO(Action):
    action_type: str = field(default="execute_snowflake_SQL", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    question: str = field(metadata={"help": 'SQL query to execute'})

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_Yes_NO Action
* Signature: SNOWFLAKE_Yes_NO(question="The CTE has multiple rows. My reasoning is that it can have it. Is it correct?")
* Description: Ask a question for help.
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_MODIFY_CTE']:
        main_pattern = r'''
            SNOWFLAKE_Yes_NO\(
                \s*question\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<question>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                \s*\)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            sql_query_raw = match.group('question')
            sql_query = sql_query_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(question=sql_query)
        return None

    def __repr__(self) -> str:
        return f'SNOWFLAKE_Yes_NO(question="{self.question})'

@dataclass
class SNOWFLAKE_REGISTER_CTE(Action):
    action_type: str = field(default="execute_snowflake_SQL", init=False, repr=False, metadata={"help": 'type of action, c.f., "exec_sf_sql"'})
    sql_query: str = field(metadata={"help": 'SQL query to execute'})
    

    @classmethod
    def get_action_description(cls) -> str:
        return """
## SNOWFLAKE_REGISTER_CTE Action
* Signature: SNOWFLAKE_REGISTER_CTE(sql_query="CTE1 AS (\nSELECT your_column_1, your_column_2\nFROM your_table_1\n)", reason="reason for registering the CTE")
* Description: Executes a SQL query on Snowflake. Please follow the syntax of action very very strictly. The sql query must follow the same format of the CTE it is registering.
Add WITH only if the given CTE has it. 
* Examples:
  - Example1: SNOWFLAKE_REGISTER_CTE(sql_query="CTE1 AS (\nSELECT count(*)\nFROM DOMES.GROUP.SALES\n)", reason="CTE is required to filter the sales data")
"""
    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional['SNOWFLAKE_REGISTER_CTE']:
        main_pattern = r'''
            SNOWFLAKE_REGISTER_CTE\(
                \s*sql_query\s*=\s*
                (?P<quote_sql>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for sql_query
                (?P<sql_query>.*?)
                (?<!\\)(?P=quote_sql)                      # Match closing quote for sql_query
                ,\s*reason\s*=\s*
                    (?P<quote_path>\"\"\"|\"|\'\'\'|\'|\"\"\")  # Match opening quote for save_path
                    (?P<save_path>.*?)
                    (?<!\\)(?P=quote_path) 
                \s*\)
        '''
        match = re.search(main_pattern, text, flags=re.DOTALL | re.VERBOSE)
        if match:
            # Extracting sql_query
            sql_query_raw = match.group('sql_query')
            sql_query = sql_query_raw.replace(r'\"', '"').replace(r"\'", "'").replace('\\\\', '\\')

            return cls(sql_query=sql_query)
        return None

    def __repr__(self) -> str:
        return f'SNOWFLAKE_REGISTER_CTE(sql_query="{self.sql_query})'

@dataclass
class Terminate(Action):

    action_type: str = field(
        default="terminate",
        init=False,
        repr=False,
        metadata={"help": "terminate action representing the task is finished, or you think it is impossible for you to complete the task"}
    )

    output: Optional[str] = field(
        default=None,
        metadata={"help": "answer to the task or output file path or 'FAIL', if exists"}
    )

    code : str = field(
        default=''
    )

    @classmethod
    def get_action_description(cls) -> str:
        return """
## Terminate Action
* Signature: Terminate(output="literal_answer_or_output_path")
* Description: This action denotes the completion of the entire task and returns the output file/folder path of the answer. The answer must be saved in a CSV file, and you should tell me the file name.
* Examples:
  - Example1: Terminate(output="result.csv")
"""

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(output="{self.output}")'

    @classmethod
    def parse_action_from_text(cls, text: str) -> Optional[Action]:
        matches = re.findall(r'Terminate\(output=(.*?)\)', text, flags=re.DOTALL)
        if matches:
            output = matches[-1]
            return cls(output=remove_quote(output))
        return None
