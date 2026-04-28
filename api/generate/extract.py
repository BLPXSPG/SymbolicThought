import os
import json
import yaml
import re
from collections import Counter
from typing import List, Dict
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.utils.token_counter import count_string_tokens
from config import Config
from generate.auto_generate import gen_response_json
from generate.RAG import VectorDatabase

cfg = Config()



def split_text(text, max_length):
        sentences = re.split(r'(?<=[。！？])', text)
        sentence_lengths = [count_string_tokens(sentence) for sentence in sentences]

        total_tokens = sum(sentence_lengths)

        num_chunks = ceil(total_tokens / max_length)
        if num_chunks == 0:
            print(total_tokens, max_length)
        target_chunk_token_count = ceil(total_tokens / num_chunks)

        chunks = []
        current_chunk = []
        current_chunk_token_count = 0

        for sentence, length in zip(sentences, sentence_lengths):
            if current_chunk_token_count + length > target_chunk_token_count and current_chunk:
                chunks.append(''.join(current_chunk))
                current_chunk = [sentence]
                current_chunk_token_count = length
            else:
                current_chunk.append(sentence)
                current_chunk_token_count += length

        if current_chunk:
            if len(chunks) < num_chunks:
                chunks.append(''.join(current_chunk))
            else:
                chunks[-1] += ''.join(current_chunk)

        return chunks

def aggregate(outputs: List[List[str]]) -> List[str]:
    """
    聚合多个输出，使用多数投票
    """
    all_names = []
    for output in outputs:
        if isinstance(output, list):
            all_names.extend(output)
    
    # 统计频次
    name_counts = Counter(all_names)
    
    # 选择出现频次大于等于阈值的名字
    threshold = max(2, len(outputs) // 2)
    frequent_names = [name for name, count in name_counts.items() if count >= threshold]
    
    # 如果频繁名字太少，选择前10个最常见的
    if len(frequent_names) < 5:
        frequent_names = [name for name, count in name_counts.most_common(10)]
    
    return frequent_names

def aggregate_relations(outputs: List[Dict]) -> Dict:
    """
    聚合多个关系抽取输出，使用频次过滤
    """
    # 统计所有关系的出现频次
    relation_counts = {}  # {(char_i, char_j, relation): count}
    
    for output in outputs:
        if isinstance(output, dict):
            for character, linked_chars in output.items():
                if isinstance(linked_chars, dict):
                    for linked_char, relationships in linked_chars.items():
                        if isinstance(relationships, list):
                            for rel in relationships:
                                key = (character, linked_char, rel)
                                relation_counts[key] = relation_counts.get(key, 0) + 1
    
    print(f"关系频次统计: {dict(relation_counts)}")
    
    # 过滤：保留至少出现2次的关系
    threshold = 2
    filtered_relations = {key: count for key, count in relation_counts.items() if count >= threshold}
    
    print(f"保留关系（出现>={threshold}次）: {dict(filtered_relations)}")
    
    # 如果过滤后的关系太少，降低阈值或选择最频繁的关系
    if len(filtered_relations) < 5:
        print(f"过滤后关系太少({len(filtered_relations)}个)，降低阈值...")
        # 降低阈值到1，即只要出现过1次就保留
        filtered_relations = relation_counts
    
    # 重新构建关系字典
    merged_data = {}
    for (character, linked_char, rel), count in filtered_relations.items():
        if character not in merged_data:
            merged_data[character] = {}
        if linked_char not in merged_data[character]:
            merged_data[character][linked_char] = []
        
        if rel not in merged_data[character][linked_char]:
            merged_data[character][linked_char].append(rel)
    
    # 统计最终结果
    total_relations = sum(len(rels) for char_data in merged_data.values() 
                         for rels in char_data.values())
    total_pairs = sum(len(char_data) for char_data in merged_data.values())
    print(f"聚合结果统计: {total_relations} 个关系, {total_pairs} 个角色对")
    
    return merged_data

def _sample_character_once(sys_prompt, prompt, config):
    try:
        response = gen_response_json(sys_prompt, prompt, config)
        if isinstance(response, dict) and "characters" in response:
            return response["characters"]
    except Exception as e:
        print(f"角色采样失败: {e}")
    return None


def extract_character(config, story):
    prompt_path = os.path.join(os.getcwd(), "prompts.yaml")
    with open(prompt_path, 'r') as f:
        prompts = yaml.load(f, Loader=yaml.FullLoader)

    character_name = story["secondary_title"]
    character_background_text = story["content"]
    sys = prompts['ext_character_list_prompt_sys']

    if count_string_tokens(character_background_text) > config.max_tokens - count_string_tokens(prompts['ext_character_list_prompt']):
        chunks = split_text(character_background_text, config.max_tokens - count_string_tokens(prompts['ext_character_list_prompt']))

        all_character_outputs = []
        for chunk in chunks:
            prompt = prompts['ext_character_list_prompt'].replace("{character_name}", character_name)
            prompt = prompt.replace("{character_background_text}", chunk)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(_sample_character_once, sys, prompt, config) for _ in range(5)]
                chunk_outputs = [f.result() for f in futures if f.result() is not None]

            if chunk_outputs:
                chunk_aggregated = aggregate(chunk_outputs)
                all_character_outputs.extend(chunk_aggregated)

        final_characters = list(set(all_character_outputs))
    else:
        prompt = prompts['ext_character_list_prompt'].replace("{character_name}", character_name)
        prompt = prompt.replace("{character_background_text}", character_background_text)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_sample_character_once, sys, prompt, config) for _ in range(5)]
            character_outputs = [f.result() for f in futures if f.result() is not None]

        final_characters = aggregate(character_outputs) if character_outputs else []

    print(f"角色抽取结果: {len(final_characters)} 个角色: {final_characters}")
    return final_characters

