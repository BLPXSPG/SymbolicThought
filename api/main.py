import os, json
from config import Config
from flask import Flask
from flask import request, jsonify, session
from flask_session import Session
from node_extraction.extract_flow import process_flow
from generate.extract import extract_character, extract_relation, get_rag
import uuid
#from extract_gpt import CharacterExtraction
import openai
from generate.logic import LogicRelation
import shutil
import fcntl
import threading

import logging
from time import gmtime, strftime, sleep

global cfg
cfg = Config()

# 预设的故事和元数据路径
DEFAULT_STORY_PATH = os.path.join(os.getcwd(), "data", "stories", "story.json")
DEFAULT_META_PATH = os.path.join(os.getcwd(), "data", "stories", "meta.json")

category_path = os.path.join(os.getcwd(), "data", "equivalent_relation.json")
with open(category_path, 'r') as f:
    equivalent_relation = json.load(f)

logic_checker = LogicRelation(cfg, equivalent_relation)

# 用于文件锁的线程锁字典
file_locks = {}
file_locks_lock = threading.Lock()

def get_file_lock(file_path):
    """获取文件对应的锁"""
    with file_locks_lock:
        if file_path not in file_locks:
            file_locks[file_path] = threading.Lock()
        return file_locks[file_path]

def safe_json_read(file_path):
    """安全地读取JSON文件"""
    file_lock = get_file_lock(file_path)
    with file_lock:
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return None

def safe_json_write(file_path, data):
    """安全地写入JSON文件"""
    file_lock = get_file_lock(file_path)
    with file_lock:
        try:
            # 先写入临时文件，然后原子性地替换原文件
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            
            # 在Windows上，需要先删除目标文件
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)
            return True
        except Exception as e:
            print(f"Error writing JSON file {file_path}: {e}")
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

app = Flask(__name__)
print(app.url_map)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex())
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
print("running?")

def initialize_user_data(user_id):
    """初始化用户数据，复制预设的故事和元数据"""
    user_story_dir = os.path.join(cfg.uploaded_files_path, "story", str(user_id))
    user_meta_dir = os.path.join(cfg.uploaded_files_path, "meta", str(user_id))
    user_task_dir = os.path.join(cfg.uploaded_files_path, "task", str(user_id))

    # 创建用户目录
    os.makedirs(user_story_dir, exist_ok=True)
    os.makedirs(user_meta_dir, exist_ok=True)
    os.makedirs(user_task_dir, exist_ok=True)

    # 如果用户目录下没有story.json，复制预设的故事文件
    user_story_path = os.path.join(user_story_dir, "story.json")
    if not os.path.exists(user_story_path):
        shutil.copy2(DEFAULT_STORY_PATH, user_story_path)

    # 如果用户目录下没有meta.json，复制预设的元数据文件
    user_meta_path = os.path.join(user_meta_dir, "meta.json")
    if not os.path.exists(user_meta_path):
        shutil.copy2(DEFAULT_META_PATH, user_meta_path)

    user_setting_path = os.path.join(user_task_dir, "setting.json")
    if not os.path.exists(user_setting_path):
        with open(user_setting_path, 'w', encoding='utf-8') as f:
            json.dump(cfg.preset_flow, f, ensure_ascii=False, indent=4)

@app.route('/input-narrative-name', methods=['POST', 'GET'])
def input_narrative_name():
    if request.method == 'POST':
        return jsonify({'post_status': 'success'})
    return jsonify({'status': 'ok'})

@app.route('/background', methods=['POST', 'GET'])
def background():
    stories = safe_json_read(DEFAULT_STORY_PATH) or []
    first_story = stories[0] if stories else {}
    return jsonify({
        'filename': first_story.get('secondary_title', 'story'),
        'background': first_story.get('content', ''),
        'background_index': [],
        'agents': first_story.get('entities_confirmed', first_story.get('entities', [])),
        'relations': first_story.get('relations', []),
        'relationcategory': list(equivalent_relation.get('equivalent relations', {}).keys()),
    })

def gen_response_35(sys: str, prompt: str, config, retry_flag = True):
    try:
        deployment_id = config.get_azure_deployment_id_for_model(config.model)
        completion = openai.ChatCompletion.create(
            engine=deployment_id, 
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": prompt},
            ],
            n=1
        )
        try:
            response = completion.choices[0].message["content"].replace('`', '').replace('json', '').replace('\n', '').replace('    ', ' ').replace('  ', ' ')  
            start_index = response.find("{")
            end_index = response.rfind("}")
            data = json.loads(response[start_index:end_index+1])
            return data

        except json.JSONDecodeError as e:
            if retry_flag:
                sys += "Careful about comma in JSON format."
                print("JSONDecodeError", response)
                print("JSONDecodeError, RETRY", response[start_index:end_index+1])
                return gen_response_35(sys, prompt, config, retry_flag = False)
            else:
                print("JSONDecodeError: ", e)
                print("Couldn't fix the JSON", response)
                return {}
            
    except Exception as e:
        print("ERROR response", e)
        sleep(2)
        if retry_flag:
            retry_flag = False
            return gen_response_35(sys, prompt, config, retry_flag)
        else:
            retry_flag = True
            return {}


