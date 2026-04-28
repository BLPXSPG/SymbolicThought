import os
import importlib


import importlib.util
import sys

def load_and_run_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def process_flow(save_path, code_dict, story, meta):
    try:
        node_extraction_path = os.path.join(save_path, "server_tmp_code.py")
        text = story[0]["content"]
        categories = meta["categories"]

        task = code_dict["task"]
        llm_type = code_dict["selectedOption"]
        code = code_dict["code"]

        # Write code to server_tmp_code.py
        with open(node_extraction_path, 'w', encoding='utf-8') as file:
            file.write(code["defaultModelSetting"][llm_type]["code"])
            file.write("\n")

        with open(node_extraction_path, 'a', encoding='utf-8') as file:
            for key in code["defaultCodeEntity"].keys():
                file.write(code["defaultCodeEntity"][key]["code"])
                file.write("\n")

            for key in code["defaultCodeRelation"].keys():
                file.write(code["defaultCodeRelation"][key]["code"])
                file.write("\n")
        # importlib.reload(server_tmp_code)
        extraction_module = load_and_run_module(node_extraction_path, "extraction_module")

        # Import functions from the generated server_tmp_code.py
        # from node_extraction.server_tmp_code import (
        #     call_llm,
        #     EntityPreProcessing,
        #     EntityExtraction,
        #     EntityPostProcessing,
        #     RelationPreProcessing,
        #     RelationExtraction,
        #     RelationPostProcessing
        # )

        # Execute the processes
        text, categories = extraction_module.EntityPreProcessing(extraction_module.call_llm, text, categories)
        text, categories, characters = extraction_module.EntityExtraction(extraction_module.call_llm, text, categories)
        text, categories, characters = extraction_module.EntityPostProcessing(extraction_module.call_llm, text, categories, characters)
        text, categories, characters = extraction_module.RelationPreProcessing(extraction_module.call_llm, text, categories, characters)
        text, categories, characters, relationships_graph = extraction_module.RelationExtraction(extraction_module.call_llm, text, categories, characters)
        text, categories, characters, relationships_graph = extraction_module.RelationPostProcessing(extraction_module.call_llm, text, categories, characters, relationships_graph)
        return True, relationships_graph
    except Exception as e:
        return False, f"An error occurred: {str(e)}"