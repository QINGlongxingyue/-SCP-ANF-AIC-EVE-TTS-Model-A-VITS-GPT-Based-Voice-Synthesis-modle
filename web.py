# -*- coding: utf-8 -*-
"""
VITS TTS 双模式系统
功能：终端互动 + Web界面 同时运行
"""
import sys
import os
import json
import requests
import threading
import webbrowser
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file

# 配置
TTS_URL = "http://localhost:3752/"
HISTORY_FILE = "chat_history.json"
AUDIO_DIR = "audio_cache"
WEB_PORT = 5000

# ========== Web界面模板 ==========
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCP AIC EVE VITS TTS Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-tertiary: #1a2234;
            --accent-cyan: #00f0ff;
            --accent-purple: #a855f7;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --border-glow: rgba(0, 240, 255, 0.3);
        }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        .grid-bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: 
                linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none; z-index: 0;
        }
        .container { position: relative; z-index: 1; max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 {
            font-size: 2.5rem; font-weight: 300; letter-spacing: 8px; text-transform: uppercase;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .header .subtitle { color: var(--text-secondary); font-size: 0.9rem; letter-spacing: 2px; margin-top: 10px; }
        .status-bar { display: flex; justify-content: center; gap: 30px; margin-top: 20px; }
        .status-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent-cyan); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .main-panel { background: var(--bg-secondary); border: 1px solid var(--border-glow); border-radius: 16px; padding: 30px; }
        .input-section { margin-bottom: 30px; }
        .input-section label { display: block; margin-bottom: 12px; color: var(--text-secondary); font-size: 0.85rem; letter-spacing: 1px; }
        .input-wrapper { display: flex; gap: 12px; }
        .text-input { flex: 1; background: var(--bg-tertiary); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 16px 20px; color: var(--text-primary); font-size: 1rem; }
        .text-input:focus { outline: none; border-color: var(--accent-cyan); box-shadow: 0 0 20px rgba(0, 240, 255, 0.15); }
        .btn { padding: 16px 32px; border: none; border-radius: 10px; font-size: 0.95rem; cursor: pointer; transition: all 0.3s; }
        .btn-primary { background: linear-gradient(135deg, var(--accent-cyan), #0891b2); color: var(--bg-primary); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 240, 255, 0.3); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .audio-player { margin-top: 20px; display: none; }
        .audio-player.show { display: block; }
        .audio-player audio { width: 100%; height: 50px; border-radius: 8px; }
        .history-section { margin-top: 30px; }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .section-title { color: var(--text-secondary); font-size: 0.85rem; }
        .btn-small { padding: 8px 16px; font-size: 0.8rem; background: transparent; border: 1px solid rgba(255,255,255,0.2); color: var(--text-secondary); border-radius: 6px; cursor: pointer; }
        .btn-small:hover { border-color: var(--accent-cyan); color: var(--accent-cyan); }
        .history-list { max-height: 400px; overflow-y: auto; }
        .history-item { background: var(--bg-tertiary); border-radius: 10px; padding: 16px; margin-bottom: 12px; border-left: 3px solid var(--accent-cyan); }
        .history-item:hover { transform: translateX(5px); border-left-color: var(--accent-purple); }
        .history-time { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 8px; }
        .history-text { font-size: 0.95rem; line-height: 1.5; }
        .history-audio { margin-top: 10px; }
        .history-audio audio { width: 100%; height: 36px; }
        .loading { display: none; align-items: center; gap: 10px; color: var(--accent-cyan); }
        .loading.show { display: flex; }
        .spinner { width: 20px; height: 20px; border: 2px solid transparent; border-top-color: var(--accent-cyan); border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-tertiary); }
        ::-webkit-scrollbar-thumb { background: var(--accent-cyan); border-radius: 3px; }
    </style>
</head>
<body>
    <div class="grid-bg"></div>
    <div class="container">
        <div class="header">
            <h1>SCP-AIC-EVE-VITS-TTS</h1>
            <div class="subtitle">Neural Voice Synthesis System</div>
            <div class="status-bar">
                <div class="status-item"><div class="status-dot"></div><span>System Online</span></div>
                <div class="status-item"><span id="historyCount">0</span> Records</div>
            </div>
        </div>
        <div class="main-panel">
            <div class="input-section">
                <label>Text Input</label>
                <div class="input-wrapper">
                    <input type="text" class="text-input" id="textInput" placeholder="输入要合成的文本..." onkeypress="if(event.key==='Enter')generateTTS()">
                    <button class="btn btn-primary" id="generateBtn" onclick="generateTTS()">Generate</button>
                </div>
            </div>
            <div class="loading" id="loading"><div class="spinner"></div><span>Processing...</span></div>
            <div class="audio-player" id="audioPlayer"><audio id="audio" controls></audio></div>
            <div class="history-section">
                <div class="section-header">
                    <span class="section-title">History</span>
                    <button class="btn btn-small" onclick="clearHistory()">Clear All</button>
                </div>
                <div class="history-list" id="historyList"></div>
            </div>
        </div>
    </div>
    <script>
        function loadHistory() {
            fetch('/api/history').then(r => r.json()).then(data => {
                document.getElementById('historyCount').textContent = data.length;
                renderHistory(data);
            });
        }
        function renderHistory(history) {
            const c = document.getElementById('historyList');
            if (!history.length) { c.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:20px;">暂无记录</p>'; return; }
            c.innerHTML = history.slice().reverse().map(item => `
                <div class="history-item">
                    <div class="history-time">${item.timestamp.split('T')[1].split('.')[0]}</div>
                    <div class="history-text">${item.content.replace(/</g,'&lt;')}</div>
                    ${item.audio ? `<div class="history-audio"><audio controls src="/audio/${item.audio.split('/').pop()}"></audio></div>` : ''}
                </div>
            `).join('');
        }
        function generateTTS() {
            const text = document.getElementById('textInput').value.trim();
            if (!text) return;
            const btn = document.getElementById('generateBtn');
            const loading = document.getElementById('loading');
            btn.disabled = true; loading.classList.add('show');
            fetch('/api/tts', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text})})
            .then(r => r.json()).then(data => {
                btn.disabled = false; loading.classList.remove('show');
                if (data.audio) {
                    document.getElementById('audio').src = '/audio/' + data.audio;
                    document.getElementById('audioPlayer').classList.add('show');
                    document.getElementById('textInput').value = '';
                    loadHistory();
                } else { alert(data.error || '生成失败'); }
            }).catch(err => { btn.disabled = false; loading.classList.remove('show'); alert('请求失败'); });
        }
        function clearHistory() { fetch('/api/history/clear', {method: 'POST'}).then(() => loadHistory()); }
        loadHistory();
    </script>
