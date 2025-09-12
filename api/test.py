from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    """简单的测试端点"""
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'timestamp': '2025-09-12'
    })

if __name__ == '__main__':
    app.run(debug=True)