# save narrative file
@app.route('/input-narrative-file', methods=['POST','GET'])
def input_narrative_file():
    if request.method == 'POST':  
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())  
        user_id = session['user_id']
        try:
            # 确保用户数据已初始化
            initialize_user_data(user_id)
            
            if 'file' not in request.files:
                print("no files")
                return jsonify({'post_status': 'success'})  # 没有文件也返回成功，因为使用预设文件
            else:
                file = request.files['file']
                file_type = request.form.get('fileType')
                if file_type == "story":
                    save_path = os.path.join(cfg.uploaded_files_path, "story", str(user_id))
                    with open(os.path.join(save_path, "story.json"), "wb") as f:
                        file.save(f)
                elif file_type == "meta":
                    save_path = os.path.join(cfg.uploaded_files_path, "meta", str(user_id))
                    with open(os.path.join(save_path, "meta.json"), "wb") as f:
                        file.save(f)

                save_path = os.path.join(cfg.uploaded_files_path, "task", str(user_id))
                setting = cfg.preset_flow
                with open(os.path.join(save_path, "setting.json"), 'w', encoding='utf-8') as f:
                    json.dump(setting, f, ensure_ascii=False, indent=4)
                print(os.path.join(save_path, "setting.json"))
            return jsonify({'post_status': 'success'})
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'post_status': 'fail'})
    else:
        return jsonify({'status': 'else'})

# get default setting
@app.route('/send-default-flow', methods=['POST','GET'])
def send_default_character():
    if request.method == 'POST':  
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())  
        user_id = session['user_id']
        try:
            task = request.get_json()["task"]
            save_path = os.path.join(cfg.uploaded_files_path, "task", str(user_id))
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                setting = cfg.preset_flow
                with open(os.path.join(save_path, "setting.json"), 'w', encoding='utf-8') as f:
                    json.dump(setting, f, ensure_ascii=False, indent=4)
            else:
                with open(os.path.join(save_path, "setting.json"), 'r', encoding='utf-8') as f:
                    setting = json.load(f)[task]
            return jsonify(setting)
        except Exception as e:
            return jsonify({'post_status': 'fail'})
    else:
        return jsonify({'status': 'else'})

# use default setting of character extraction
@app.route('/input-flow-character', methods=['POST','GET'])
def input_flow_character():
    if request.method == 'POST':  
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4()) 
        user_id = session['user_id']
        try:
            save_path = os.path.join(cfg.uploaded_files_path, "task", str(user_id))
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                setting = cfg.preset_flow.copy()
                setting["Current"] = cfg.preset_flow["Character"]
                with open(os.path.join(save_path, "setting.json"), 'w', encoding='utf-8') as f:
                    json.dump(setting, f, ensure_ascii=False, indent=4)
            return jsonify({'post_status': 'success'})
        except Exception as e:
            return jsonify({'post_status': 'fail'})
    else:
        return jsonify({'status': 'else'})

# save code
@app.route('/save-setting', methods=['POST','GET'])
def save_setting():
    if request.method == 'POST':  
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())  
        user_id = session['user_id']
        try:
            current_setting = request.get_json()["code"]
            #print(request.get_json())
            current_task = request.get_json()["task"]
            save_path = os.path.join(cfg.uploaded_files_path, "task", str(user_id))
            llm_type = request.get_json()["selectedOption"]
            with open(os.path.join(save_path, "setting.json"), 'r', encoding='utf-8') as f:
                setting = json.load(f)
            setting[current_task] = current_setting
            with open(os.path.join(save_path, "setting.json"), 'w', encoding='utf-8') as f:
                json.dump(setting, f, ensure_ascii=False, indent=4)
            print("save setting:",os.path.join(save_path, "setting.json"))
            return jsonify({'post_status': 'success'})
        except Exception as e:
            return jsonify({'post_status': 'fail'})
    else:
        return jsonify({'status': 'else'})

@app.route('/test-setting', methods=['POST','GET'])
def test_setting():
    if request.method == 'POST':  
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())  
        user_id = session['user_id']
        try:

            story_file = os.path.join(cfg.uploaded_files_path, "story", str(user_id), "story.json")
            story = safe_json_read(story_file)
            meta_file = os.path.join(cfg.uploaded_files_path, "meta", str(user_id), "meta.json")
            meta = safe_json_read(meta_file)
            code_dict = request.get_json()
            save_path = os.path.join(cfg.uploaded_files_path, "task", str(user_id))
            Flag, string = process_flow(save_path, code_dict, story, meta)
            if Flag:
                result = {"Response": string} # result = {"Response": "Error: ..."}
                return jsonify({'post_status': 'success', 'test_result': result})
            else:
                result = {"Response": string}
                return jsonify({'post_status': 'Fail', 'test_result': result})
        except Exception as e:
            #logging.error("Exception occurred, conversation Error", exc_info=True)
            return jsonify({'post_status': 'fail'})
    else:
        return jsonify({'status': 'else'})
    
