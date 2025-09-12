from flask import Flask, jsonify, render_template, request
import os
from datetime import datetime

app = Flask(__name__)

# 配置模板和静态文件路径
template_dir = os.path.join(os.path.dirname(__file__), '..', 'stock_screener', 'templates')
static_dir = os.path.join(os.path.dirname(__file__), '..', 'stock_screener', 'static')

app.template_folder = template_dir
app.static_folder = static_dir

@app.route('/')
def index():
    """主页"""
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        return render_template('index.html', current_date=current_date)
    except Exception as e:
        return jsonify({
            'error': 'Template loading failed',
            'message': str(e),
            'template_folder': app.template_folder
        }), 500

@app.route('/test')
def test():
    """测试端点"""
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'timestamp': datetime.now().isoformat(),
        'paths': {
            'template_folder': app.template_folder,
            'static_folder': app.static_folder
        }
    })

@app.route('/screen', methods=['POST'])
def start_screening():
    """筛选功能 - 暂时返回模拟数据"""
    try:
        data = request.get_json()
        target_date = data.get('date')
        
        if not target_date:
            return jsonify({
                'success': False,
                'message': '请提供筛选日期'
            })
        
        # 模拟结果数据
        mock_results = [
            {
                'code': '000001',
                'name': '平安银行',
                'current_price': 15.50,
                'change_pct': 2.3,
                'volume': 1234567,
                'turnover': 19135000,
                'market_cap': 30000000000
            },
            {
                'code': '000002',
                'name': '万科A',
                'current_price': 18.20,
                'change_pct': 1.8,
                'volume': 987654,
                'turnover': 17975000,
                'market_cap': 20000000000
            }
        ]
        
        mock_summary = {
            'total_count': 2,
            'avg_change_pct': 2.05,
            'avg_volume': 1111110,
            'total_market_cap': 50000000000
        }
        
        return jsonify({
            'success': True,
            'status': 'completed',
            'message': f'筛选完成，找到 {len(mock_results)} 只符合条件的股票（模拟数据）',
            'results': mock_results,
            'summary': mock_summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'筛选失败: {str(e)}'
        }), 500

@app.route('/progress')
def get_progress():
    """获取筛选进度"""
    return jsonify({
        'status': 'idle',
        'progress': 0,
        'message': '请点击开始筛选'
    })

@app.route('/results')
def get_results():
    """获取筛选结果"""
    return jsonify({
        'success': False,
        'message': '请重新执行筛选获取结果'
    })

@app.route('/export/excel', methods=['POST'])
def export_excel():
    """导出Excel"""
    return jsonify({
        'success': False,
        'message': '导出功能暂时不可用'
    }), 501

@app.route('/export/csv', methods=['POST'])
def export_csv():
    """导出CSV"""
    return jsonify({
        'success': False,
        'message': '导出功能暂时不可用'
    }), 501

@app.route('/status')
def get_status():
    """获取服务器状态"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'environment': 'vercel-simplified'
    })

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'message': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误',
        'error': str(error)
    }), 500

if __name__ == '__main__':
    app.run(debug=True)