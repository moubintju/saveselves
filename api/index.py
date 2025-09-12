from flask import Flask, jsonify, render_template, request
import os
import sys
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 添加股票筛选模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock_screener'))

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
    """执行股票筛选 - 支持真实数据和模拟数据"""
    try:
        data = request.get_json()
        target_date = data.get('date')
        use_real_data = data.get('use_real_data', False)
        
        if not target_date:
            return jsonify({
                'success': False,
                'message': '请提供筛选日期'
            })
        
        logger.info(f"开始筛选 {target_date} 的股票，使用真实数据: {use_real_data}")
        
        if use_real_data:
            # 尝试使用真实数据
            try:
                from stock_screener import StockScreener
                
                logger.info("正在创建股票筛选器...")
                screener = StockScreener()
                
                logger.info("开始执行股票筛选...")
                # 限制股票数量以避免Vercel超时
                results = screener.screen_rescue_stocks(target_date, max_stocks=50)
                summary = screener.get_screening_summary()
                
                logger.info(f"筛选完成，找到 {len(results)} 只符合条件的股票")
                
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'message': f'筛选完成，找到 {len(results)} 只符合条件的股票',
                    'results': results,
                    'summary': summary
                })
                
            except Exception as real_data_error:
                logger.error(f"真实数据筛选失败: {real_data_error}")
                # 如果真实数据失败，回退到模拟数据
                return get_mock_screening_result(target_date, str(real_data_error))
        else:
            # 使用模拟数据
            return get_mock_screening_result(target_date)
        
    except Exception as e:
        logger.error(f"筛选过程发生错误: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'筛选失败: {str(e)}'
        }), 500

def get_mock_screening_result(target_date, error_msg=None):
    """获取模拟筛选结果"""
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
        },
        {
            'code': '600036',
            'name': '招商银行',
            'current_price': 42.10,
            'change_pct': 1.5,
            'volume': 2100000,
            'turnover': 88410000,
            'market_cap': 109500000000
        }
    ]
    
    mock_summary = {
        'total_count': len(mock_results),
        'avg_change_pct': 1.87,
        'avg_volume': 1395404,
        'total_market_cap': 159500000000
    }
    
    message = f'筛选完成，找到 {len(mock_results)} 只符合条件的股票（模拟数据）'
    if error_msg:
        message += f' - 真实数据获取失败: {error_msg[:100]}...'
    
    return jsonify({
        'success': True,
        'status': 'completed',
        'message': message,
        'results': mock_results,
        'summary': mock_summary
    })

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