@app.route('/get-books', methods=['POST','GET'])
def get_books():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_id = session['user_id']
    
    # 确保用户数据已初始化
    initialize_user_data(user_id)
    
    story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
    story_data = safe_json_read(story_path)
    if story_data is None:
        return jsonify({'error': 'Error reading story file'}), 500
    return jsonify(story_data)


@app.route('/get-character', methods=['POST','GET'])
def get_character():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_id = session['user_id']
    
    # 确保用户数据已初始化
    initialize_user_data(user_id)
    
    data = request.get_json()
    story_id = data.get('storyId')
    story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
    
    story_data = safe_json_read(story_path)
    if story_data is None:
        return jsonify({'error': 'Failed to read story data'}), 500

    story_new = {
        "number": story_data[story_id]["number"],
        "primary_title": story_data[story_id]["primary_title"],
        "secondary_title": story_data[story_id]["secondary_title"],
        "content": story_data[story_id]["content"]
    }

    print("extract characters from the story...")
    characters = extract_character(cfg, story_data[story_id])

    story_new["entities_unconfirmed"] = characters
    story_new["entities_confirmed"] = []
    story_new["entities_removed"] = []
    story_new["entities_added"] = []
    story_new["coreference"] = []

    story_data[story_id] = story_new

    if not safe_json_write(story_path, story_data):
        return jsonify({'error': 'Failed to save character data'}), 500

    response_data = {
        "characters": characters,
        "force_update": True,
        "timestamp": strftime("%Y-%m-%d %H:%M:%S", gmtime())
    }
    return jsonify(response_data)

def remove_extra_empty_lists(lst):
    found_empty = False
    result = []
    for sublist in lst:
        if sublist == []:
            if not found_empty:
                result.append(sublist)
                found_empty = True
        else:
            result.append(sublist)
    return result

#LabelEntity - update the entity data
@app.route('/send-entities', methods=['POST'])
def send_entities():
    # Ensure that we received JSON data
    if not request.is_json:
        return jsonify({"error": "Invalid content type"}), 400

    # Extract the JSON data from the request
    data = request.get_json()
    story_id = data.get("storyId")
    added_words = data.get("addedWords", [])
    removed_words = data.get("removedWords", [])
    confirmed_words = data.get("confirmedWords", [])
    coreference = data.get("coreferenceSlots", [])
    coreference = remove_extra_empty_lists(coreference)
    
    # 添加强制完成标志
    force_complete = data.get("forceComplete", False)
    
    #print(confirmed_words, removed_words, added_words, coreference)
    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        
        if os.path.exists(story_path):
            # 使用安全的读取函数
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500
            
            # 如果是强制完成模式，确保所有实体都被处理
            if force_complete and "entities_unconfirmed" in story_data[story_id]:
                all_unconfirmed = set(story_data[story_id]["entities_unconfirmed"])
                all_confirmed = set(confirmed_words)
                all_removed = set(removed_words)
                all_added = set(added_words)
                
                # 找出还没有被处理的实体，自动添加到确认列表
                unprocessed = all_unconfirmed - all_confirmed - all_removed
                if unprocessed:
                    confirmed_words.extend(list(unprocessed))
                    print(f"强制完成模式：自动确认了 {len(unprocessed)} 个未处理的实体")
            
            # 更新数据
            story_data[story_id]["entities_confirmed"] = list(set(confirmed_words))
            story_data[story_id]["entities_removed"] = list(set(removed_words))
            story_data[story_id]["entities_added"] = list(set(added_words))
            story_data[story_id]["coreference"] = coreference
            
            # 使用安全的写入函数
            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500

            return jsonify({
                "success": True,
                "message": "Entity data saved successfully",
                "story_data": story_data[story_id],
                "auto_confirmed": len(unprocessed) if force_complete and 'unprocessed' in locals() else 0
            }), 200
        else:
            return jsonify({"error": "Story file not found"}), 404
    else:
        return jsonify({"error": "User not logged in"}), 401

