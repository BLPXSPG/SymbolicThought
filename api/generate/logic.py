import os
from time import sleep
import json, csv, yaml, sys
import copy
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from memory.processing import split_text
from config.utils.token_counter import count_string_tokens
import shutil
#from googletrans import Translator
#from deep_translator import GoogleTranslator
import itertools
import re
from math import ceil
import logging
from generate.auto_generate import multiple_generate, gen_response_json, gen_response_string
from generate.relationship import Relation
from generate.RAG import VectorDatabase
from collections import defaultdict
from tqdm import tqdm

logging.basicConfig(
    filename='extract.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class LogicRelation():
    def __init__(self, config, equivalent_relation):
        self.config = config
        self.language = config.use_language
        prompt_path = os.path.join(os.getcwd(), "prompts.yaml")
        with open(prompt_path, 'r') as f:
            self.prompts = yaml.load(f, Loader=yaml.FullLoader)
            f.close()

        self.multiple = 3  # 添加 multiple 变量初始化
        self.equivalent_relation = equivalent_relation
        self.high_level_relations = self.equivalent_relation["High-Level relations"]
        self.high_level_relations = {k.lower().strip(): [item.lower().strip() for item in v] for k, v in self.high_level_relations.items()}

        self.high_level_category_map = {}
        for relation in self.high_level_relations:
            for mapping_relation in self.high_level_relations[relation]:
                relation = relation.lower().strip()
                mapping_relation = mapping_relation.lower().strip()
                self.high_level_category_map[mapping_relation] = relation
        self.equivalent_relation = self.equivalent_relation["equivalent relations"]

        self.equivalent_relation = {k.lower().strip(): [item.lower().strip() for item in v] for k, v in self.equivalent_relation.items()}
        self.relation_merge_map = {}
        for relation in self.equivalent_relation:
            for mapping_relation in self.equivalent_relation[relation]:
                relation = relation.lower().strip()
                mapping_relation = mapping_relation.lower().strip()
                self.relation_merge_map[mapping_relation] = relation
        
        self.category_list = list(self.equivalent_relation.keys()) + list(self.relation_merge_map.keys())
        self.category_list = [item.lower().strip() for item in self.category_list]
        self.combined_list = list(self.high_level_relations.keys()) + self.category_list

        self.relation_class()

    def generate_csv(self, relations, save_dir):
        with open(save_dir, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            header = [''] + relations
            writer.writerow(header)
            
            for name in relations:
                row = [name] + [''] * len(relations)
                writer.writerow(row)

    def find_n_entries(self, file_path):
        n_entries = []
        first_column_values = []
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row_index, row in enumerate(reader):
                first_column_value = row[0]
                first_column_values.append(first_column_value)
                for col_index, entry in enumerate(row):
                    if entry == 'N':
                        n_entries.append((row_index, col_index))
        return n_entries, first_column_values[1:]

    def label_relation_logic_graph(self):
        conflict_graph_path = os.path.join(os.getcwd(), "data", "relation_logic_conflict.csv")
        if not os.path.exists(conflict_graph_path):
            self.generate_csv(self.category_list, conflict_graph_path)
            #logging.info(f'Need Annotation (conflicting relationships)!')
        else:
            self.relation_logic_conflict = {}
            n_entries_list, category_list = self.find_n_entries(conflict_graph_path)
            #print(category_list)
            #logging.info(f"Entries with 'N': {n_entries_list}")
            for entry in n_entries_list:

                if category_list[entry[0]-1] in self.relation_logic_conflict:
                    self.relation_logic_conflict[category_list[entry[0]-1]] += [category_list[entry[1]-1]]
                else:
                    self.relation_logic_conflict[category_list[entry[0]-1]] = [category_list[entry[1]-1]]
                if category_list[entry[1]-1] in self.relation_logic_conflict:
                    self.relation_logic_conflict[category_list[entry[1]-1]] += [category_list[entry[0]-1]]
                else:
                    self.relation_logic_conflict[category_list[entry[1]-1]] = [category_list[entry[0]-1]]
            logging.info(f"conflicting relationships: {self.relation_logic_conflict}")

        antisymmetric_graph_path = os.path.join(os.getcwd(), "data", "relation_logic_antisymmetric.csv")
        if not os.path.exists(antisymmetric_graph_path):
            self.generate_csv(category_list, antisymmetric_graph_path)
            #logging.info(f'Need Annotation (antisymmetric relationships)!')
        else:
            self.relation_logic_antisymmetric = {}
            n_entries_list, category_list = self.find_n_entries(antisymmetric_graph_path)
            #logging.info(f"Entries with 'N': {n_entries_list}")
            for entry in n_entries_list:
                if category_list[entry[0]-1] in self.relation_logic_antisymmetric:
                    self.relation_logic_antisymmetric[category_list[entry[0]-1]] += [category_list[entry[1]-1]]
                else:
                    self.relation_logic_antisymmetric[category_list[entry[0]-1]] = [category_list[entry[1]-1]]
                if category_list[entry[1]-1] in self.relation_logic_antisymmetric:
                    self.relation_logic_antisymmetric[category_list[entry[1]-1]] += [category_list[entry[0]-1]]
                else:
                    self.relation_logic_antisymmetric[category_list[entry[1]-1]] = [category_list[entry[0]-1]]
            logging.info(f"antisymmetric relationships: {self.relation_logic_antisymmetric}")

    def relation_class(self):
        self.label_relation_logic_graph()
        relation_logic_path = os.path.join(os.getcwd(), "data", "relation_logic.json")
        if os.path.exists(relation_logic_path):
            with open(relation_logic_path, 'r') as f:
                data = json.load(f)
                relation_logic_inversion = data["inversion"]
                relation_logic_gender = data["gender"]
                relation_logic_exclusive = data["exclusive"]
                f.close()
        # add domain knowledge to each relationship
        self.relation_class_dic = {}
        for relationship in self.category_list:
            realtionship_class = Relation(relationship)
            self.relation_class_dic[relationship] = realtionship_class
        
        for relationship,  realtionship_class in self.relation_class_dic.items():
            realtionship_class.add_inversion(relation_logic_inversion[relationship])
            realtionship_class.add_gender(relation_logic_gender[relationship])
            realtionship_class.update_exclusive(relation_logic_exclusive[relationship])
            realtionship_class.add_conflict(self.relation_logic_conflict[relationship])
            realtionship_class.add_antisymmetric(self.relation_logic_antisymmetric[relationship])

        # self.high_level_relations
        for parent_relationship in self.equivalent_relation:
            for child_relationship in self.equivalent_relation[parent_relationship]:
                #logging.info(f'parent: {parent_relationship}, child: {child_relationship}')
                child_class = self.relation_class_dic.get(child_relationship)
                parent_class = self.relation_class_dic.get(parent_relationship)
                if child_class:
                    child_class.add_parent_relation(parent_relationship)
                if parent_class:
                    parent_class.add_child_relation(child_relationship)
                #relation_class_dic[child_relationship] = child_class
                #relation_class_dic[parent_relationship] = parent_class
        for parent_relationship in self.high_level_relations:
            for child_relationship in self.high_level_relations[parent_relationship]:
                child_class = self.relation_class_dic.get(child_relationship)
                if child_class:
                    child_class.add_parent_relation(parent_relationship)

    def add_conflict_checks_to_relations(self, relationships_graph):
        updated_graph = copy.deepcopy(relationships_graph)
        for node_lvl2 in updated_graph[0].get("children", []):  # 主体人物A
            character_a = node_lvl2.get("name", "")
            if character_a == "relationships":
                continue  # 跳过根节点，防止被当作人物节点处理
            for node_lvl3 in node_lvl2.get("children", []):  # 与之有关联的人物B
                character_b = node_lvl3.get("name", "")
                relation_nodes = node_lvl3.get("children", [])
                
                # 安全地创建映射，跳过没有必要字段的节点
                relation_name_to_value = {}
                relation_names = set()
                for r in relation_nodes:
                    if "name" in r and "value" in r:
                        relation_name_to_value[r["name"]] = r["value"]
                        relation_names.add(r["name"])
                
                for relation_node in relation_nodes:
                    if "name" not in relation_node or "value" not in relation_node:
                        continue
                        
                    current_relation = relation_node["name"]
                    current_value = relation_node["value"]
                    check_conflicts = set()
                    
                    # conflict
                    check_conflicts |= set(self.relation_logic_conflict.get(current_relation, []))
                    # antisymmetric
                    check_conflicts |= set(self.relation_logic_antisymmetric.get(current_relation, []))
                    # exclusive
                    current_class = self.relation_class_dic.get(current_relation)
                    if current_class and current_class.exclusive:
                        for other_relation in relation_names:
                            if other_relation != current_relation:
                                other_class = self.relation_class_dic.get(other_relation)
                                if other_class and other_class.exclusive:
                                    check_conflicts.add(other_relation)
                    
                    # 构建 check 字典: value -> [人物A, 人物B, 关系名]
                    actual_conflicts = check_conflicts & relation_names - {current_relation}
                    check_result = {}
                    for conflict_name in actual_conflicts:
                        if conflict_name in relation_name_to_value:  # 确保冲突的关系有value
                            value = relation_name_to_value[conflict_name]
                            check_result[value] = [character_a, character_b, conflict_name]
                    
                    if check_result:
                        relation_node["check"] = check_result
        
        return updated_graph

    def add_inversion_suggestion_to_relations(self, relationships_graph, character_i, character_j, relationship_ij, max_value, is_user_added=False):
        """为关系图添加反向关系建议。
        
        Args:
            relationships_graph: 关系图数据
            character_i: 起始角色
            character_j: 目标角色
            relationship_ij: 从角色i到角色j的关系
            max_value: 当前最大的节点值
            is_user_added: 是否是用户手动添加的关系
        
        Returns:
            tuple: (更新后的关系图, 最大节点值)
        """
        if not relationships_graph or not isinstance(relationships_graph, list) or not relationships_graph[0].get("children"):
            return relationships_graph, max_value
            
        updated_graph = copy.deepcopy(relationships_graph)
        
        # 确保关系存在于我们的映射中
        if relationship_ij not in self.relation_class_dic:
            return updated_graph, max_value

        # 获取反向关系
        relationship_ji = self.relation_class_dic[relationship_ij].inversion[0] if self.relation_class_dic[relationship_ij].inversion else None
        if not relationship_ji:
            return updated_graph, max_value

        found_char_i = False
        found_char_j = False
        found_char_j_node = None

        # 遍历图中的节点
        for node_lvl2 in updated_graph[0].get("children", []):
            if node_lvl2.get("name") == character_j:  # 找到目标角色j
                found_char_j = True
                found_char_j_node = node_lvl2
                for node_lvl3 in node_lvl2.get("children", []):
                    if node_lvl3.get("name") == character_i:  # 找到起始角色i
                        found_char_i = True
                        # 检查是否已经存在反向关系
                        existing_relations = [child.get("name") for child in node_lvl3.get("children", [])]
                        if relationship_ji not in existing_relations:
                            # 添加反向关系，并标记为自动建议
                            max_value += 1
                            node_lvl3.setdefault("children", []).append({
                                "name": relationship_ji,
                                "value": max_value,
                                "depth": 4,
                                "itemStyle": {"color": "#FFBF00"},
                                "auto_suggested": True  # 标记为自动建议的关系
                            })
                break

        # 如果没有找到目标角色j，创建一个新的角色j节点
        if not found_char_j:
            # 安全唯一负数分配
            used_values = set(child.get('value') for child in updated_graph[0].get('children', []) if isinstance(child, dict) and child.get('depth') == 2 and isinstance(child.get('value'), int) and child.get('value') < 0)
            new_value = -1
            while new_value in used_values:
                new_value -= 1
            new_char_j_node = {
                "name": character_j,
                "value": new_value,  # 用安全负数
                "depth": 2,
                "children": []
            }
            updated_graph[0]["children"].append(new_char_j_node)
            found_char_j_node = new_char_j_node

        # 如果找到了角色j但没有找到角色i的关联，创建一个新的关联
        if not found_char_i and found_char_j_node:
            max_value += 1
            new_char_i_relation = {
                "name": character_i,
                "value": max_value,
                "depth": 3,
                "children": [{
                    "name": relationship_ji,
                    "value": max_value + 1,
                    "depth": 4,
                    "itemStyle": {"color": "#FFBF00"},
                    "auto_suggested": True
                }]
            }
            max_value += 1
            if "children" not in found_char_j_node or not isinstance(found_char_j_node["children"], list):
                found_char_j_node["children"] = []
            found_char_j_node["children"].append(new_char_i_relation)

        return updated_graph, max_value

    def check_direction(self, cfg, embedding_dir, story_type, story_name, relationships_graph, story_data, max_value):
        logging.info(f"check_direction: story_type={story_type}, story_name={story_name}")

        if not relationships_graph or not isinstance(relationships_graph, list):
            logging.error("relationships_graph is empty or not a list")
            return relationships_graph, max_value

        logging.debug(f"Graph has {len(relationships_graph)} root nodes")
        for i, item in enumerate(relationships_graph):
            logging.debug(f"Root node {i}: keys={item.keys() if isinstance(item, dict) else 'N/A'}")

        updated_graph = copy.deepcopy(relationships_graph)

        try:
            db = VectorDatabase(max_length=30)
            embedding_path = os.path.join(embedding_dir, story_type + "_" + story_name + ".pkl")
            db.load_texts(embedding_path)
            db.load_faiss(os.path.join(embedding_dir, story_type + "_" + story_name + ".faiss"))
            logging.debug("Database loaded successfully")
        except Exception as e:
            logging.error(f"Error loading database: {e}")
            return relationships_graph, max_value

        character_nodes = {}
        for root in updated_graph:
            if isinstance(root, dict):
                if root.get("name") == "relationships":
                    for char_node in root.get("children", []):
                        if isinstance(char_node, dict) and char_node.get("depth") == 2:
                            character_nodes[char_node["name"]] = char_node
                elif root.get("depth") == 2:
                    character_nodes[root["name"]] = root
        logging.debug(f"Found {len(character_nodes)} character nodes")

        for char_node in character_nodes.values():
            character_i = char_node['name']

            if 'children' not in char_node:
                continue
            logging.debug(f"Processing {character_i}: {len(char_node['children'])} targets")

            to_remove = []
            to_add = []

            for target in char_node['children']:
                if target.get('depth') != 3:
                    continue

                character_j = target['name']

                if 'children' not in target:
                    continue

                for relation in target['children']:
                    if relation.get('depth') != 4:
                        continue

                    relationship_ij = relation['name']

                    if relationship_ij not in self.relation_class_dic:
                        continue

                    if relationship_ij in self.relation_class_dic[relationship_ij].inversion:
                        continue

                    retrieve_prompt = self.prompts['retrieve_relation_related'].format(
                        character_i=character_i,
                        character_j=character_j,
                        relation_ij=relationship_ij
                    )

                    related_text = db.query_num(retrieve_prompt, 10, cfg)

                    relation1 = relationship_ij.replace(' x', ' '+character_j)
                    relation2 = relationship_ij.replace(' x', ' '+character_i)

                    prompt = self.prompts['check_direction'].replace('{character_background_text}', " ".join(related_text))
                    prompt = prompt.replace('{character_i}', character_i).replace('{character_j}', character_j)
                    prompt = prompt.replace('{relation_i}', relation1).replace('{relation_j}', relation2)

                    response_list = multiple_generate(cfg, self.prompts['remove_conflict_sys'], prompt, multiple=self.multiple)

                    vote_list = []
                    for response in response_list:
                        if "1" in response:
                            vote_list.append(relationship_ij)

                    logging.debug(f"  {character_i}->{character_j} [{relationship_ij}]: {len(vote_list)}/{self.multiple} votes to keep")

                    if len(vote_list) >= math.ceil(self.multiple/2):
                        to_remove.append((character_j, relationship_ij))
                        to_add.append({
                            'source': character_j,
                            'target': character_i,
                            'relation': relationship_ij,
                            'value': relation.get('value', 0)
                        })

            logging.debug(f"  {character_i}: removing {len(to_remove)}, adding {len(to_add)}")
            for character_j, relationship_ij in to_remove:
                for target in char_node['children']:
                    if target['name'] == character_j:
                        target['children'] = [r for r in target['children'] if r['name'] != relationship_ij]
                        if not target['children']:
                            char_node['children'].remove(target)
                        break

            for rel in to_add:
                if rel['source'] not in character_nodes:
                    used_values = set(child.get('value') for child in updated_graph[0].get('children', []) if isinstance(child, dict) and child.get('depth') == 2 and isinstance(child.get('value'), int) and child.get('value') < 0)
                    new_value = -1
                    while new_value in used_values:
                        new_value -= 1
                    character_nodes[rel['source']] = {
                        'name': rel['source'],
                        'depth': 2,
                        'children': [],
                        'value': new_value
                    }
                    updated_graph.append(character_nodes[rel['source']])
                target_node = character_nodes[rel['source']]
                target_child = None
                for child in target_node.get('children', []):
                    if child['name'] == rel['target']:
                        target_child = child
                        break
                if not target_child:
                    max_value += 1
                    target_child = {
                        'name': rel['target'],
                        'depth': 3,
                        'children': [],
                        'value': max_value
                    }
                    if 'children' not in target_node:
                        target_node['children'] = []
                    target_node['children'].append(target_child)
                relation_exists = False
                if 'children' in target_child:
                    for existing_relation in target_child['children']:
                        if existing_relation['name'] == rel['relation']:
                            relation_exists = True
                            break
                if not relation_exists:
                    relation_node = {
                        'name': rel['relation'],
                        'depth': 4,
                        'value': rel['value'],
                        "itemStyle": {"color": "#FFBF00"},
                        "auto_suggested": True
                    }
                    if 'children' not in target_child:
                        target_child['children'] = []
                    target_child['children'].append(relation_node)
                    logging.debug(f"  Added: {rel['source']}->{rel['target']}: {rel['relation']}")

        logging.info("check_direction finished")
        return updated_graph, max_value




#from config.config import Config
#cfg = Config()
#test = LogicRelation(cfg)
#print(test.relation_class_dic)

#test_data = """[{"children": [{"children": [{"children": [{"depth": 4, "name": "acquaintance of x", "value": 100001}], "coreference": [], "depth": 3, "name": "德雷克·里莫瑞特", "value": 1}, {"children": [{"depth": 4, "name": "acquaintance of x", "value": 100002}], "coreference": [], "depth": 3, "name": "盖尔·里莫瑞特", "value": 2}, {"children": [{"depth": 4, "name": "acquaintance of x", "value": 100003}], "coreference": [], "depth": 3, "name": "汉斯·里莫瑞特", "value": 3}, {"children": [{"depth": 4, "name": "acquaintance of x", "value": 100004}, {"depth": 4, "name": "stranger to x", "value": 100005}, {"depth": 4, "name": "friend of x", "value": 100006}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 4}, {"children": [{"depth": 4, "name": "same person as x (different identity)", "value": 100007}], "coreference": [], "depth": 3, "name": "神父汤姆", "value": 5}], "coreference": [], "depth": 2, "name": "汤姆", "value": -1}, {"children": [{"children": [{"depth": 4, "name": "stranger to x", "value": 100008}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 6}], "coreference": ["卡特", "实习生"], "depth": 2, "name": "依琳·卡特", "value": -2}, {"children": [{"children": [{"depth": 4, "name": "acquaintance of x", "value": 100009}], "coreference": [], "depth": 3, "name": "汤姆", "value": 7}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100010}], "coreference": [], "depth": 3, "name": "盖尔·里莫瑞特", "value": 8}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100011}], "coreference": [], "depth": 3, "name": "汉斯·里莫瑞特", "value": 9}, {"children": [{"depth": 4, "name": "colleague of x", "value": 100013}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 10}], "coreference": [], "depth": 2, "name": "德雷克·里莫瑞特", "value": -3}, {"children": [{"children": [{"depth": 4, "name": "acquaintance of x", "value": 100014}], "coreference": [], "depth": 3, "name": "汤姆", "value": 11}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100015}], "coreference": [], "depth": 3, "name": "德雷克·里莫瑞特", "value": 12}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100016}], "coreference": [], "depth": 3, "name": "汉斯·里莫瑞特", "value": 13}, {"children": [{"depth": 4, "name": "stranger to x", "value": 100017}, {"depth": 4, "name": "colleague of x", "value": 100018}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 14}], "coreference": [], "depth": 2, "name": "盖尔·里莫瑞特", "value": -4}, {"children": [{"children": [{"depth": 4, "name": "acquaintance of x", "value": 100019}], "coreference": [], "depth": 3, "name": "汤姆", "value": 15}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100020}], "coreference": [], "depth": 3, "name": "德雷克·里莫瑞特", "value": 16}, {"children": [{"depth": 4, "name": "sibling of x", "value": 100021}], "coreference": [], "depth": 3, "name": "盖尔·里莫瑞特", "value": 17}, {"children": [{"depth": 4, "name": "stranger to x", "value": 100022}, {"depth": 4, "name": "colleague of x", "value": 100023}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 18}], "coreference": [], "depth": 2, "name": "汉斯·里莫瑞特", "value": -5}, {"children": [{"children": [{"depth": 4, "name": "stranger to x", "value": 100024}, {"depth": 4, "name": "colleague of x", "value": 100025}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 19}], "coreference": [], "depth": 2, "name": "斯科特", "value": -6}, {"children": [{"children": [{"depth": 4, "name": "acquaintance of x", "value": 100026}, {"depth": 4, "name": "stranger to x", "value": 100027}, {"depth": 4, "name": "friend of x", "value": 100028}], "coreference": [], "depth": 3, "name": "汤姆", "value": 20}, {"children": [{"depth": 4, "name": "stranger to x", "value": 100029}], "coreference": [], "depth": 3, "name": "德雷克·里莫瑞特", "value": 21}, {"children": [{"depth": 4, "name": "stranger to x", "value": 100030}], "coreference": [], "depth": 3, "name": "盖尔·里莫瑞特", "value": 22}, {"children": [{"depth": 4, "name": "stranger to x", "value": 100031}], "coreference": [], "depth": 3, "name": "汉斯·里莫瑞特", "value": 23}, {"children": [{"depth": 4, "name": "wife of x", "value": 100032}, {"depth": 4, "name": "husband of x", "value": 100033}, {"depth": 4, "name": "romantic relationships with x", "value": 100034}], "coreference": [], "depth": 3, "name": "妻子", "value": 24}, {"children": [{"depth": 4, "name": "colleague of x", "value": 100035}], "coreference": ["伯克利"], "depth": 3, "name": "院长伯克利", "value": 25}, {"children": [{"depth": 4, "name": "colleague of x", "value": 100036}, {"depth": 4, "name": "helper of x", "value": 100037}], "coreference": [], "depth": 3, "name": "护士长科斯塔", "value": 26}, {"children": [{"depth": 4, "name": "acquaintance of x", "value": 100038}], "coreference": [], "depth": 3, "name": "神父汤姆", "value": 27}], "coreference": ["你(You)"], "depth": 2, "name": "安德鲁·帕洛斯基", "value": -7}, {"children": [{"children": [{"depth": 4, "name": "colleague of x", "value": 100039}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 28}], "coreference": ["伯克利"], "depth": 2, "name": "院长伯克利", "value": -8}, {"children": [{"children": [{"depth": 4, "name": "husband of x", "value": 100040}, {"depth": 4, "name": "wife of x", "value": 100041}, {"depth": 4, "name": "romantic relationships with x", "value": 100042}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 29}], "coreference": [], "depth": 2, "name": "妻子", "value": -9}, {"children": [{"children": [{"depth": 4, "name": "colleague of x", "value": 100043}, {"depth": 4, "name": "helper of x", "value": 100044}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 30}], "coreference": [], "depth": 2, "name": "护士长科斯塔", "value": -10}, {"children": [{"children": [{"depth": 4, "name": "stranger to x", "value": 100045}, {"depth": 4, "name": "same person as x (different identity)", "value": 100046}], "coreference": [], "depth": 3, "name": "汤姆", "value": 31}, {"children": [{"depth": 4, "name": "acquaintance of x", "value": 100047}], "coreference": ["你(You)"], "depth": 3, "name": "安德鲁·帕洛斯基", "value": 32}], "coreference": [], "depth": 2, "name": "神父汤姆", "value": -11}], "name": "relationships"}]"""
#test_data = json.loads(test_data)
#new_data = test.add_conflict_checks_to_relations(test_data)
#print(new_data)
