import os

def print_tree(startpath, prefix=""):
    # List all files and directories in the given path
    md_files = []
    json_files = []
    ddl_files = []
    tree_str = "" 
    for i, item in enumerate(os.listdir(startpath)):
        path = os.path.join(startpath, item)
        # If the item is a directory
        if os.path.isdir(path):
            # Print the directory name
            tree_str += f"{prefix}├── {item}/\n"
            # Recursively call the function for subdirectories
            tree_str_inside, md_files_inside, json_files_inside, ddl_files_inside = print_tree(path, prefix + "│   ")
            md_files += md_files_inside
            json_files += json_files_inside
            tree_str += tree_str_inside
            ddl_files += ddl_files_inside
        else:
            # Print the file name
            tree_str += f"{prefix}├── {item}\n"
            # Check if the file is a markdown file
            if item.endswith(".md"):
                md_files.append(path)
            # Check if the file is a JSON file
            if item.endswith(".json"):
                json_files.append(path)
            # Check if the file is a DDL file
            if item.endswith(".csv"):
                ddl_files.append(path)
                
    return tree_str, md_files, json_files, ddl_files

if __name__ == "__main__":
    # Example usage: Print the tree for the current directory
    tree_str, md_files, json_files, ddl_files = print_tree(".")

    print(tree_str)
    print("<DELIMITER>")
    print("\n".join(md_files))
    print("<DELIMITER>")
    print("\n".join(json_files))
    print("<DELIMITER>")
    print("\n".join(ddl_files))