# 新增：完成实体标注并进入下一步的同步接口
@app.route('/finish-entities-and-next', methods=['POST'])
def finish_entities_and_next():
    """
    专门用于"Finish and Next Step"按钮的接口
    确保实体数据完整保存后再允许进入下一步
    """
    if not request.is_json:
        return jsonify({"error": "Invalid content type"}), 400

    data = request.get_json()
    story_id = data.get("storyId")
    added_words = data.get("addedWords", [])
    removed_words = data.get("removedWords", [])
    confirmed_words = data.get("confirmedWords", [])
    coreference = data.get("coreferenceSlots", [])
    coreference = remove_extra_empty_lists(coreference)
    
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
        
    user_id = session['user_id']
    story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
    
    if not os.path.exists(story_path):
        return jsonify({"error": "Story file not found"}), 404
    
    # 使用安全的读取函数
    story_data = safe_json_read(story_path)
    if story_data is None:
        return jsonify({"error": "Failed to read story data"}), 500
    
    if str(story_id) not in story_data:
        return jsonify({"error": "Story not found"}), 404
    
    # 确保所有必要字段存在
    if "entities_unconfirmed" not in story_data[str(story_id)]:
        return jsonify({"error": "No entities to confirm"}), 400
    
    # 计算需要自动确认的实体
    all_unconfirmed = set(story_data[str(story_id)]["entities_unconfirmed"])
    all_confirmed = set(confirmed_words)
    all_removed = set(removed_words)
    
    # 找出还没有被处理的实体，自动添加到确认列表
    unprocessed = all_unconfirmed - all_confirmed - all_removed
    auto_confirmed_count = 0
    
    if unprocessed:
        confirmed_words.extend(list(unprocessed))
        auto_confirmed_count = len(unprocessed)
        print(f"完成并进入下一步：自动确认了 {auto_confirmed_count} 个未处理的实体: {list(unprocessed)}")
    
    # 更新数据
    story_data[str(story_id)]["entities_confirmed"] = list(set(confirmed_words))
    story_data[str(story_id)]["entities_removed"] = list(set(removed_words))
    story_data[str(story_id)]["entities_added"] = list(set(added_words))
    story_data[str(story_id)]["coreference"] = coreference
    
    # 使用安全的写入函数
    if not safe_json_write(story_path, story_data):
        return jsonify({"error": "Failed to save story data"}), 500
    
    # 验证数据完整性
    final_confirmed = len(story_data[str(story_id)]["entities_confirmed"])
    final_removed = len([e for e in story_data[str(story_id)]["entities_removed"] 
                        if e in story_data[str(story_id)]["entities_unconfirmed"]])
    total_unconfirmed = len(story_data[str(story_id)]["entities_unconfirmed"])
    
    if final_confirmed + final_removed != total_unconfirmed:
        return jsonify({
            "error": "Data validation failed",
            "details": f"confirmed: {final_confirmed}, removed: {final_removed}, total: {total_unconfirmed}"
        }), 500
    
    return jsonify({
        "success": True,
        "message": "Entities completed successfully, ready for next step",
        "auto_confirmed_count": auto_confirmed_count,
        "auto_confirmed_entities": list(unprocessed) if unprocessed else [],
        "total_confirmed": final_confirmed,
        "total_removed": final_removed,
        "ready_for_next_step": True,
        "story_data": story_data[str(story_id)]
    }), 200

@app.route('/merge-coreference', methods=['POST','GET'])
def merge_coreference():
    data = request.get_json()
    children_name = data.get('childrenName')
    is_highlighted = data.get('isHighlighted')
    highlighted_node = data.get('highlightedNode')
    left_tree_data = data.get('leftTreeData')
    story_id = data.get('storyId')
    changed_relation = data.get('highlightedRightNodes')
    character_i = data.get('selectedRoot')
    #print("received infor",children_name, is_highlighted, highlighted_node, story_id, changed_relation, character_i)

    updated_tree_data = []
    for root in left_tree_data:
        parts, cj = update_node_coreference(root, highlighted_node, children_name, is_highlighted)
        if cj:
            character_j = cj
        updated_tree_data.append(parts)

    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        if os.path.exists(story_path):
            # 使用安全的读取函数
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500

            #print("changed relation", character_i, character_j, children_name)
            max_value = story_data[story_id]["max_node"]
            if is_highlighted:  # Only add inverse relations when adding a new relation
                updated_tree_data, max_value = logic_checker.add_inversion_suggestion_to_relations(updated_tree_data, character_i, character_j, children_name, max_value, is_user_added=True)
                updated_tree_data = logic_checker.add_conflict_checks_to_relations(updated_tree_data)
                story_data[story_id]["max_node"] = max_value

            story_data[story_id]["relations"] = updated_tree_data  

            # 使用安全的写入函数
            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500
    
    return jsonify(updated_tree_data)

