from flask import Flask, render_template, request, jsonify, send_file
import threading
import os
from datetime import datetime
import logging
from stock_screener import StockScreener
import json
import io

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 全局变量存储筛选状态和结果
screening_status = {
    'status': 'idle',  # idle, running, completed, error
    'progress': 0,
    'message': '',
    'results': [],
    'summary': {},
    'error_message': ''
}

screener = None
screening_thread = None

def progress_callback(progress, message):
    """筛选进度回调函数"""
    global screening_status
    screening_status['progress'] = progress
    screening_status['message'] = message
    logger.info(f"筛选进度: {progress}% - {message}")

def run_screening(target_date):
    """在后台线程中运行筛选"""
    global screening_status, screener
    
    try:
        screening_status['status'] = 'running'
        screening_status['progress'] = 0
        screening_status['message'] = '正在初始化...'
        
        # 创建筛选器实例
        screener = StockScreener()
        
        # 开始筛选
        logger.info(f"开始筛选 {target_date} 的自救股票")
        results = screener.screen_rescue_stocks(target_date, progress_callback)
        
        # 获取筛选摘要
        summary = screener.get_screening_summary()
        
        # 更新状态
        screening_status['status'] = 'completed'
        screening_status['progress'] = 100
        screening_status['message'] = f'筛选完成，找到 {len(results)} 只符合条件的股票'
        screening_status['results'] = results
        screening_status['summary'] = summary
        
        logger.info(f"筛选完成，共找到 {len(results)} 只符合条件的股票")
        
    except Exception as e:
        logger.error(f"筛选过程发生错误: {e}")
        screening_status['status'] = 'error'
        screening_status['error_message'] = str(e)
        screening_status['message'] = f'筛选失败: {str(e)}'

@app.route('/')
def index():
    """主页"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', current_date=current_date)

@app.route('/screen', methods=['POST'])
def start_screening():
    """启动筛选"""
    global screening_thread, screening_status
    
    try:
        data = request.get_json()
        target_date = data.get('date')
        
        if not target_date:
            return jsonify({
                'success': False,
                'message': '请提供筛选日期'
            })
        
        # 检查是否已有筛选在进行
        if screening_status['status'] == 'running':
            return jsonify({
                'success': False,
                'message': '筛选已在进行中，请等待完成'
            })
        
        # 重置状态
        screening_status = {
            'status': 'idle',
            'progress': 0,
            'message': '',
            'results': [],
            'summary': {},
            'error_message': ''
        }
        
        # 启动筛选线程
        screening_thread = threading.Thread(
            target=run_screening,
            args=(target_date,)
        )
        screening_thread.daemon = True
        screening_thread.start()
        
        return jsonify({
            'success': True,
            'message': '筛选已启动'
        })
        
    except Exception as e:
        logger.error(f"启动筛选失败: {e}")
        return jsonify({
            'success': False,
            'message': f'启动筛选失败: {str(e)}'
        })

@app.route('/progress')
def get_progress():
    """获取筛选进度"""
    global screening_status
    
    response_data = {
        'status': screening_status['status'],
        'progress': screening_status['progress'],
        'message': screening_status['message']
    }
    
    if screening_status['status'] == 'error':
        response_data['message'] = screening_status.get('error_message', '未知错误')
    
    return jsonify(response_data)

@app.route('/results')
def get_results():
    """获取筛选结果"""
    global screening_status
    
    if screening_status['status'] != 'completed':
        return jsonify({
            'success': False,
            'message': '筛选尚未完成或发生错误'
        })
    
    return jsonify({
        'success': True,
        'results': screening_status['results'],
        'summary': screening_status['summary']
    })

@app.route('/export/<format>', methods=['POST'])
def export_results(format):
    """导出筛选结果"""
    global screener, screening_status
    
    if screening_status['status'] != 'completed' or not screener:
        return jsonify({
            'success': False,
            'message': '没有可导出的结果'
        }), 400
    
    try:
        if format.lower() == 'excel':
            filename = screener.export_results_to_excel()
            if filename:
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=os.path.basename(filename),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        elif format.lower() == 'csv':
            filename = screener.export_results_to_csv()
            if filename:
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=os.path.basename(filename),
                    mimetype='text/csv'
                )
        
        return jsonify({
            'success': False,
            'message': '导出失败'
        }), 500
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }), 500

@app.route('/status')
def get_status():
    """获取服务器状态"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'screening_status': screening_status['status']
    })

@app.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500

def create_directories():
    """创建必要的目录"""
    directories = ['results', 'static', 'templates']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"创建目录: {directory}")

if __name__ == '__main__':
    # 创建必要的目录
    create_directories()
    
    # 启动应用
    logger.info("启动A股自救股票筛选工具...")
    logger.info("访问 http://localhost:5000 开始使用")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # 生产环境建议设为False
        threaded=True
    )