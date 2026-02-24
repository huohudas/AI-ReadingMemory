import streamlit as st
from openai import OpenAI
import re
import os

st.set_page_config(page_title="微信读书 AI 前情提要", layout="wide")

st.markdown("""
<style>
    header[data-testid="stHeader"] {display: none;}
    footer {display: none;}
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 1rem;}
    
    /* 侧边栏：微信读书亮色主题 */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #333333 !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
    section[data-testid="stSidebar"] textarea {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        background-color: #1677FF !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 20px !important;
        transition: all 0.3s ease !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        background-color: #4096FF !important;
        box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3) !important;
        transform: translateY(-1px);
    }
    
    /* 删除按钮文字改为白色 */
    section[data-testid="stSidebar"] button[key^="del_"] {
        color: #FFFFFF !important;
    }
    
    /* 主容器宽度 */
    [data-testid="stAppViewBlockContainer"] {
        max-width: 1200px !important;
        padding-top: 2rem !important;
    }
    
    .phone-content { color: #333333; font-size: 17px; line-height: 1.8; text-align: justify; }
    .phone-content p { text-indent: 2em; margin-bottom: 0.8em; }
    .book-title {
        font-size: 20px; font-weight: bold; color: #1A1A1A; text-align: center;
        margin-bottom: 1.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #E0E0E0;
    }
    .hint-banner {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFF3CD 100%);
        border-radius: 12px; padding: 10px 15px; margin-bottom: 15px;
        border-left: 4px solid #FFB800; font-size: 13px; color: #856404; text-align: center;
    }
    .ai-card {
        background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #F0F0F0;
    }
    .ai-card-title { font-size: 16px; font-weight: 600; color: #1A1A1A; margin-bottom: 12px; }
    .ai-card-content { font-size: 15px; line-height: 1.7; color: #444444; }
    .reading-progress {
        font-size: 12px; color: #999; text-align: center; margin-top: 16px;
        padding-top: 12px; border-top: 1px solid #E8E8E8;
    }
    
    .cot-card {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #00E676;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .cot-content {
        font-size: 15px;
        line-height: 1.8;
        color: #444444;
    }
    
    /* ==========================================
       优先级布局：侧边栏 > 手机壳 > AI面板
       ========================================== */
    /* 1. 侧边栏：最高优先级，不可压缩 */
    section[data-testid="stSidebar"] {
        z-index: 9999 !important;
        flex-shrink: 0 !important;
    }
    /* 2. 主内容容器：允许换行以保护刚性元素 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: wrap !important;
        align-items: flex-start !important;
        gap: 20px !important;
    }
    /* 3. 手机壳：刚性布局，锁死尺寸 */
    [data-testid="stHorizontalBlock"] > div:first-child,
    section[data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:first-child {
        /* 锁死尺寸：绝不压缩 */
        flex: 0 0 390px !important;
        width: 390px !important;
        min-width: 390px !important;
        height: 780px !important;
        /* 外观样式 */
        background-color: #F7F7F4 !important;
        border: 12px solid #111111 !important;
        border-radius: 40px !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.45) !important;
        padding: 24px 16px !important;
        box-sizing: border-box !important;
        overflow-y: auto !important;
        /* 换行后依然保持靠左 */
        margin-left: 0 !important;
    }
    /* 4. AI 面板：弹性布局，空间不够就换行 */
    [data-testid="stHorizontalBlock"] > div:last-child {
        flex: 1 1 300px !important;
        min-width: 300px !important;
        margin-top: 0 !important;
    }
    /* 5. 主容器内边距 */
    [data-testid="stAppViewBlockContainer"] {
        padding: 2rem !important;
    }
    /* 6. 内部内容 padding */
    [data-testid="stHorizontalBlock"] > div:first-child > div {
        padding: 0 !important;
    }
    
    /* 忽略按钮：灰色低调全宽，无任何定位 */
    :not([data-testid="stSidebar"]) button[key="ignore_btn"],
    :not([data-testid="stSidebar"]) [data-testid="stButton"]:has(button[data-testid="baseButton-secondary"]) button {
        background-color: transparent !important;
        border: 1px solid #E8E8E8 !important;
        color: #CCCCCC !important;
        font-size: 12px !important;
        border-radius: 8px !important;
        height: 28px !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_parse_book(filepath="book1.txt"):
    if not os.path.exists(filepath):
        return [{"title": "演示章节", "content": "未能找到 book1.txt 文件，请检查路径。"}]
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except:
        with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
            text = f.read()

    pattern = re.compile(r'^\s*第[一二三四五六七八九十百千万0-9零]+\s*[章回].*?$', re.MULTILINE)
    matches = list(pattern.finditer(text))
    
    chapters = []
    if not matches:
        for i in range(0, min(len(text), 50000), 5000):
            chapters.append({"title": f"第 {i//5000 + 1} 部分", "content": text[i:i+5000]})
        return chapters

    for i in range(len(matches)):
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        title = matches[i].group().strip()
        content = text[start_idx:end_idx].strip()
        if len(content) > 100:
            chapters.append({"title": title, "content": content})
    return chapters

def get_api_key():
    api_key = None
    if os.path.exists("api_key.txt"):
        try:
            with open("api_key.txt", "r", encoding="utf-8") as f:
                api_key = f.read().strip()
        except Exception:
            pass
    elif os.path.exists(".streamlit/secrets.toml"):
        try:
            if "DEEPSEEK_API_KEY" in st.secrets:
                api_key = st.secrets["DEEPSEEK_API_KEY"]
        except Exception:
            pass
    return api_key

def main():
    chapters = load_and_parse_book("book1.txt")
    chapter_titles = [ch["title"] for ch in chapters]
    
    with st.sidebar:
        st.markdown("### 🎛️ 后台控制台")
        st.markdown("---")
        
        current_chapter = st.selectbox(
            "📖 章节翻页选择器",
            options=chapter_titles if chapter_titles else ["暂无章节"],
            index=0
        )
        current_idx = chapter_titles.index(current_chapter) if current_chapter in chapter_titles else 0
        
        st.markdown("---")
        
        days_passed = st.slider(
            "⏰ 模拟时光机 (天)",
            min_value=1,
            max_value=15,
            value=1,
            step=1
        )
        
        st.markdown("---")
        st.markdown("### ✍️ 历史划线管理")
        
        if "highlights" not in st.session_state:
            st.session_state.highlights = []
        
        new_hl = st.text_area("添加新划线", height=80, placeholder="在此粘贴前文的划线句子...")
        if st.button("+ 导入划线", use_container_width=True):
            if new_hl.strip():
                st.session_state.highlights.append(new_hl.strip())
                st.rerun()
        
        if st.session_state.highlights:
            st.markdown("<div style='color:#333333; font-size:14px; margin-bottom:10px;'>已存划线记录：</div>", unsafe_allow_html=True)
            for i, hl in enumerate(st.session_state.highlights):
                col1, col2 = st.columns([5, 1])
                col1.caption(f"{i+1}. {hl[:20]}..." if len(hl) > 20 else f"{i+1}. {hl}")
                if col2.button("❌", key=f"del_{i}", help="删除此划线"):
                    st.session_state.highlights.pop(i)
                    st.rerun()
        else:
            st.caption("暂无历史划线记录")
        
        st.markdown("---")
        st.markdown(f"<div style='color: #666666; font-size: 12px; text-align: center; margin-top: 10px;'>已过 {days_passed} 天未阅读</div>", unsafe_allow_html=True)
    
    if chapters and len(chapters) > 0:
        if "ignored_recap" not in st.session_state:
            st.session_state.ignored_recap = False
        
        # 切换章节时重置忽略状态
        if st.session_state.get("last_chapter_ignore") != current_chapter:
            st.session_state["last_chapter_ignore"] = current_chapter
            st.session_state.ignored_recap = False
        
        col_phone, col_ai_board = st.columns([1, 1.3], gap="large")
        
        thinking_process = ""
        
        with col_phone:
            if st.session_state.get("last_chapter") != current_chapter:
                st.session_state["last_chapter"] = current_chapter
                import streamlit.components.v1 as components
                components.html("""
                <script>
                (function() {
                    function resetScroll() {
                        var cols = window.parent.document.querySelectorAll(
                            '[data-testid="column"]'
                        );
                        for (var i = 0; i < cols.length; i++) {
                            cols[i].scrollTop = 0;
                        }
                    }
                    setTimeout(resetScroll, 300);
                    setTimeout(resetScroll, 600);
                })();
                </script>
                """, height=1)
            
            st.markdown('<div class="book-title">📖 斗破苍穹</div>', unsafe_allow_html=True)
            
            if days_passed >= 3 and current_idx > 0 and not st.session_state.ignored_recap:
                st.markdown(f"""
                <div style="
                    background:linear-gradient(135deg,#FFF9E6 0%,#FFF3CD 100%);
                    border-radius:12px; padding:8px 12px;
                    border-left:4px solid #FFB800;
                    margin-bottom:4px;
                ">
                    <span style="font-size:14px; color:#856404;">
                        💡 已过 {days_passed} 天，AI 已备好前情提要
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("✕ 不需要回顾，直接阅读", key="ignore_btn", use_container_width=True):
                    st.session_state.ignored_recap = True
                    st.session_state.ai_response = None
                    st.rerun()
                
                if "ai_response" not in st.session_state:
                    st.session_state.ai_response = None
                
                if st.button("✨ 点击生成专属回忆", key="generate_btn", use_container_width=True):
                    api_key = get_api_key()
                    if not api_key:
                        st.error("⚠️ 未找到 API Key，请在本地创建 api_key.txt 或在云端配置 Secrets。")
                    else:
                        with st.spinner('AI 正在重温前文...'):
                            try:
                                client = OpenAI(
                                    api_key=api_key,
                                    base_url="https://api.deepseek.com/v1"
                                )
                                
                                context_text = "\n\n".join([f"【{ch['title']}】\n{ch['content'][:2000]}" for ch in chapters[max(0, current_idx-3):current_idx]])
                                if not context_text:
                                    context_text = "当前为书籍开头，暂无前文内容。"
                                
                                highlights_text = "\n".join([f"{i+1}. {hl}" for i, hl in enumerate(st.session_state.highlights)])
                                highlight_context = f"\n以下是用户的历史划线记录：\n{highlights_text}\n" if st.session_state.highlights else ""
                                
                                system_prompt = f"""
你是一个专业的沉浸式阅读助手。
请基于以下前文背景(Context)，为中断阅读多日的读者生成前情提要。{highlight_context}

请严格按照以下三个板块输出你的回答（绝对不要输出任何客套话或阅读寄语）：

【AI分析过程】
（请用50字左右分析：根据用户的历史划线记录，推测该用户更关注哪些角色、情感或剧情主线？如果用户没有划线，请说明将进行全局摘要。你接下来的剧情回顾必须侧重于这些偏好点。）

【剧情回顾】
（结合上面的分析侧重点，用 100-150 字精炼总结前文最核心的剧情冲突与进展。）

【主要人物现状】
（列举 2-3 位出场的核心人物，用一句话概括他们当下的处境、实力阶段或核心目标。）

[前文背景 Context]:
{context_text}
"""
                                
                                response = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[
                                        {"role": "system", "content": system_prompt}
                                    ],
                                    temperature=0.7,
                                    max_tokens=600
                                )
                                
                                st.session_state.ai_response = response.choices[0].message.content
                                
                            except Exception as e:
                                st.error(f"API 调用失败: {str(e)}")
                
                if st.session_state.ai_response and not st.session_state.ignored_recap:
                    ai_result = st.session_state.ai_response
                    
                    if "【AI分析过程】" in ai_result and "【剧情回顾】" in ai_result:
                        parts = ai_result.split("【剧情回顾】")
                        thinking_process = parts[0].replace("【AI分析过程】", "").strip()
                        final_recap = "【剧情回顾】\n" + parts[1].strip()
                    else:
                        thinking_process = "未能成功解析大模型的思考过程。"
                        final_recap = ai_result
                    
                    final_recap_html = final_recap.replace('\n', '<br>')
                    st.markdown(f"""
                    <div class="ai-card">
                        <div class="ai-card-title">🤖 AI 专属回顾</div>
                        <div class="ai-card-content">{final_recap_html}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("💬 仍然想不起来？向 AI 深度追问前文细节"):
                        st.info("💡 渐进式交互演示：真实产品中，用户可在此输入具体问题（如：'萧炎的三年之约是怎么回事？'），AI 将基于全书 RAG 检索精准解答。")
                        st.chat_input("向 AI 提问前文细节 (Demo 演示暂不调用接口)...", disabled=True)
            
            if chapters and current_idx < len(chapters):
                current_content = chapters[current_idx]['content']
            else:
                current_content = "暂无内容"
            
            paragraphs = current_content.strip().split('\n')
            content_html = ""
            for p in paragraphs:
                if p.strip():
                    content_html += f"<p>{p.strip()}</p>"
            
            st.markdown(f"""
            <div class="phone-content">
                {content_html}
            </div>
            """, unsafe_allow_html=True)
            
            total_chapters = len(chapters)
            st.markdown(f"""
            <div class="reading-progress">
                📖 {current_chapter} · 第 {current_idx + 1}/{total_chapters} 章
            </div>
            """, unsafe_allow_html=True)
        
        with col_ai_board:
            st.markdown("<h3 style='color: #2B2B2B; margin-bottom: 20px; padding-top: 50px;'>🧠 AI 分析与思考链路 (CoT)</h3>", unsafe_allow_html=True)
            
            if 'thinking_process' in locals() and thinking_process:
                st.info("💡 以下是大模型基于用户历史划线做出的深层意图推演：")
                st.markdown(f"""
                <div class="cot-card">
                    <div class="cot-content">{thinking_process}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.success("✨ 【Demo 架构展示】通过透出 Chain of Thought，清晰展示系统如何利用注意力权重，实现千人千面的个性化前情提要。")
            else:
                st.markdown("<div style='color: #888888; text-align: left; margin-top: 20px; font-style: italic;'>⬅️ 请在左侧手机模拟器中点击生成，此处将实时透出大模型推理过程。</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