def merge_character_data(data1, data2):
    merged_data = data1.copy()  
    for character, linked_characters in data2.items():
        if character not in merged_data:
            merged_data[character] = linked_characters
        else:
            for linked_character, relationships in linked_characters.items():
                if linked_character in merged_data[character]:
                    existing_relationships = set(merged_data[character][linked_character])
                    new_relationships = [rel for rel in relationships if rel not in existing_relationships]
                    merged_data[character][linked_character].extend(new_relationships)
                else:
                    merged_data[character][linked_character] = relationships

    return merged_data

def clean_data(data, character_list, relations):
    cleaned_data = {}

    for character in character_list:
        linked_characters = data.get(character, {})
        cleaned_linked_characters = {}
        
        for linked_character, relationship_categories in linked_characters.items():
            if linked_character in character_list:
                valid_relationships = [category for category in relationship_categories if category in relations]
                
                if valid_relationships:
                    cleaned_linked_characters[linked_character] = valid_relationships
        
        cleaned_data[character] = cleaned_linked_characters

    return cleaned_data

def convert_to_echarts_structure(data, coreference, character_name):
    coreference_dic = {}
    for character in coreference:
        if len(character) > 1:
            coreference_dic[character[0]] = character[1:]
        elif len(character) == 1:
            coreference_dic[character[0]] = []
        else:
            continue
    if character_name in coreference_dic:
        coreference_dic[character_name] += ["你(You)"]
    else:
        coreference_dic[character_name] = ["你(You)"]

    result = {
        "name": "relationships",
        "children": []
    }
    depth_2_value = -1
    depth_3_value = 1
    depth_4_value = 100000

    for key, sub_data in data.items():
        depth_2_node = {
            "name": key,
            "children": [],
            "value": depth_2_value,
            "coreference": coreference_dic[key],
            "depth": 2
        }
        depth_2_value -= 1  
        for sub_key, relationships in sub_data.items():
            depth_3_node = {
                "name": sub_key,
                "children": [],
                "value": depth_3_value,
                "coreference": coreference_dic[sub_key],
                "depth": 3
            }
            depth_3_value += 1  
            for relationship in relationships:
                depth_4_value += 1  
                depth_3_node["children"].append({
                    "name": relationship,
                    "depth": 4,
                    "value": depth_4_value,
                    "itemStyle": {"color": "#FFBF00"},  # 使用金色作为初始关系的默认颜色
                    "auto_suggested": True  # 标记为自动生成的关系
                })
                
            depth_2_node["children"].append(depth_3_node)
        
        result["children"].append(depth_2_node)
    
    return result, depth_3_value


def convert_characters_to_structure(character_list):
    result = {
        "name": "characters",
        "children": []
    }
    
    for character in character_list:
        result["children"].append({
            "name": character
        })
    
    return result

def _sample_relation_once(sys_prompt, prompt, config):
    try:
        response = gen_response_json(sys_prompt, prompt, config)
        if isinstance(response, dict):
            return response
    except Exception as e:
        print(f"关系采样失败: {e}")
    return None