#LabelRelation - initialise relation data for StoryId
@app.route('/get-relation-data/<int:story_id>', methods=['GET'])
def get_relation_data(story_id):
    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        relation_path = os.path.join(cfg.uploaded_files_path, 'meta', str(user_id), 'meta.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({'error': 'Failed to read story data'}), 500
            equivalent_relation = safe_json_read(relation_path)
            if equivalent_relation is None:
                return jsonify({'error': 'Failed to read relation data'}), 500
            # 检查实体确认状态，如果不完整则自动补全
            if "entities_confirmed" not in story_data[story_id]:
                story_data[story_id]["entities_confirmed"] = []
            if "entities_removed" not in story_data[story_id]:
                story_data[story_id]["entities_removed"] = []
            if "entities_added" not in story_data[story_id]:
                story_data[story_id]["entities_added"] = []
            
            removed_entities = [entity_i for entity_i in story_data[story_id]["entities_removed"] if entity_i in story_data[story_id]["entities_unconfirmed"]]
            confirmed_count = len(story_data[story_id]["entities_confirmed"])
            removed_count = len(removed_entities)
            total_unconfirmed = len(story_data[story_id]["entities_unconfirmed"])
            
            # 如果实体确认不完整，自动将剩余未处理的实体标记为已确认（兜底逻辑）
            if confirmed_count + removed_count != total_unconfirmed:
                print(f"实体确认不完整，自动补全：confirmed={confirmed_count}, removed={removed_count}, total={total_unconfirmed}")
                
                # 找出还没有被确认或移除的实体
                all_confirmed_set = set(story_data[story_id]["entities_confirmed"])
                all_removed_set = set(story_data[story_id]["entities_removed"])
                all_unconfirmed_set = set(story_data[story_id]["entities_unconfirmed"])
                
                unprocessed_entities = all_unconfirmed_set - all_confirmed_set - all_removed_set
                
                # 将未处理的实体自动添加到已确认列表中
                if unprocessed_entities:
                    story_data[story_id]["entities_confirmed"].extend(list(unprocessed_entities))
                    story_data[story_id]["entities_confirmed"] = list(set(story_data[story_id]["entities_confirmed"]))  # 去重
                    
                    # 保存更新后的数据
                    if not safe_json_write(story_path, story_data):
                        return jsonify({"error": "Failed to save auto-confirmed entity data"}), 500
                    
                    print(f"自动确认了 {len(unprocessed_entities)} 个实体: {list(unprocessed_entities)}")

            # 检查是否需要生成关系图
            need_generate = False
            if "relations" not in story_data[story_id]:
                need_generate = True
            elif not story_data[story_id]["relations"]:  # 如果relations是空的
                need_generate = True
            
            embedding_dir = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), "embedding")
            rag_available = bool(story_data[story_id].get("rag"))
            if not story_data[story_id].get("rag"):
                if not os.path.exists(embedding_dir):
                    os.mkdir(embedding_dir)
                try:
                    rag_dic = get_rag(cfg, story_data[story_id], embedding_dir)
                    story_data[story_id]["rag"] = rag_dic
                    rag_available = True
                except Exception as e:
                    print(f"RAG generation skipped: {e}")
                    story_data[story_id]["rag"] = {}
                    rag_available = False

            if need_generate:
                relations, entities, max_node = extract_relation(cfg, story_data[story_id], equivalent_relation)
                
                if rag_available:
                    # 首先检查并修正关系方向
                    relations, max_node = logic_checker.check_direction(
                        cfg,
                        embedding_dir, 
                        story_data[story_id]["primary_title"], 
                        story_data[story_id]["secondary_title"], 
                        relations, 
                        story_data[story_id],
                        max_node
                    )
                else:
                    print("Skipping relation direction check because RAG is unavailable.")
                
                # 收集所有关系
                all_relations = []
                for relation in relations:
                    if relation.get('depth') == 2:  # 角色节点
                        char_name = relation.get('name')
                        if 'children' in relation:
                            for target in relation['children']:  # depth 3 节点，目标角色
                                if 'children' in target:
                                    for relation_type in target['children']:  # depth 4 节点，关系类型
                                        all_relations.append({
                                            'source': char_name,
                                            'target': target['name'],
                                            'relation': relation_type['name']
                                        })
                
                # 为每个关系添加反向关系建议（只添加合适的反向关系）
                for rel in all_relations:
                    relations, max_node = logic_checker.add_inversion_suggestion_to_relations(
                        relations, rel['source'], rel['target'], rel['relation'],
                        max_node, is_user_added=False
                    )
                
                story_data[story_id]["relations"] = relations
                story_data[story_id]["max_node"] = max_node
                story_data[story_id]["entities"] = entities
                story_data[story_id]["relations_generated"] = relations

            story_data[story_id]["relations"] = logic_checker.add_conflict_checks_to_relations(story_data[story_id]["relations"])

            if need_generate or "rag" not in story_data[story_id]:
                if not safe_json_write(story_path, story_data):
                    return jsonify({'error': 'Failed to save story data'}), 500

        else:
            return jsonify({'error': 'Story file not found'}), 404
        
    response_data = {
        "relationdata": story_data[story_id]["relations"],
        "characterdata_detail": story_data[story_id]["entities"],
        "story_data": story_data
    }
    return jsonify(response_data)

def update_node_coreference(node, highlighted_node, children_name, is_highlighted, current_depth=0):
    entity = None
    if current_depth == 2 and node.get('value') == highlighted_node:
        updated_children = node.get('children', []).copy()

        if is_highlighted:
            if not any(child.get('name') == children_name for child in updated_children):
                updated_children.append({'name': children_name, 'itemStyle': {'color': '#2E8B57'}})
        else:
            updated_children = [child for child in updated_children if child.get('name') != children_name]

        node['children'] = updated_children
        return node, node.get('name')

    if 'children' in node:
        update_children = []
        for child in node['children']:
            updated, c_j = update_node_coreference(child, highlighted_node, children_name, is_highlighted, current_depth + 1)
            if c_j:
                entity = c_j
            update_children.append(updated)

    return node, entity

