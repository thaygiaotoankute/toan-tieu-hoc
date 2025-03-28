from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import os
import json
import requests
from io import BytesIO
import markdown
import tempfile
import subprocess

app = Flask(__name__)

# Cấu hình Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Dữ liệu dạng toán
math_topics = {
    "lop1": {
        "name": "Toán Lớp 1 Chân Trời Sáng Tạo",
        "topics": [
            {"id": "1-1", "name": "1. Định hướng không gian cơ bản"},
            {"id": "1-2", "name": "2. Các số đến 10 và số 0"},
            {"id": "1-3", "name": "3. Phép cộng, phép trừ trong phạm vi 10"},
            {"id": "1-4", "name": "4. Các số đến 20"},
            {"id": "1-5", "name": "5. Phép cộng, phép trừ trong phạm vi 20"},
            {"id": "1-6", "name": "6. Hình học cơ bản"}
        ]
    },
    "lop2": {
        "name": "Toán Lớp 2 Chân Trời Sáng Tạo",
        "topics": [
            {"id": "2-1", "name": "1. Ôn tập và bổ sung"},
            {
                "id": "2-2", 
                "name": "2. Phép cộng, phép trừ qua 10 trong phạm vi 20",
                "subtopics": [
                    {"id": "2-2-1", "name": "2.1. Phép cộng có tổng bằng 10"},
                    {"id": "2-2-2", "name": "2.2. Các dạng cộng với một số"},
                    {"id": "2-2-3", "name": "2.3. Phép trừ có hiệu bằng 10"},
                    {"id": "2-2-4", "name": "2.4. 11 trừ đi một số"}
                ]
            },
            {"id": "2-3", "name": "3. Hình học cơ bản"},
            {
                "id": "2-4",
                "name": "4. Phép cộng, phép trừ có nhớ trong phạm vi 100",
                "subtopics": [
                    {"id": "2-4-1", "name": "4.1. Phép cộng có tổng là số tròn chục"},
                    {"id": "2-4-2", "name": "4.2. Phép cộng có nhớ trong phạm vi 100"},
                    {"id": "2-4-3", "name": "4.3. Phép trừ có số bị trừ là số tròn chục"},
                    {"id": "2-4-4", "name": "4.4. Phép trừ có nhớ trong phạm vi 100"}
                ]
            },
            {"id": "2-5", "name": "5. Phép nhân, phép chia"},
            {"id": "2-6", "name": "6. Các số đến 1000"},
            {
                "id": "2-7",
                "name": "7. Phép cộng, phép trừ trong phạm vi 1000",
                "subtopics": [
                    {"id": "2-7-1", "name": "7.1. Phép cộng không nhớ trong phạm vi 1000"},
                    {"id": "2-7-2", "name": "7.2. Phép trừ không nhớ trong phạm vi 1000"},
                    {"id": "2-7-3", "name": "7.3. Đơn vị đo lường - Ki-lô-gam"},
                    {"id": "2-7-4", "name": "7.4. Phép cộng có nhớ trong phạm vi 1000"},
                    {"id": "2-7-5", "name": "7.5. Phép trừ có nhớ trong phạm vi 1000"}
                ]
            }
        ]
    }
}

@app.route('/')
def index():
    return render_template('index.html', math_topics=math_topics)

@app.route('/generate', methods=['POST'])
def generate_questions():
    topic = request.form.get('topic')
    
    if not topic:
        return jsonify({"error": "Vui lòng chọn dạng toán"}), 400
    
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key chưa được cấu hình"}), 500
    
    try:
        # Tạo prompt cho Gemini
        prompt = f"""
        Hãy tạo 5 câu hỏi toán tiểu học cho dạng toán sau: {topic}
        
        Mỗi câu hỏi cần có định dạng sau:
        1. [Câu hỏi]
        Đáp án: [Đáp án]
        Hướng dẫn giải: [Cách giải chi tiết]
        
        Đảm bảo câu hỏi phù hợp với học sinh tiểu học và cung cấp hướng dẫn giải dễ hiểu.
        """
        
        # Gọi Gemini API
        model = genai.GenerativeModel(
            model_name='gemini-2.5-pro-exp-03-25',
            generation_config={
                'temperature': 0.2,
                'top_p': 0.95,
                'max_output_tokens': 4096,
            }
        )
        response = model.generate_content(prompt)
        
        # Trả về kết quả
        return jsonify({"questions": response.text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/export', methods=['POST'])
def export_to_word():
    content = request.form.get('content')
    title = request.form.get('title', 'Câu hỏi Toán tiểu học')
    
    if not content:
        return jsonify({"error": "Không có nội dung để xuất"}), 400
    
    try:
        # Tạo file markdown tạm thời
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as md_file:
            md_file_path = md_file.name
            md_content = f"# {title}\n\n{content}"
            md_file.write(md_content.encode('utf-8'))
        
        # Tạo file docx đích
        docx_file_path = tempfile.mktemp(suffix='.docx')
        
        # Sử dụng pandoc để chuyển đổi
        subprocess.run(['pandoc', md_file_path, '-o', docx_file_path], check=True)
        
        # Xóa file markdown tạm thời
        os.unlink(md_file_path)
        
        # Trả về file Word
        return send_file(
            docx_file_path, 
            as_attachment=True,
            download_name=f"{title.replace(' ', '_')}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    
    except subprocess.CalledProcessError:
        return jsonify({"error": "Lỗi khi chuyển đổi file. Hãy đảm bảo Pandoc đã được cài đặt."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
