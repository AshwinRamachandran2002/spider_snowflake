import json
import logging
import random
from typing import Any, Dict, Optional
import docker
import requests
import os
import ast
import tempfile
import platform
from spider_agent.agent.sql_template import LOCAL_SQL_TEMPLATE, BQ_GET_TABLES_TEMPLATE, BQ_GET_TABLE_INFO_TEMPLATE, BQ_SAMPLE_ROWS_TEMPLATE, BQ_EXEC_SQL_QUERY_TEMPLATE, SF_EXEC_SQL_QUERY_TEMPLATE
logger = logging.getLogger("spider_agent.pycontroller")


class PythonController:
    def __init__(self, container, work_dir="/workspace"):
        # self.container = container
        self.mnt_dir = f'/home/ashwin/Spider2/methods/spider-agent-snow/output/gpt-4o-agent-o1/{container}'#[mount['Source'] for mount in container.attrs['Mounts']][0]
        # print("mnt_dir:", self.mnt_dir)
        self.work_dir = self.mnt_dir


    def get_file(self, file_path: str):
        """
        Gets a file from the docker container.
        """    
        real_file_path = os.path.join(self.mnt_dir, file_path.replace("/workspace/",""))
        try:
            with open(real_file_path, 'r') as file:
                file_content = file.read()
        except FileNotFoundError:
            print("File not found:", file_path)
        except Exception as e:
            print("An error occurred:", str(e))
        return file_content

    def _wrap_with_print(self, command):
        # Parse the command as an AST (Abstract Syntax Tree)
        parsed_command = ast.parse(command.strip())

        # Check if the command contains an assignment node, print node, or import
        has_assignment = any(isinstance(node, ast.Assign) for node in ast.walk(parsed_command))
        has_print = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print' for node in ast.walk(parsed_command))
        has_import = any(isinstance(node, ast.Import) for node in ast.walk(parsed_command))
        is_assert = command.strip().startswith("assert")

        # Wrap the command with "print" if it's not an assignment and does not have a "print" statement
        if not any([has_assignment, has_print, has_import, is_assert]):
            return f"print({command})"
        else:
            return command
        
    def _input_multiline_function(self):
        lines = []
        while True:
            line = input(". ")
            if len(line) == 0:
                break
            lines.append(line)
        return "\n".join(lines)

    def execute_python_code(self, action: str) -> None:
        try:
            if action.strip().startswith("def "):
                function_definition = self._input_multiline_function()
                action = action + "\n" + function_definition
            else:
                action = self._wrap_with_print(action)
            logger.info(f"Command run: {action}")
            observation = self._execute_python_code(action)
        except Exception as err:
            observation = f"Error executing action: {err}"
        return observation

    def _execute_python_code(self, code: str) -> str:
        temp_file_path = "/tmp/temp_script.py"
        code = code.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
        command = f'echo """{code}""" > {temp_file_path} && python3 {temp_file_path}'
        return self.execute_command(command)
    
    def exec_run(self, cmd, workdir=None):
        import subprocess
        exit_code = None
        output = None

        try:

            process = subprocess.run(
                cmd,
                cwd=workdir,  # Set the working directory
                shell=False,    # Use the shell to execute the command
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE   # Capture standard error
            )
            # Get exit code and output
            exit_code = process.returncode
            output = process.stdout.decode() if exit_code == 0 else process.stderr.decode()
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return exit_code, output

    def execute_command(self, command: str):
        cmd = ["bash", "-c", command]
        exit_code, output = self.exec_run(cmd, workdir=self.work_dir)
        # exit_code, output = self.container.exec_run(cmd, workdir=self.work_dir)
        ## can't create a new python environment in the container, eg. python3 -m venv /path/to/venv
        if "venv" in command:
            return "Creating a new python environment is not allowed in the container. You can use 'pip install' to install the required packages."
        is_cd_flag = command.strip().startswith("cd ")
        if is_cd_flag:
            changed = command[command.index("cd ") + 3:].strip()
            if "&&" in changed:
                changed = changed[:changed.index("&&")].strip()
            self.work_dir = self.update_working_directory(self.work_dir, changed)
            return f"The command to change directory to {self.work_dir} is executed successfully."
        
        return output.strip()

    def _file_exists(self, file_path: str) -> bool:
        check_command = f"test -f {file_path} && echo 'exists' || echo 'not exists'"
        result = self.execute_command(check_command)
        return result.strip() == 'exists'
    
    def execute_python_file(self, file_path: str, content: str):
        escaped_content = content.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
        if not file_path.startswith('/'):
            if platform.system() == 'Windows':
                file_path = self.work_dir + '/' + file_path
            else:
                file_path = os.path.join(self.work_dir, file_path)
        dir_path = os.path.dirname(file_path)
        mkdir_command = f"mkdir -p {dir_path}"
        self.execute_command(mkdir_command)

        create_command = f'echo "{escaped_content}" > {file_path} && python3 {file_path}'
        return self.execute_command(create_command)
    
    def execute_sql_code(self,file_path, code, output: str) -> str:
        if code.startswith('""') and code.endswith('""'):
            code = code[2:-2]
        script_content = LOCAL_SQL_TEMPLATE.format(file_path=file_path, sql_command=code, output_path=output)
        temp_file_path = "temp_sql_script.py"
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        if observation.startswith(f'File "{temp_file_path}"'):
            observation = observation.split("\n", 1)[1]
        return observation
    
    def execute_bq_exec_sql_query(self, action):
        sql_query, is_save = action.sql_query, action.is_save
        save_path = getattr(action, 'save_path', "")

        script_content = BQ_EXEC_SQL_QUERY_TEMPLATE.format(
            sql_query=sql_query, is_save=is_save, save_path=save_path)

        temp_file_path = "temp_sql_script.py" 
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        if observation.startswith(f'File "{temp_file_path}"'):
            observation = observation.split("\n", 1)[1]
        return observation
    
    def execute_sf_exec_sql_query(self, action):
        sql_query, is_save = action.sql_query, True#action.is_save
        save_path = getattr(action, 'save_path', "")
        save_path = os.path.join(self.mnt_dir, save_path.replace("/workspace/",""))
        

        script_content = SF_EXEC_SQL_QUERY_TEMPLATE.format(
            sql_query=sql_query, is_save=is_save, save_path=save_path)

        temp_file_path = "temp_sql_script.py" 
        # import pdb; pdb.set_trace()
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        if observation.startswith(f'File "{temp_file_path}"'):
            observation = observation.split("\n", 1)[1]
        
        return observation

    def execute_sf_exec_sql_query_random(self, sql_query):
        sql_query = sql_query

        script_content = SF_EXEC_SQL_QUERY_TEMPLATE.format(
            sql_query=sql_query, is_save=False, save_path="")

        temp_file_path = "temp_sql_script.py" 
        # import pdb; pdb.set_trace()
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        # if observation.startswith(f'File "{temp_file_path}"'):
        #     observation = observation.split("\n", 1)[1]
        
        return observation
    def execute_sf_exec_sql_query_special(self, action):
        sql_query = action.sql_query

        script_content = SF_EXEC_SQL_QUERY_TEMPLATE.format(
            sql_query=sql_query, is_save=False, save_path="")

        temp_file_path = "temp_sql_script.py" 
        # import pdb; pdb.set_trace()
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        if observation.startswith(f'File "{temp_file_path}"'):
            observation = observation.split("\n", 1)[1]
        return observation    
    
    def execute_sf_exec_sql_query_special2(self, action):
        clause_tuple = action.clause_tuple
        observation_final = ""
        correct_or_not = {}        
        for i, clause in enumerate(clause_tuple):
            column_name = clause["column_name"]
            condition_type = clause["condition_type"]
            table_name = clause["table_name"]
            keyword_or_pattern = str(clause["keyword_or_pattern"])
            keyword_or_pattern = keyword_or_pattern.replace("[", "(").replace("]", ")")
            
            sql_query = 'SELECT DISTINCT "' + column_name + '" FROM ' + table_name + ' WHERE "' + column_name + '" ' + condition_type + ' ' + keyword_or_pattern + ' LIMIT 5;'
            script_content = SF_EXEC_SQL_QUERY_TEMPLATE.format(
                sql_query=sql_query, is_save=False, save_path="")

            temp_file_path = "temp_sql_script.py" 
            # import pdb; pdb.set_trace()
            observation = self.execute_python_file(temp_file_path, script_content)
            self.execute_command(f"rm {temp_file_path}")
            if observation.startswith(f'File "{temp_file_path}"'):
                observation = observation.split("\n", 1)[1]

            observation_final += "SQL query: " + sql_query + "\n" + observation + "\n\n"
            if 'No data found' in observation:
                correct_or_not[i] = False
            else:
                correct_or_not[i] = True

        observation_final += "Remember: The output is limited to 5 rows for each query. This is meant for checking if a condition clause is valid or not. Not for data retrievel."
        return observation_final, correct_or_not


    def execute_sf_exec_sql_query_special3(self, column_name, table_name):

        sql_query = 'SELECT DISTINCT "' + column_name + '" FROM ' + table_name + ' LIMIT 20;'
        script_content = SF_EXEC_SQL_QUERY_TEMPLATE.format(
            sql_query=sql_query, is_save=False, save_path="")

        temp_file_path = "temp_sql_script.py" 
        # import pdb; pdb.set_trace()
        observation = self.execute_python_file(temp_file_path, script_content)
        self.execute_command(f"rm {temp_file_path}")
        # if observation.startswith(f'File "{temp_file_path}"'):
        #     observation = observation.split("\n", 1)[1]
        return observation.split("\n")


    def execute_sf_inspect_table_json(self, json_file_path):
        content = json.loads(self.get_file(json_file_path))
        
        info = {}
        column_names = []
        info["table_fullname"] = content["table_fullname"]
        for i, column in enumerate(content["column_names"]):
            type = content["column_types"][i]
            description = content["description"][i]
            if description is None:
                description = ""
            
            vals = []
            for row in content["sample_rows"]:
                vals.append(row[column])

            if type == "NUMBER":
                for i, val in enumerate(vals):
                    if val is None:
                        continue
                    vals[i] = float(val)
            distinct_vals = list(set(vals))

            if not type == "TEXT" and not type == "BINARY" and not type == "VARIANT":
                if len(distinct_vals) == 0:
                    info[column] = {"type": type, "description": description, "sample_values": float(0)}
                else:
                    info[column] = {"type": type, "description": description, "sample_values": distinct_vals[0]}
            else:
                if type == "TEXT" or type == "VARIANT":
                    distinct_values = self.execute_sf_exec_sql_query_special3(column, content["table_fullname"])
                    if type == "TEXT":
                        if len(distinct_values[0]) > 100:
                            distinct_values = [distinct_values[0][:100] + "..."]
                    if len(distinct_values) == 20:
                        distinct_values = distinct_values[:2]
                    distinct_values = "\n--> " + distinct_values[0]
                    if len(distinct_values) > 5000:
                        distinct_values = distinct_values[:5000] + "..."
                    info[column] = {"type": type, "description": description, "sample_values": [], "distinct_values": distinct_values}
                else:
                    info[column] = {"type": type, "description": description, "sample_values": []}
            column_names.append(column)
        return info, column_names

    def execute_sf_inspect_ddl(self, ddl_file_path):
        csv_content = self.get_file(ddl_file_path)
        csv_rows = csv_content.split("\n")
        refined_content = ""
        for row in csv_rows:
            if not row.startswith("\t"):
                refined_content += row + "\n"
                continue
            refined_content += row + "\n"
        # max_length = 40000  
        # if len(refined_content) > max_length:
        #     refined_content = ""
        #     for row in csv_rows:
        #         if not row.startswith("\t"):
        #             refined_content += row + "\n"
        #             continue
        return refined_content

    def execute_sf_info_ddl(self, ddl_file_paths):
        ddl_table = {}
        for ddl_file_path in ddl_file_paths:
            csv_content = self.get_file(ddl_file_path)
            csv_rows = csv_content.split("\n")
            refined_content = []
            for row in csv_rows:
                if not row.startswith("\t"):
                    if not row.startswith("table") and not row.startswith(")"):
                        refined_content.append(row.split(",")[0])
                    continue
            ddl_table[ddl_file_path] = refined_content
        return ddl_table

    def execute_PREDICTED_MINIMAL_SET_OF_COLUMN_NAMES_AND_EXAMPLE_ROWS(self, action):
        column_names = action.column_names
        example_rows = action.example_rows
        num_rows = action.number_of_rows
        observation = f"The number of columns in the final result must be {len(column_names)}\n"
        observation = f"The column names in the final result must be {column_names}\n"
        # for i, column_name in enumerate(column_names):
        #     observation += f"The column {column_name} must contain data similar to {example_rows[i]}\n"
        if "CANNOT_BE_PREDICTED" not in num_rows:
            observation += f"The final result must strictly only contain {num_rows} rows"
        # observation += f"\nThe number of rows depends on {action.depends_on}"
        return observation

    def execute_inspect_markdown(self, action):
        markdown_file_path = action.markdown_file_path
        content = self.get_file(markdown_file_path)
        return content

    def get_directory_tree(self):
        return self.execute_command("python tree_function.py")
    
    def get_real_file_path(self, file_path: str):
        if not file_path.startswith(self.work_dir): # if the filepath is not absolute path, then it is a relative path
            if file_path.startswith("./"): file_path = file_path[2:]
            file_path = os.path.join(self.work_dir.rstrip('/'), file_path)

        if platform.system() == 'Windows':
            real_file_path = os.path.join(self.mnt_dir, file_path.replace('/workspace\\',""))
        else:
            real_file_path = os.path.join(self.mnt_dir, file_path.replace("/workspace/",""))     
        return real_file_path
    
    
    def get_current_workdir(self):
        return self.work_dir
    
    
    def update_working_directory(self, current: str, changed: Optional[str] = None) -> str:
        """ Resolves absolute path from the current working directory path and the argument of the `cd` command
        @args:
            current (str): the current working directory
            changed (Optional[str]): the changed working directory, argument of shell `cd` command
        @return:
            new_path (str): absolute path of the new working directory in the container
        """
        if not changed:
            return current
        if changed[0] == "/":
            current = ""

        path = []
        for segment in (current + "/" + changed).split("/"):
            if segment == "..":
                if path:
                    path.pop()
            elif segment and segment != ".":
                path.append(segment)
        new_path = "/" + "/".join(path)
        return new_path
    
    

if __name__ == '__main__':

    client = docker.from_env()
    container_name = "spider_agent"
    container = client.containers.get(container_name)
    
    
    controller = PythonController(container)