</body>
</html>
'''

# ========== Flask应用 ==========
app = Flask(__name__)

class VTTSWeb:
    def __init__(self):
        self.history = []
        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)
        self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"[记忆] 已加载 {len(self.history)} 条历史记录")
            except:
                self.history = []

    def save_history(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def generate_tts(self, text, language="zh"):
        try:
            print(f"[TTS] 正在生成语音: {text[:30]}...")
            response = requests.post(TTS_URL, json={"text": text, "text_language": language}, timeout=50)
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                audio_file = os.path.join(AUDIO_DIR, f"audio_{timestamp}.wav")
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                print(f"[下载] 音频已保存: {audio_file}")
                return audio_file
            else:
                print(f"[错误] TTS失败 HTTP {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("[错误] TTS服务连接失败")
            return None
        except Exception as e:
            print(f"[错误] {type(e).__name__}: {e}")
            return None

    def add_to_history(self, role, content, audio_file=None):
        record = {"timestamp": datetime.now().isoformat(), "role": role, "content": content, "audio": audio_file}
        self.history.append(record)
        self.save_history()
        return record

    def show_history(self, last_n=10):
        print(f"\n{'='*50}")
        for r in self.history[-last_n:]:
            t = r['timestamp'].split('T')[1].split('.')[0]
            print(f"[{t}] {r['content']}")
        print(f"{'='*50}\n")

vts = VTTSWeb()

# ========== Web路由 ==========
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tts', methods=['POST'])
def api_tts():
    text = request.get_json().get('text', '')
    if not text:
        return jsonify({'error': '请输入文本'})
    audio_file = vts.generate_tts(text)
    if audio_file:
        vts.add_to_history("user", text, audio_file)
        return jsonify({'success': True, 'audio': os.path.basename(audio_file)})
    return jsonify({'error': 'TTS生成失败'})

@app.route('/api/history')
def api_history():
    return jsonify(vts.history)

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    vts.history = []
    vts.save_history()
    return jsonify({'success': True})

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename))

# ========== 终端模式 ==========
def run_terminal():
    print("\n" + "="*60)
    print("  VITS TTS 双模式系统")
    print("="*60)
    print(f"  Web界面已启动: http://127.0.0.1:{WEB_PORT}")
    print("="*60)
    print("命令说明:")
    print("  - 直接输入文本 -> 生成语音")
    print("  - 'history'    -> 查看历史")
    print("  - 'clear'      -> 清空历史")
    print("  - 'quit'       -> 退出")
    print("="*60 + "\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[退出]")
            os._exit(0)

        if not user_input:
            continue
        if user_input.lower() == 'quit':
            print("[退出] 再见!")
            os._exit(0)
        elif user_input.lower() == 'history':
            vts.show_history()
        elif user_input.lower() == 'clear':
            vts.history = []
            vts.save_history()
            print("[记忆] 已清空")
        else:
            audio = vts.generate_tts(user_input)
            vts.add_to_history("user", user_input, audio)

def start_web():
    """后台启动Flask"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

def open_default_browser(url):
    """
    使用系统默认浏览器打开指定URL
    Windows下底层通过cmd调用默认浏览器
    """
    try:
        webbrowser.open(url, new=0, autoraise=True)
    except Exception as e:
        print(f"[警告] 打开浏览器失败: {e}")

if __name__ == "__main__":
    # Web服务放后台线程
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    
    url = f"http://127.0.0.1:{WEB_PORT}"
    print(f"\n[Web] {url} 已在后台启动")
    print("[提示] 若浏览器未自动打开，可手动访问上述地址，或在终端中按住Ctrl并左键点击链接打开。")
    
    # 自动打开默认浏览器
    open_default_browser(url)
    
    # 主线程跑终端
    run_terminal()
