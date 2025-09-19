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

# 全局筛选器实例，保持会话状态
global_screener = None

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
            
            # 使用全局筛选器实例保持API统计
            global global_screener
            if global_screener is None or batch_start == 0:
                logger.info("正在创建股票筛选器...")
                global_screener = StockScreener()
            else:
                logger.info("使用现有筛选器实例...")
            
            screener = global_screener
            
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
                'api_calls_made': batch_results.get('api_calls_made', 0),
                'api_success_rate': batch_results.get('api_success_rate', 0),
                'verification_info': batch_results.get('verification_info', {}),
                'message': f'✅ 已处理 {batch_results["processed_count"]}/{batch_results["total_stocks"]} 只股票，找到 {len(batch_results["results"])} 只符合条件的股票 | 📡 API调用: {batch_results.get("api_calls_made", 0)}次 (成功率: {batch_results.get("api_success_rate", 0):.1f}%)'
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
        'environment': 'vercel'
    })

@app.route('/verify-data')
def verify_data():
    """验证真实数据获取 - 显示前10只股票的真实数据"""
    try:
        from stock_screener import StockScreener
        from data_fetcher import StockDataFetcher
        
        logger.info("开始验证真实数据获取...")
        
        data_fetcher = StockDataFetcher()
        
        # 获取前10只股票的真实数据
        all_stocks = data_fetcher.get_all_stocks()
        if all_stocks is None or len(all_stocks) == 0:
            return jsonify({
                'success': False,
                'message': '无法获取股票数据'
            }), 500
        
        # 取前10只股票
        sample_stocks = all_stocks.head(10)
        
        verification_data = []
        api_calls_count = 0
        
        for index, stock in sample_stocks.iterrows():
            stock_code = stock['代码']
            stock_name = stock['名称']
            
            # 获取历史数据验证
            try:
                hist_data = data_fetcher.get_stock_history(stock_code, days=3)
                api_calls_count += 1
                
                verification_item = {
                    'code': stock_code,
                    'name': stock_name,
                    'current_price': float(stock.get('最新价', 0)),
                    'change_pct': float(stock.get('涨跌幅', 0)),
                    'volume': int(stock.get('成交量', 0)),
                    'market_cap': float(stock.get('总市值', 0)),
                    'has_history_data': hist_data is not None,
                    'history_days': len(hist_data) if hist_data is not None else 0,
                    'data_timestamp': datetime.now().isoformat()
                }
                
                if hist_data is not None and len(hist_data) > 0:
                    latest_data = hist_data.iloc[-1]
                    verification_item['latest_close'] = float(latest_data.get('收盘', 0))
                    verification_item['latest_date'] = str(latest_data.get('日期', ''))
                
                verification_data.append(verification_item)
                
            except Exception as e:
                logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
                verification_data.append({
                    'code': stock_code,
                    'name': stock_name,
                    'error': str(e),
                    'data_timestamp': datetime.now().isoformat()
                })
        
        return jsonify({
            'success': True,
            'message': f'成功验证 {len(verification_data)} 只股票的真实数据',
            'total_stocks_available': len(all_stocks),
            'api_calls_made': api_calls_count,
            'verification_samples': verification_data,
            'data_source': 'akshare',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"数据验证失败: {e}")
        return jsonify({
            'success': False,
            'message': f'数据验证失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api-stats')
def get_api_statistics():
    """获取API调用统计信息"""
    try:
        global global_screener
        if global_screener is None:
            return jsonify({
                'success': False,
                'message': '筛选器未初始化，请先开始筛选',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        detailed_stats = global_screener.get_detailed_statistics()
        
        return jsonify({
            'success': True,
            'message': '成功获取API统计信息',
            'statistics': detailed_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取API统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取API统计失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/data-verification-detailed')
def get_detailed_verification():
    """获取详细的数据验证信息"""
    try:
        from stock_screener import StockScreener
        from data_fetcher import StockDataFetcher
        
        logger.info("🔍 开始详细数据验证...")
        
        data_fetcher = StockDataFetcher()
        
        # 获取所有股票数据并记录API调用
        logger.info("📡 正在获取股票列表...")
        all_stocks = data_fetcher.get_all_stocks()
        
        if all_stocks is None or len(all_stocks) == 0:
            return jsonify({
                'success': False,
                'message': '无法获取股票数据'
            }), 500
        
        # 测试3只股票的历史数据
        sample_stocks = all_stocks.head(3)
        verification_samples = []
        
        for index, stock in sample_stocks.iterrows():
            stock_code = stock['代码']
            stock_name = stock['名称']
            
            logger.info(f"📊 测试股票: {stock_name}({stock_code})")
            
            # 获取历史数据
            hist_data = data_fetcher.get_stock_history(stock_code, days=5)
            
            sample_info = {
                'code': stock_code,
                'name': stock_name,
                'current_price': float(stock.get('最新价', 0)),
                'change_pct': float(stock.get('涨跌幅', 0)),
                'has_history': hist_data is not None,
                'history_length': len(hist_data) if hist_data is not None else 0
            }
            
            if hist_data is not None and len(hist_data) > 0:
                latest = hist_data.iloc[-1]
                sample_info['latest_close'] = float(latest.get('收盘', 0))
                sample_info['latest_date'] = str(latest.get('日期', ''))
            
            verification_samples.append(sample_info)
        
        # 获取完整的API统计
        api_stats = data_fetcher.get_api_statistics()
        
        return jsonify({
            'success': True,
            'message': f'✅ 数据验证完成，确认使用真实API数据',
            'verification_result': {
                'data_source': 'akshare',
                'total_stocks_available': len(all_stocks),
                'sample_stocks_tested': len(verification_samples),
                'api_calls_made': api_stats['total_calls'],
                'api_success_rate': api_stats['success_rate'],
                'data_confirmed_real': api_stats['data_source_verified'],
                'verification_samples': verification_samples,
                'api_statistics': api_stats
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"详细数据验证失败: {e}")
        return jsonify({
            'success': False,
            'message': f'数据验证失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

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