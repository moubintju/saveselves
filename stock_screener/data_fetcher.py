import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.market_data = None
        self.api_calls_count = 0
        self.api_calls_log = []
        self.data_source_verified = False
        self.last_api_call_time = None
        
    def get_all_stocks(self):
        """获取所有A股股票列表"""
        try:
            logger.info("正在获取A股股票列表...")
            self._log_api_call("get_all_stocks", "获取A股股票列表")
            
            # 获取A股实时行情数据
            stock_data = ak.stock_zh_a_spot_em()
            
            # 筛选主板股票（排除创业板、科创板）
            # 主板股票代码：以000、001、002、600、601、603、605开头
            main_board_codes = stock_data[
                stock_data['代码'].str.startswith(('000', '001', '002', '600', '601', '603', '605'))
            ].copy()
            
            # 排除ST股票
            non_st_stocks = main_board_codes[
                ~main_board_codes['名称'].str.contains('ST|退', na=False)
            ].copy()
            
            logger.info(f"获取到 {len(non_st_stocks)} 只主板非ST股票")
            self.market_data = non_st_stocks
            self.data_source_verified = True
            self._log_api_success("get_all_stocks", f"成功获取{len(non_st_stocks)}只股票")
            return non_st_stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            self._log_api_error("get_all_stocks", str(e))
            return None
    
    def get_stock_history(self, symbol, days=5):
        """获取股票历史数据"""
        try:
            # 在每次API调用前增加延迟
            time.sleep(0.05)  # 50ms延迟
            
            self._log_api_call("get_stock_history", f"获取股票{symbol}历史数据({days}天)")
            
            # 获取历史数据，period可选："daily", "weekly", "monthly"
            # adjust可选："", "qfq", "hfq" 分别表示不复权、前复权、后复权
            hist_data = ak.stock_zh_a_hist(
                symbol=symbol, 
                period="daily", 
                start_date=(datetime.now() - timedelta(days=10)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if hist_data is not None and len(hist_data) >= days:
                # 按日期排序，确保最新数据在最后
                hist_data = hist_data.sort_values('日期')
                self._log_api_success("get_stock_history", f"成功获取股票{symbol}历史数据({len(hist_data)}天)")
                return hist_data.tail(days)
            else:
                self._log_api_warning("get_stock_history", f"股票{symbol}历史数据不足({len(hist_data) if hist_data is not None else 0}天)")
                return None
            
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 历史数据失败: {e}")
            self._log_api_error("get_stock_history", f"股票{symbol}: {str(e)}")
            return None
    
    def is_limit_up(self, open_price, close_price, stock_code):
        """判断是否涨停"""
        if pd.isna(open_price) or pd.isna(close_price) or open_price <= 0:
            return False
            
        # 计算涨幅
        pct_change = (close_price - open_price) / open_price * 100
        
        # 主板涨停限制为10%，创业板和科创板为20%
        if stock_code.startswith(('300', '688')):
            limit_threshold = 19.5  # 略小于20%，避免浮点精度问题
        else:
            limit_threshold = 9.5   # 略小于10%
            
        return pct_change >= limit_threshold
    
    def is_limit_down(self, open_price, close_price, stock_code):
        """判断是否跌停"""
        if pd.isna(open_price) or pd.isna(close_price) or open_price <= 0:
            return False
            
        # 计算跌幅
        pct_change = (close_price - open_price) / open_price * 100
        
        # 主板跌停限制为-10%，创业板和科创板为-20%
        if stock_code.startswith(('300', '688')):
            limit_threshold = -19.5
        else:
            limit_threshold = -9.5
            
        return pct_change <= limit_threshold
    
    def is_small_positive_line(self, open_price, close_price, high_price, low_price):
        """判断是否为小阳线"""
        if any(pd.isna([open_price, close_price, high_price, low_price])):
            return False
            
        # 收盘价高于开盘价（阳线）
        if close_price <= open_price:
            return False
            
        # 涨幅控制在1%-6%之间（小阳线）
        pct_change = (close_price - open_price) / open_price * 100
        if not (1.0 <= pct_change <= 6.0):
            return False
            
        # 上下影线不能过长（实体部分占比较大）
        body_size = close_price - open_price
        total_range = high_price - low_price
        
        if total_range <= 0:
            return False
            
        body_ratio = body_size / total_range
        return body_ratio >= 0.5  # 实体至少占50%
    
    def check_first_limit_up_in_3_days(self, hist_data, stock_code):
        """检查是否为近3日内首次涨停（首板）"""
        if hist_data is None or len(hist_data) < 3:
            return False
            
        hist_data = hist_data.tail(3).copy()  # 取最近3天
        
        for i, row in hist_data.iterrows():
            open_p = row.get('开盘', 0)
            close_p = row.get('收盘', 0)
            
            if self.is_limit_up(open_p, close_p, stock_code):
                # 如果是最新的一天涨停，检查前面2天是否没有涨停
                if i == hist_data.index[-1]:  # 最新交易日
                    # 检查前两天
                    prev_days = hist_data[hist_data.index < i]
                    for _, prev_row in prev_days.iterrows():
                        prev_open = prev_row.get('开盘', 0)
                        prev_close = prev_row.get('收盘', 0)
                        if self.is_limit_up(prev_open, prev_close, stock_code):
                            return False  # 前面有涨停，不是首板
                    return True  # 前面没有涨停，是首板
                else:
                    return False  # 不是最新交易日的涨停
        
        return False  # 最近3天都没有涨停
    
    def get_stock_basic_info(self, symbol):
        """获取股票基本信息"""
        try:
            # 从已获取的市场数据中查找
            if self.market_data is not None:
                stock_info = self.market_data[self.market_data['代码'] == symbol]
                if not stock_info.empty:
                    return stock_info.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 基本信息失败: {e}")
            return None
    
    def _log_api_call(self, api_name, description):
        """记录API调用"""
        self.api_calls_count += 1
        self.last_api_call_time = datetime.now()
        
        call_info = {
            'call_id': self.api_calls_count,
            'api_name': api_name,
            'description': description,
            'timestamp': self.last_api_call_time.isoformat(),
            'status': 'calling'
        }
        
        self.api_calls_log.append(call_info)
        logger.info(f"📡 API调用 #{self.api_calls_count}: {api_name} - {description}")
    
    def _log_api_success(self, api_name, result_info):
        """记录API调用成功"""
        if self.api_calls_log:
            self.api_calls_log[-1]['status'] = 'success'
            self.api_calls_log[-1]['result'] = result_info
            self.api_calls_log[-1]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"✅ API调用成功: {api_name} - {result_info}")
    
    def _log_api_error(self, api_name, error_info):
        """记录API调用失败"""
        if self.api_calls_log:
            self.api_calls_log[-1]['status'] = 'error'
            self.api_calls_log[-1]['error'] = error_info
            self.api_calls_log[-1]['completed_at'] = datetime.now().isoformat()
        
        logger.error(f"❌ API调用失败: {api_name} - {error_info}")
    
    def _log_api_warning(self, api_name, warning_info):
        """记录API调用警告"""
        if self.api_calls_log:
            self.api_calls_log[-1]['status'] = 'warning'
            self.api_calls_log[-1]['warning'] = warning_info
            self.api_calls_log[-1]['completed_at'] = datetime.now().isoformat()
        
        logger.warning(f"⚠️ API调用警告: {api_name} - {warning_info}")
    
    def get_api_statistics(self):
        """获取API调用统计信息"""
        if not self.api_calls_log:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'warning_calls': 0,
                'data_source_verified': self.data_source_verified,
                'last_call_time': None
            }
        
        successful = len([call for call in self.api_calls_log if call.get('status') == 'success'])
        failed = len([call for call in self.api_calls_log if call.get('status') == 'error'])
        warnings = len([call for call in self.api_calls_log if call.get('status') == 'warning'])
        
        return {
            'total_calls': self.api_calls_count,
            'successful_calls': successful,
            'failed_calls': failed,
            'warning_calls': warnings,
            'success_rate': (successful / self.api_calls_count * 100) if self.api_calls_count > 0 else 0,
            'data_source_verified': self.data_source_verified,
            'last_call_time': self.last_api_call_time.isoformat() if self.last_api_call_time else None,
            'api_calls_log': self.api_calls_log[-10:]  # 只返回最近10次调用
        }