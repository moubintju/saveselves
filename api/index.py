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
    """执行股票筛选 - 分批处理所有A股"""
    try:
        data = request.get_json()
        target_date = data.get('date')
        batch_start = data.get('batch_start', 0)  # 批次开始位置
        batch_size = data.get('batch_size', 20)   # 每批处理数量
        
        if not target_date:
            return jsonify({
                'success': False,
                'message': '请提供筛选日期'
            })
        
        logger.info(f"开始筛选 {target_date} 的股票，批次 {batch_start}-{batch_start + batch_size}")
        
        try:
            from stock_screener import StockScreener
            
            logger.info("正在创建股票筛选器...")
            screener = StockScreener()
            
            logger.info("开始执行股票筛选...")
            # 分批处理，避免超时
            batch_results = screener.screen_rescue_stocks_batch(
                target_date, 
                batch_start=batch_start, 
                batch_size=batch_size
            )
            
            logger.info(f"批次处理完成")
            
            return jsonify({
                'success': True,
                'status': 'batch_completed',
                'batch_start': batch_start,
                'batch_size': batch_size,
                'results': batch_results['results'],
                'total_stocks': batch_results['total_stocks'],
                'processed_count': batch_results['processed_count'],
                'has_more': batch_results['has_more'],
                'message': f'已处理 {batch_results["processed_count"]}/{batch_results["total_stocks"]} 只股票，找到 {len(batch_results["results"])} 只符合条件的股票'
            })
            
        except Exception as e:
            logger.error(f"股票筛选失败: {e}")
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'筛选失败: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"筛选过程发生错误: {e}")
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