import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from data_fetcher import StockDataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockScreener:
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.screening_results = []
        self.processed_stocks_count = 0
        self.screening_start_time = None
        self.screening_end_time = None
        
    def screen_rescue_stocks(self, target_date=None, progress_callback=None, max_stocks=100):
        """筛选可以自救的股票"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"开始筛选 {target_date} 的自救股票...")
        
        # 获取所有股票
        all_stocks = self.data_fetcher.get_all_stocks()
        if all_stocks is None or len(all_stocks) == 0:
            logger.error("无法获取股票数据")
            return []
            
        total_stocks = min(len(all_stocks), max_stocks)
        logger.info(f"共需要筛选 {total_stocks} 只股票 (限制为前{max_stocks}只)")
        
        rescue_stocks = []
        processed_count = 0
        
        # 限制处理的股票数量以避免超时
        limited_stocks = all_stocks.head(max_stocks)
        
        for index, stock in limited_stocks.iterrows():
            processed_count += 1
            stock_code = stock['代码']
            stock_name = stock['名称']
            
            # 报告进度
            if progress_callback:
                progress = int((processed_count / total_stocks) * 100)
                progress_callback(progress, f"正在分析: {stock_name}({stock_code})")
            
            # 执行筛选逻辑
            if self.check_rescue_criteria(stock, stock_code):
                rescue_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'current_price': stock.get('最新价', 0),
                    'change_pct': stock.get('涨跌幅', 0),
                    'volume': stock.get('成交量', 0),
                    'turnover': stock.get('成交额', 0),
                    'market_cap': stock.get('总市值', 0)
                })
            
            # 每处理5只股票增加小延迟，降低请求频率
            if processed_count % 5 == 0:
                time.sleep(0.1)  # 100ms延迟
                
            # 每处理10只股票记录一次进度
            if processed_count % 10 == 0:
                logger.info(f"已处理 {processed_count}/{total_stocks} 只股票，找到 {len(rescue_stocks)} 只符合条件的股票")
        
        logger.info(f"筛选完成！共找到 {len(rescue_stocks)} 只符合自救条件的股票")
        self.screening_results = rescue_stocks
        return rescue_stocks
    
    def screen_rescue_stocks_batch(self, target_date=None, batch_start=0, batch_size=20):
        """分批筛选可以自救的股票"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        # 记录筛选开始时间
        if batch_start == 0:
            self.screening_start_time = datetime.now()
            
        logger.info(f"🚀 开始分批筛选 {target_date} 的自救股票，批次 {batch_start}-{batch_start + batch_size}...")
        logger.info(f"📊 当前API统计: {self.data_fetcher.get_api_statistics()}")
        
        # 获取所有股票
        all_stocks = self.data_fetcher.get_all_stocks()
        if all_stocks is None or len(all_stocks) == 0:
            logger.error("无法获取股票数据")
            return {
                'results': [],
                'total_stocks': 0,
                'processed_count': 0,
                'has_more': False
            }
            
        total_stocks = len(all_stocks)
        logger.info(f"总共有 {total_stocks} 只股票需要筛选")
        
        # 获取当前批次的股票
        batch_end = min(batch_start + batch_size, total_stocks)
        batch_stocks = all_stocks.iloc[batch_start:batch_end]
        
        logger.info(f"当前批次处理 {len(batch_stocks)} 只股票 ({batch_start}-{batch_end})")
        
        rescue_stocks = []
        processed_count = batch_start
        
        for index, stock in batch_stocks.iterrows():
            processed_count += 1
            stock_code = stock['代码']
            stock_name = stock['名称']
            
            logger.info(f"正在分析: {stock_name}({stock_code}) - {processed_count}/{total_stocks}")
            
            # 执行筛选逻辑
            self.processed_stocks_count += 1
            if self.check_rescue_criteria(stock, stock_code):
                rescue_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'current_price': stock.get('最新价', 0),
                    'change_pct': stock.get('涨跌幅', 0),
                    'volume': stock.get('成交量', 0),
                    'turnover': stock.get('成交额', 0),
                    'market_cap': stock.get('总市值', 0)
                })
            
            # 每处理2只股票增加延迟，降低请求频率
            if (processed_count - batch_start) % 2 == 0:
                time.sleep(0.2)  # 200ms延迟
        
        has_more = batch_end < total_stocks
        
        # 记录筛选结束时间
        if not has_more:
            self.screening_end_time = datetime.now()
        
        # 获取API统计信息
        api_stats = self.data_fetcher.get_api_statistics()
        
        logger.info(f"✅ 批次筛选完成！本批次找到 {len(rescue_stocks)} 只符合自救条件的股票")
        logger.info(f"📊 API调用统计: 总计{api_stats['total_calls']}次，成功{api_stats['successful_calls']}次，失败{api_stats['failed_calls']}次")
        
        return {
            'results': rescue_stocks,
            'total_stocks': total_stocks,
            'processed_count': processed_count,
            'has_more': has_more,
            'api_calls_made': api_stats['total_calls'],
            'api_success_rate': api_stats['success_rate'],
            'verification_info': {
                'data_source': 'akshare',
                'real_data_confirmed': api_stats['data_source_verified'],
                'processing_timestamp': datetime.now().isoformat(),
                'api_statistics': api_stats
            }
        }
    
    def check_rescue_criteria(self, stock_data, stock_code):
        """检查股票是否符合自救标准"""
        try:
            # 获取历史数据（API调用统计已在data_fetcher中处理）
            hist_data = self.data_fetcher.get_stock_history(stock_code, days=5)
            if hist_data is None or len(hist_data) < 2:
                return False
                
            # 最新交易日数据
            today_data = hist_data.iloc[-1]
            yesterday_data = hist_data.iloc[-2] if len(hist_data) > 1 else None
            
            # 提取价格数据
            today_open = today_data.get('开盘', 0)
            today_close = today_data.get('收盘', 0)
            today_high = today_data.get('最高', 0)
            today_low = today_data.get('最低', 0)
            today_volume = today_data.get('成交量', 0)
            
            if yesterday_data is not None:
                yesterday_open = yesterday_data.get('开盘', 0)
                yesterday_close = yesterday_data.get('收盘', 0)
                yesterday_volume = yesterday_data.get('成交量', 0)
            else:
                return False
            
            # 条件1: 当天非涨停
            if self.data_fetcher.is_limit_up(today_open, today_close, stock_code):
                return False
                
            # 条件2: 当天为小阳线
            if not self.data_fetcher.is_small_positive_line(today_open, today_close, today_high, today_low):
                return False
                
            # 条件3: 当天成交量小于昨日成交量
            if today_volume >= yesterday_volume:
                return False
                
            # 条件4: 昨日非跌停，昨日非涨停
            if (self.data_fetcher.is_limit_up(yesterday_open, yesterday_close, stock_code) or 
                self.data_fetcher.is_limit_down(yesterday_open, yesterday_close, stock_code)):
                return False
                
            # 条件5: 近3日内首次涨停（首板）- 需要更多历史数据
            extended_hist = self.data_fetcher.get_stock_history(stock_code, days=10)
            if not self.data_fetcher.check_first_limit_up_in_3_days(extended_hist, stock_code):
                return False
                
            # 条件6: 主板股票 - 已在data_fetcher中过滤
            # 条件7: 非ST股票 - 已在data_fetcher中过滤
            
            return True
            
        except Exception as e:
            logger.warning(f"检查股票 {stock_code} 失败: {e}")
            return False
    
    def get_screening_summary(self):
        """获取筛选结果摘要"""
        if not self.screening_results:
            return {
                'total_count': 0,
                'avg_change_pct': 0,
                'avg_volume': 0,
                'total_market_cap': 0
            }
            
        results_df = pd.DataFrame(self.screening_results)
        
        return {
            'total_count': len(self.screening_results),
            'avg_change_pct': results_df['change_pct'].mean(),
            'avg_volume': results_df['volume'].mean(),
            'total_market_cap': results_df['market_cap'].sum(),
            'max_change_pct': results_df['change_pct'].max(),
            'min_change_pct': results_df['change_pct'].min()
        }
    
    def get_detailed_statistics(self):
        """获取详细的统计信息"""
        api_stats = self.data_fetcher.get_api_statistics()
        
        # 计算处理时间
        processing_time = None
        if self.screening_start_time and self.screening_end_time:
            processing_time = (self.screening_end_time - self.screening_start_time).total_seconds()
        
        return {
            'screening_statistics': {
                'total_processed': self.processed_stocks_count,
                'results_found': len(self.screening_results),
                'success_rate': (len(self.screening_results) / self.processed_stocks_count * 100) if self.processed_stocks_count > 0 else 0,
                'processing_time_seconds': processing_time,
                'start_time': self.screening_start_time.isoformat() if self.screening_start_time else None,
                'end_time': self.screening_end_time.isoformat() if self.screening_end_time else None
            },
            'api_statistics': api_stats,
            'data_verification': {
                'data_source': 'akshare',
                'real_data_confirmed': api_stats['data_source_verified'],
                'api_calls_per_stock': api_stats['total_calls'] / self.processed_stocks_count if self.processed_stocks_count > 0 else 0
            }
        }
    
    def export_results_to_excel(self, filename=None):
        """导出结果到Excel文件"""
        if not self.screening_results:
            logger.warning("没有筛选结果可导出")
            return None
            
        if filename is None:
            filename = f"rescue_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        try:
            df = pd.DataFrame(self.screening_results)
            
            # 添加中文列名
            df.columns = ['股票代码', '股票名称', '最新价', '涨跌幅(%)', '成交量', '成交额', '总市值']
            
            # 格式化数据
            df['涨跌幅(%)'] = df['涨跌幅(%)'].round(2)
            df['最新价'] = df['最新价'].round(2)
            
            # 保存到results目录
            filepath = f"results/{filename}"
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            logger.info(f"结果已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return None
    
    def export_results_to_csv(self, filename=None):
        """导出结果到CSV文件"""
        if not self.screening_results:
            logger.warning("没有筛选结果可导出")
            return None
            
        if filename is None:
            filename = f"rescue_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        try:
            df = pd.DataFrame(self.screening_results)
            
            # 添加中文列名
            df.columns = ['股票代码', '股票名称', '最新价', '涨跌幅(%)', '成交量', '成交额', '总市值']
            
            # 格式化数据
            df['涨跌幅(%)'] = df['涨跌幅(%)'].round(2)
            df['最新价'] = df['最新价'].round(2)
            
            # 保存到results目录
            filepath = f"results/{filename}"
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            logger.info(f"结果已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return None