#RelationGraph - update the relation data (relation)
@app.route('/change-relation', methods=['POST'])
def change_relation():
    data = request.get_json()
    children_name = data.get('childrenName')
    is_highlighted = data.get('isHighlighted')
    highlighted_node = data.get('highlightedNode')
    left_tree_data = data.get('leftTreeData')
    story_id = data.get('storyId')
    changed_relation = data.get('highlightedRightNodes')
    character_i = data.get('selectedRoot')

    # 遍历图中的节点，找到所有已存在的value
    existing_values = set()
    def collect_values(node):
        if isinstance(node, dict):
            if 'value' in node:
                existing_values.add(str(node['value']))
            if 'children' in node:
                for child in node['children']:
                    collect_values(child)

    for root in left_tree_data:
        collect_values(root)

    # 生成新的唯一value
    def get_next_value(max_value):
        while str(max_value) in existing_values:
            max_value += 1
        existing_values.add(str(max_value))
        return max_value

    updated_tree_data = []
    for root in left_tree_data:
        parts, cj = update_node(root, highlighted_node, children_name, is_highlighted, get_next_value)
        if cj:
            character_j = cj
        updated_tree_data.append(parts)

    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500

            if not is_highlighted:
                # 先清除所有节点的check状态
                def clear_check_status(nodes):
                    for node in nodes:
                        if 'check' in node:
                            del node['check']
                        if 'children' in node and node['children']:
                            clear_check_status(node['children'])
                
                clear_check_status(updated_tree_data)
                # 重新检查冲突
                updated_tree_data = logic_checker.add_conflict_checks_to_relations(updated_tree_data)
            else:  # 添加关系的情况保持原有逻辑
                print("changed relation", character_i, character_j, children_name)
                max_value = story_data[story_id]["max_node"]
                updated_tree_data, max_value = logic_checker.add_inversion_suggestion_to_relations(updated_tree_data, character_i, character_j, children_name, max_value, is_user_added=True)
                updated_tree_data = logic_checker.add_conflict_checks_to_relations(updated_tree_data)
                story_data[story_id]["max_node"] = max_value

            story_data[story_id]["relations"] = updated_tree_data

            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500

    return jsonify(updated_tree_data)

def update_node(node, highlighted_node, children_name, is_highlighted, get_next_value):
    entity = None
    if node.get('value') == highlighted_node:
        updated_children = node.get('children', []).copy()  
        
        if is_highlighted:
            if not any(child.get('name') == children_name for child in updated_children):
                # 获取当前最大value
                current_max = max([int(child.get('value', 0)) for child in updated_children], default=0)
                # 生成新的唯一value
                new_value = get_next_value(current_max + 1)
                updated_children.append({
                    'name': children_name, 
                    'value': new_value,
                    'depth': 4,
                    'itemStyle': {'color': '#2E8B57'}  # 使用正确的绿色 #2E8B57
                })
        else:
            updated_children = [child for child in updated_children if child.get('name') != children_name]

        node['children'] = updated_children
        return node, node.get('name')
    
    if 'children' in node:
        update_children = []
        for child in node['children']:
            updated, c_j = update_node(child, highlighted_node, children_name, is_highlighted, get_next_value) 
            if c_j:
                entity = c_j
            update_children.append(updated)
        node['children'] = update_children
    
    return node, entity

def update_character_node(node, highlighted_node, children_name, is_highlighted, max_value):
    if node.get('value') == highlighted_node:
        updated_children = node.get('children', [])
        if is_highlighted:
            #max_value = find_global_max_value(node)
            if not any(child.get('name') == children_name for child in updated_children):
                #max_value = max((child.get('value', 0) for child in updated_children), default=0)
                new_child = {
                    'name': children_name,
                    'children': [],
                    'value': max_value,
                    'depth': 3,
                    'itemStyle': {'color': '#5cd65c'}
                }
                updated_children.append(new_child)
            print("updated_children", updated_children)
        else:
            updated_children = [child for child in updated_children if child.get('name') != children_name]
        node['children'] = updated_children
    
    # 递归处理所有子节点
    if 'children' in node:
        node['children'] = [update_character_node(child, highlighted_node, children_name, is_highlighted, max_value) 
                          for child in node['children']]
    
    return node

