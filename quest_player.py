import streamlit as st
import os
import json

st.set_page_config(page_title="ИИ Квест-Платформа", layout="centered")
st.title("🔮 Вселенная Интерактивных Квест-Книг")

# Главный каталог со всеми историями
BASE_STORIES_DIR = "stories"

# --- 1. АВТОМАТИЧЕСКИЙ СКАНИРОВЩИК КНИГ В ПАПКЕ STORIES ---
if not os.path.exists(BASE_STORIES_DIR):
    os.makedirs(BASE_STORIES_DIR, exist_ok=True)

# Ищем все подпапки внутри stories, где есть файл story_map.json
available_quests = {}
for folder in os.listdir(BASE_STORIES_DIR):
    folder_path = os.path.join(BASE_STORIES_DIR, folder)
    if os.path.isdir(folder_path):
        map_file = os.path.join(folder_path, "story_map.json")
        if os.path.exists(map_file):
            try:
                with open(map_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                # Ключ — имя папки, значение — красивое название истории из ТЗ
                available_quests[folder] = meta.get("story_name", folder).upper()
            except:
                available_quests[folder] = folder

# --- 2. ИНИЦИАЛИЗАЦИЯ ИГРОВОЙ ПАМЯТИ ---
if "current_quest" not in st.session_state:
    st.session_state.current_quest = None
if "current_node" not in st.session_state:
    st.session_state.current_node = "start"
if "history" not in st.session_state:
    st.session_state.history = []
if "saves" not in st.session_state:
    st.session_state.saves = {}

# --- 3. БОКОВОЙ МЕНЕДЖЕР ВЫБОРА КНИГ ---
st.sidebar.write("### 📚 Ваша Библиотека")
if not available_quests:
    st.sidebar.warning("📭 Папка stories пуста. Сгенерируйте книгу через night_writer.py!")
else:
    # Красивый выпадающий список для выбора нужного квеста на лету!
    quest_options = list(available_quests.keys())
    selected_quest_folder = st.sidebar.selectbox(
        "Выберите книгу для погружения:", 
        quest_options, 
        format_func=lambda x: available_quests[x]
    )
    
    # Если игрок переключил книгу — сбрасываем состояние под новую историю
    if st.session_state.current_quest != selected_quest_folder:
        st.session_state.current_quest = selected_quest_folder
        st.session_state.current_node = "start"
        st.session_state.history = []
        st.session_state.saves = {}
        st.rerun()

# --- 4. ИГРОВОЙ ДВИЖОК ОТРЕНДЕРИННОЙ КНИГИ ---
if st.session_state.current_quest:
    quest_path = os.path.join(BASE_STORIES_DIR, st.session_state.current_quest)
    map_path = os.path.join(quest_path, "story_map.json")
    
    with open(map_path, "r", encoding="utf-8") as f:
        story_map = json.load(f)
        
    scenes = story_map.get("scenes", {})
    current_id = st.session_state.current_node
    
    if current_id in scenes:
        scene_data = scenes[current_id]
        
        # Подгружаем текст текущей сцены (.txt)
        txt_path = os.path.join(quest_path, f"{current_id}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as txt_f:
                story_text = txt_f.read()
        else:
            story_text = "⚠️ Ошибка: Текст этой сцены не найден на диске."
            
        # Рендерим текст книги
        st.subheader(f"📖 {scene_data.get('title', 'Без названия')}")
        st.markdown(story_text)
        st.divider()
        
        # Кнопки выборов
        choices = scene_data.get("choices", [])
        if choices:
            st.write("### 🤔 Ваши действия:")
            for choice in choices:
                if st.button(choice["text"], key=f"btn_{choice['next_scene']}", use_container_width=True):
                    st.session_state.history.append(st.session_state.current_node)
                    st.session_state.current_node = choice["next_scene"]
                    st.rerun()
        else:
            node_lower = current_id.lower()
            if "win" in node_lower or "happy" in node_lower or "success" in node_lower:
                st.balloons()
                st.success("🏆 ИСТИННАЯ КОНЦОВКА: Вы нашли выход и выжили! Солнце встает над проклятым местом.")
            elif "coma" in node_lower or "madness" in node_lower or "hospital" in node_lower or "insane" in node_lower or "ghost" in node_lower:
                st.warning("🧠 ПУГАЮЩАЯ КОНЦОВКА: Вы выбрались... или вам так кажется? Ваш разум заперт внутри собственной головы.")
            else:
                st.error("💀 ЖЕСТОКАЯ СМЕРТЬ: Трансляция оборвалась белым шумом. Конец игры...")
                
        # Боковая панель управления (Откаты и сейвы)
        st.sidebar.divider()
        st.sidebar.write("### 🛠 Управление квестом")
        
        if st.sidebar.button("🔄 Начать сначала", use_container_width=True):
            st.session_state.current_node = "start"
            st.session_state.history = []
            st.rerun()
            
        if st.sidebar.button("⬅️ Шаг назад (Откатить выбор)", use_container_width=True):
            if st.session_state.history:
                st.session_state.current_node = st.session_state.history.pop()
                st.rerun()
            else:
                st.sidebar.error("Вы в самом начале истории!")
                
        st.sidebar.divider()
        st.sidebar.write("### 💾 Система Сохранений")
        slot = st.sidebar.selectbox("Выберите слот сохранения:", ["Слот 1", "Слот 2", "Слот 3"])
        
        if st.sidebar.button("📥 Сохранить путь", use_container_width=True):
            st.session_state.saves[slot] = {
                "node": st.session_state.current_node,
                "history": list(st.session_state.history)
            }
            st.sidebar.success(f"Сохранено в {slot}!")
            
        if st.sidebar.button("📤 Загрузить путь", use_container_width=True):
            if slot in st.session_state.saves:
                save_data = st.session_state.saves[slot]
                st.session_state.current_node = save_data["node"]
                st.session_state.history = list(save_data["history"])
                st.sidebar.success(f"Загружен {slot}!")
                st.rerun()
            else:
                st.sidebar.error(f"Слот {slot} пуст!")
