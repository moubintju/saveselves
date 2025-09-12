from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock_screener'))
from stock_screener import StockScreener
import json
import io
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

@app.route('/')
def index():
    """主页"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    template_path = os.path.join(os.path.dirname(__file__), '..', 'stock_screener', 'templates')
    app.template_folder = template_path
    return render_template('index.html', current_date=current_date)

@app.route('/screen', methods=['POST'])
def start_screening():
    """执行筛选 - 同步处理"""
    try:
        data = request.get_json()
        target_date = data.get('date')
        
        if not target_date:
            return jsonify({
                'success': False,
                'message': '请提供筛选日期'
            })
        
        logger.info(f"开始筛选 {target_date} 的自救股票")
        
        # 创建筛选器实例并直接执行筛选
        screener = StockScreener()
        results = screener.screen_rescue_stocks(target_date)
        summary = screener.get_screening_summary()
        
        logger.info(f"筛选完成，共找到 {len(results)} 只符合条件的股票")
        
        return jsonify({
            'success': True,
            'status': 'completed',
            'message': f'筛选完成，找到 {len(results)} 只符合条件的股票',
            'results': results,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"筛选过程发生错误: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'筛选失败: {str(e)}'
        }), 500

@app.route('/progress')
def get_progress():
    """获取筛选进度 - Vercel环境下始终返回完成状态"""
    return jsonify({
        'status': 'idle',
        'progress': 0,
        'message': '请点击开始筛选'
    })

@app.route('/results')
def get_results():
    """获取筛选结果 - 在Vercel环境下，结果通过/screen接口直接返回"""
    return jsonify({
        'success': False,
        'message': '请重新执行筛选获取结果'
    })

@app.route('/export/excel', methods=['POST'])
def export_excel():
    """导出Excel - 内存处理"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        
        if not results:
            return jsonify({
                'success': False,
                'message': '没有可导出的结果'
            }), 400
        
        # 创建内存中的Excel文件
        from io import BytesIO
        import pandas as pd
        
        output = BytesIO()
        
        # 转换结果为DataFrame
        df = pd.DataFrame(results)
        
        # 写入Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='筛选结果')
        
        output.seek(0)
        
        filename = f"自救股票筛选结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    """导出CSV - 内存处理"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        
        if not results:
            return jsonify({
                'success': False,
                'message': '没有可导出的结果'
            }), 400
        
        # 创建内存中的CSV文件
        from io import StringIO
        import pandas as pd
        
        output = StringIO()
        
        # 转换结果为DataFrame并写入CSV
        df = pd.DataFrame(results)
        df.to_csv(output, index=False, encoding='utf-8-sig')
        
        # 转换为BytesIO
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        
        filename = f"自救股票筛选结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"导出CSV失败: {e}")
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
        'environment': 'vercel'
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

# Vercel需要的应用实例
if __name__ == '__main__':
    app.run(debug=True)