#RelationGraph - update the relation data (character)
@app.route('/change-character', methods=['POST'])
def change_character():
    data = request.get_json()
    children_name = data.get('childrenName')
    is_highlighted = data.get('isHighlighted')
    highlighted_node = data.get('highlightedNode')
    leftTreeData = data.get('leftTreeData')
    story_id = data.get('storyId')

    if 'user_id' in session:
        user_id = session['user_id']
        
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        relation_path = os.path.join(cfg.uploaded_files_path, 'meta', str(user_id), 'meta.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500

            max_value = story_data[story_id]["max_node"]
            if is_highlighted:
                print("is_highlighted", highlighted_node, children_name)
                max_value += 1
                story_data[story_id]["max_node"] = max_value
            updated_tree_data = [update_character_node(root, highlighted_node, children_name, is_highlighted, max_value) for root in leftTreeData]

            story_data[story_id]["relations"] = updated_tree_data

            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500

    return jsonify(updated_tree_data)

def delete_node_from_tree(tree_data, target_name, target_value):
    def recursive_filter(node):
        # 如果是目标节点，返回 None（表示删除）
        if node.get("name") == target_name and node.get("value") == target_value:
            print(f"recursive_filter return: {node}")
            return None

        # 递归处理子节点
        children = node.get("children", [])
        new_children = []
        for child in children:
            result = recursive_filter(child)
            if result is not None:
                new_children.append(result)

        # 如果还有子节点，保留 children 字段；否则删掉
        if new_children:
            node["children"] = new_children
        else:
            node.pop("children", None)

        return node

    # 处理所有根节点
    updated_tree = []
    for root in tree_data:
        result = recursive_filter(root)
        if result is not None:
            updated_tree.append(result)
    return updated_tree


@app.route('/delete-node', methods=['POST'])
def delete_node():
    data = request.get_json()
    remove_node = data.get('nodeName')
    remove_value = data.get('nodeValue')
    leftTreeData = data.get('leftTreeData')
    story_id = data.get('storyId')

    updated_tree_data = delete_node_from_tree(leftTreeData, remove_node, remove_value)

    if 'user_id' in session:
        user_id = session['user_id']
        
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500

            def clear_check_status(nodes):
                for node in nodes:
                    if 'check' in node:
                        del node['check']
                    if 'children' in node and node['children']:
                        clear_check_status(node['children'])

            clear_check_status(updated_tree_data)
            updated_tree_data = logic_checker.add_conflict_checks_to_relations(updated_tree_data)
            story_data[story_id]["relations"] = updated_tree_data

            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500

    return jsonify(updated_tree_data)


@app.route('/send-words', methods=['POST','GET'])
def update_entity():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.get_json()

        story_file = os.path.join(cfg.uploaded_files_path, "story", str(user_id), "story.json")
        story = safe_json_read(story_file)
        if story is None:
            return jsonify({"error": "Failed to read story data"}), 500

        for i in data["addedWords"]:
            story[int(i)]["entities"] = data["addedWords"][i]

        for i in data["removedWords"]:
            story[int(i)]["removedWords"] = data["removedWords"][i]

        if not safe_json_write(story_file, story):
            return jsonify({"error": "Failed to save story data"}), 500

        return jsonify({}) 

def update_colour_by_value(tree_data, target_value, new_color):
    """更新指定value的节点的颜色，同时保持其他属性不变。

    Args:
        tree_data: 树形数据
        target_value: 目标节点的value值
        new_color: 新的颜色值

    Returns:
        bool: 是否找到并更新了节点
    """
    def update_node_recursive(node):
        if isinstance(node, dict):
            if str(node.get('value')) == str(target_value):
                # 保持原有属性，只更新颜色
                if 'itemStyle' not in node:
                    node['itemStyle'] = {}
                node['itemStyle']['color'] = new_color
                # 移除auto_suggested标记，因为现在是用户确认的
                node.pop('auto_suggested', None)
                # 添加confirmed标记
                node['confirmed'] = True
                return True
            
            if 'children' in node:
                for child in node['children']:
                    if update_node_recursive(child):
                        return True
        return False

    for root in tree_data:
        if update_node_recursive(root):
            return True
    return False

#confirm relation (change colour)
@app.route('/confirm-node', methods=['POST'])
def confirm_node():
    data = request.get_json()
    node_value = data.get('nodeValue')
    story_id = data.get('storyId')
    left_tree = data.get('leftTreeData')
    print(node_value, left_tree)
    
    if node_value is None or not left_tree:
        return jsonify({"error": "Missing nodeValue or leftTreeData"}), 400

    success = update_colour_by_value(left_tree, node_value, "#2E8B57")
    if not success:
        return jsonify({"error": f"Node with value '{node_value}' not found"}), 404

    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({"error": "Failed to read story data"}), 500
            story_data[story_id]["relations"] = left_tree
            if not safe_json_write(story_path, story_data):
                return jsonify({"error": "Failed to save story data"}), 500
    return jsonify(left_tree)
            
@app.route('/download-annotations/<int:story_id>', methods=['GET'])
def download_annotations(story_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not found'}), 401
    
    user_id = session['user_id']
    story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
    
    story_data = safe_json_read(story_path)
    if story_data is None:
        return jsonify({'error': 'Failed to export annotations'}), 500

    if str(story_id) not in story_data:
        return jsonify({'error': 'Story not found'}), 404

    export_data = {
        "story_id": story_id,
        "title": story_data[str(story_id)].get("primary_title", ""),
        "characters": {
            "confirmed": story_data[str(story_id)].get("entities_confirmed", []),
            "coreference": story_data[str(story_id)].get("coreference", [])
        },
        "relations": story_data[str(story_id)].get("relations", []),
        "timestamp": strftime("%Y-%m-%d %H:%M:%S", gmtime())
    }

    response = jsonify(export_data)
    response.headers['Content-Disposition'] = f'attachment; filename=story_{story_id}_annotations.json'
    response.headers['Content-Type'] = 'application/json'
    return response

#LabelRelation - regenerate relation data for StoryId
@app.route('/regenerate-relations/<int:story_id>', methods=['POST'])
def regenerate_relations(story_id):
    if 'user_id' in session:
        user_id = session['user_id']
        story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
        relation_path = os.path.join(cfg.uploaded_files_path, 'meta', str(user_id), 'meta.json')
        if os.path.exists(story_path):
            story_data = safe_json_read(story_path)
            if story_data is None:
                return jsonify({'error': 'Failed to read story data'}), 500
            equivalent_relation = safe_json_read(relation_path)
            if equivalent_relation is None:
                return jsonify({'error': 'Failed to read relation data'}), 500

            # 重新生成关系图
            relations, entities, max_node = extract_relation(cfg, story_data[story_id], equivalent_relation)
            
            # 首先检查并修正关系方向
            embedding_dir = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), "embedding")
            relations, max_node = logic_checker.check_direction(
                cfg,
                embedding_dir, 
                story_data[story_id]["primary_title"], 
                story_data[story_id]["secondary_title"], 
                relations, 
                story_data[story_id],
                max_node
            )
            
            # 收集所有关系
            all_relations = []
            for relation in relations:
                if relation.get('depth') == 2:  # 角色节点
                    char_name = relation.get('name')
                    if 'children' in relation:
                        for target in relation['children']:  # depth 3 节点，目标角色
                            if 'children' in target:
                                for relation_type in target['children']:  # depth 4 节点，关系类型
                                    all_relations.append({
                                        'source': char_name,
                                        'target': target['name'],
                                        'relation': relation_type['name']
                                    })
            
            # 为每个关系添加反向关系建议（只添加合适的反向关系）
            for rel in all_relations:
                relations, max_node = logic_checker.add_inversion_suggestion_to_relations(
                    relations, rel['source'], rel['target'], rel['relation'],
                    max_node, is_user_added=False
                )
            
            story_data[story_id]["relations"] = relations
            story_data[story_id]["max_node"] = max_node
            story_data[story_id]["entities"] = entities
            story_data[story_id]["relations_generated"] = relations

            story_data[story_id]["relations"] = logic_checker.add_conflict_checks_to_relations(story_data[story_id]["relations"])

            if not safe_json_write(story_path, story_data):
                return jsonify({'error': 'Failed to save story data'}), 500
            
            response_data = {
                "relationdata": story_data[story_id]["relations"],
                "characterdata_detail": story_data[story_id]["entities"],
                "story_data": story_data
            }
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Story file not found'}), 404
    return jsonify({'error': 'User not found'}), 401