def extract_relation(config, story, equivalent_relation):
    prompt_path = os.path.join(os.getcwd(), "prompts.yaml")
    with open(prompt_path, 'r') as f:
        prompts = yaml.load(f, Loader=yaml.FullLoader)

    relations = list(equivalent_relation["High-Level relations"]) + list(equivalent_relation["equivalent relations"].keys())
    relations = [item.lower().strip() for item in relations]
    relations = [r for r in relations if r != "stranger to x"]

    character_name = story["secondary_title"]
    character_background_text = story["content"]
    sys = prompts['extract_relation_given_character_sys']
    base_prompt = prompts['extract_relation_given_character_new_json'].replace("{categories}", str(relations))

    character_list = [character[0] for character in story["coreference"] if len(character) > 0]

    base_prompt = base_prompt.replace("{character_name}", character_name).replace("{character_list}", str(character_list))

    if count_string_tokens(character_background_text) > config.max_tokens - count_string_tokens(base_prompt):
        chunks = split_text(character_background_text, config.max_tokens - count_string_tokens(base_prompt))

        all_relation_outputs = []
        for chunk in chunks:
            prompt = base_prompt.replace("{character_background_text}", chunk)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(_sample_relation_once, sys, prompt, config) for _ in range(5)]
                chunk_outputs = [f.result() for f in futures if f.result() is not None]

            all_relation_outputs.extend(chunk_outputs)

        merged_response = aggregate_relations(all_relation_outputs) if all_relation_outputs else {}
    else:
        prompt = base_prompt.replace("{character_background_text}", character_background_text)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_sample_relation_once, sys, prompt, config) for _ in range(5)]
            relation_outputs = [f.result() for f in futures if f.result() is not None]

        merged_response = aggregate_relations(relation_outputs) if relation_outputs else {}

    print("聚合后的关系抽取结果:", merged_response)
    merged_response = clean_data(merged_response, character_list, relations)
    print("清理后的关系数据:", merged_response)
    merged_response, max_node = convert_to_echarts_structure(merged_response, story["coreference"], character_name)
    print("转换为ECharts结构:", merged_response)
    entities = convert_characters_to_structure(character_list)
    print("角色实体结构:", entities)

    return [merged_response], entities, max_node

def get_rag(config, story, embedding_dir):
    character_list = [character[0] for character in story["coreference"] if len(character) > 0]

    coreference_dic = {}
    story_name = story["primary_title"]
    character_name = story["secondary_title"]
    for character in story["coreference"]:
        if len(character) > 1:
            coreference_dic[character[0]] = character[1:]
        elif len(character) == 1:
            coreference_dic[character[0]] = []
    if config.first_person:
        if character_name in coreference_dic:
            coreference_dic[character_name] += ["你(You)"]
        else:
            coreference_dic[character_name] = ["你(You)"]

    related_text_dic = {ci: {} for ci in character_list}

    db = VectorDatabase(max_length=20)
    embedding_path = os.path.join(embedding_dir, story_name + "_" + character_name + ".pkl")
    if os.path.exists(embedding_path):
        db.load_texts(embedding_path)
        db.load_faiss(os.path.join(embedding_dir, story_name + "_" + character_name + ".faiss"))
    else:
        db.add_text(story["content"], config)
        db.save_texts(embedding_path)
        db.save_faiss(os.path.join(embedding_dir, story_name + "_" + character_name + ".faiss"))

    pairs = []
    for idx, ci in enumerate(character_list):
        for cj in character_list[idx+1:]:
            ci_ref = ci + str(coreference_dic[ci]) if coreference_dic.get(ci) else ci
            cj_ref = cj + str(coreference_dic[cj]) if coreference_dic.get(cj) else cj
            retrieve_prompt = f"Information about the relationship between {ci_ref} and {cj_ref}"
            pairs.append((ci, cj, retrieve_prompt))

    def _query_pair(pair):
        ci, cj, prompt = pair
        return ci, cj, db.query_num(prompt, 10, config)

    with ThreadPoolExecutor(max_workers=min(24, len(pairs) or 1)) as executor:
        for ci, cj, related_text in executor.map(_query_pair, pairs):
            related_text_dic[ci][cj] = related_text
            related_text_dic[cj][ci] = related_text

    return related_text_dic
            