def convert_relations_to_flat_format(relations):
    """将树形关系转换为扁平化格式
    
    Args:
        relations: 树形关系数据列表
    
    Returns:
        dict: 扁平化的关系数据，格式为 {character: {target_char: [relation_type1, relation_type2, ...]}}
    """
    flat_relations = {}
    
    def process_node(node):
        if node.get('depth') == 2:  # 角色节点
            char_name = node.get('name')
            if char_name not in flat_relations:
                flat_relations[char_name] = {}
            
            # 处理该角色的所有关系
            if 'children' in node:
                for relation_type in node['children']:  # depth 3 节点，关系类型
                    relation_name = relation_type['name'].lower()
                    if 'children' in relation_type:
                        for target in relation_type['children']:  # depth 4 节点，目标角色
                            target_name = target['name']
                            if target_name not in flat_relations[char_name]:
                                flat_relations[char_name][target_name] = []
                            if relation_name not in flat_relations[char_name][target_name]:
                                flat_relations[char_name][target_name].append(relation_name)
        
        # 递归处理子节点
        if 'children' in node:
            for child in node['children']:
                process_node(child)
    
    # 处理所有根节点
    for root in relations:
        process_node(root)
    
    # 重新组织数据结构
    reorganized_relations = {}
    for char_name, relations_dict in flat_relations.items():
        reorganized_relations[char_name] = {}
        for target_name, relation_types in relations_dict.items():
            for relation_type in relation_types:
                if relation_type not in reorganized_relations[char_name]:
                    reorganized_relations[char_name][relation_type] = []
                reorganized_relations[char_name][relation_type].append(target_name)
    
    return reorganized_relations

@app.route('/download-relation', methods=['POST'])
def download_relation():
    if 'user_id' not in session:
        return jsonify({'error': 'User not found'}), 401
    
    user_id = session['user_id']
    story_path = os.path.join(cfg.uploaded_files_path, 'story', str(user_id), 'story.json')
    
    story_data = safe_json_read(story_path)
    if story_data is None:
        return jsonify({'error': 'Failed to export relations'}), 500

    export_data = []
    for story in story_data:
        filtered_story = {
            "content": story.get("content", ""),
            "coreference": story.get("coreference", [])
        }

        if "relations" in story:
            filtered_story["relations"] = convert_relations_to_flat_format(story["relations"])

        if "relations_generated" in story:
            filtered_story["relations_generated"] = convert_relations_to_flat_format(story["relations_generated"])

        export_data.append(filtered_story)

    return jsonify(export_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)


    
