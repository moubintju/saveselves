// 全局变量
let screeningInProgress = false;
let screeningInterval = null;

// DOM元素
const startBtn = document.getElementById('start-screening');
const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const errorText = document.getElementById('error-text');
const summaryInfo = document.getElementById('summary-info');
const apiStatsInfo = document.getElementById('api-stats-info');
const resultsTableBody = document.querySelector('#results-table tbody');
const exportExcelBtn = document.getElementById('export-excel');
const exportCsvBtn = document.getElementById('export-csv');

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('screening-date').value = today;
    
    // 绑定事件
    startBtn.addEventListener('click', startScreening);
    exportExcelBtn.addEventListener('click', () => exportResults('excel'));
    exportCsvBtn.addEventListener('click', () => exportResults('csv'));
    
    // 隐藏所有结果区域
    hideAllSections();
});

// 隐藏所有结果区域
function hideAllSections() {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

// 显示错误信息
function showError(message) {
    hideAllSections();
    errorText.textContent = message;
    errorSection.style.display = 'block';
    resetUI();
}

// 重置UI状态
function resetUI() {
    screeningInProgress = false;
    startBtn.textContent = '开始筛选';
    startBtn.disabled = false;
    
    if (screeningInterval) {
        clearInterval(screeningInterval);
        screeningInterval = null;
    }
}

// 处理分批结果
async function handleBatchResult(result) {
    // 更新全局状态
    totalStocks = result.total_stocks;
    currentBatch++;
    
    // 累积结果
    allResultsData = allResultsData.concat(result.results);
    
    // 更新进度
    const progress = Math.floor((result.processed_count / result.total_stocks) * 100);
    updateProgress(progress, result.message);
    
    // 实时显示当前累积的结果
    displayBatchResults(allResultsData, {
        total_count: allResultsData.length,
        processed_stocks: result.processed_count,
        total_stocks: result.total_stocks
    }, result);
    
    // 显示结果区域
    hideAllSections();
    resultsSection.style.display = 'block';
    
    // 如果还有更多批次，继续处理
    if (result.has_more) {
        // 延迟一下再继续下一批，避免请求过于频繁
        setTimeout(() => {
            continueNextBatch(document.getElementById('screening-date').value);
        }, 2000);
    } else {
        // 所有批次完成
        updateProgress(100, `筛选完成！共查询 ${result.processed_count} 只股票，找到 ${allResultsData.length} 只符合条件的股票`);
        resetUI();
        
        // 计算最终摘要
        const finalSummary = calculateFinalSummary(allResultsData);
        displayBatchResults(allResultsData, finalSummary, result);
    }
}

// 继续下一批处理
async function continueNextBatch(screeningDate) {
    try {
        const response = await fetch('/screen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: screeningDate,
                batch_start: currentBatch * 20,
                batch_size: 20
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.status === 'batch_completed') {
            handleBatchResult(result);
        } else {
            showError(result.message || '批次处理失败');
            resetUI();
        }
        
    } catch (error) {
        console.error('批次处理失败:', error);
        showError('批次处理失败，请重试');
        resetUI();
    }
}

// 显示分批结果
function displayBatchResults(results, summary, batchResult = null) {
    // 存储当前结果数据供导出使用
    currentResultsData = results;
    
    // 显示摘要信息
    displayBatchSummary(summary);
    
    // 显示API统计信息
    if (batchResult) {
        displayApiStats(batchResult);
    }
    
    // 清空表格
    resultsTableBody.innerHTML = '';
    
    if (results && results.length > 0) {
        // 填充表格数据
        results.forEach(stock => {
            const row = createResultRow(stock);
            resultsTableBody.appendChild(row);
        });
    } else {
        // 无结果时显示提示
        const noDataRow = document.createElement('tr');
        noDataRow.innerHTML = `
            <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                暂未找到符合条件的股票，继续筛选中...
            </td>
        `;
        resultsTableBody.appendChild(noDataRow);
    }
}

// 显示分批摘要信息
function displayBatchSummary(summary) {
    const processedStocks = summary.processed_stocks || 0;
    const totalStocks = summary.total_stocks || 0;
    const foundCount = summary.total_count || 0;
    
    summaryInfo.innerHTML = `
        <div class="summary-item">
            <span class="value">${foundCount}</span>
            <span class="label">符合条件股票</span>
        </div>
        <div class="summary-item">
            <span class="value">${processedStocks}</span>
            <span class="label">已查询股票</span>
        </div>
        <div class="summary-item">
            <span class="value">${totalStocks}</span>
            <span class="label">总股票数量</span>
        </div>
        <div class="summary-item">
            <span class="value">${totalStocks > 0 ? ((processedStocks / totalStocks) * 100).toFixed(1) : 0}%</span>
            <span class="label">查询进度</span>
        </div>
    `;
}

// 显示API统计信息
function displayApiStats(result) {
    const apiCalls = result.api_calls_made || 0;
    const apiSuccessRate = isNaN(result.api_success_rate) ? 0 : (result.api_success_rate || 0);
    const isRealData = result.verification_info?.real_data_confirmed || false;
    
    if (apiCalls > 0) {
        apiStatsInfo.style.display = 'block';
        apiStatsInfo.innerHTML = `
            <h4>📊 API调用统计</h4>
            <div class="api-stats-grid">
                <div class="api-stat-item">
                    <span class="api-value">📡 ${apiCalls}</span>
                    <span class="api-label">API调用次数</span>
                </div>
                <div class="api-stat-item">
                    <span class="api-value">✅ ${apiSuccessRate.toFixed(1)}%</span>
                    <span class="api-label">调用成功率</span>
                </div>
                <div class="api-stat-item">
                    <span class="api-value">${isRealData ? '🔗 真实数据' : '❌ 测试数据'}</span>
                    <span class="api-label">数据来源确认</span>
                </div>
                <div class="api-stat-item">
                    <span class="api-value">🏭 AkShare</span>
                    <span class="api-label">数据提供商</span>
                </div>
            </div>
        `;
    } else {
        apiStatsInfo.style.display = 'none';
    }
}

// 计算最终摘要
function calculateFinalSummary(results) {
    if (!results || results.length === 0) {
        return {
            total_count: 0,
            avg_change_pct: 0,
            avg_volume: 0,
            total_market_cap: 0
        };
    }
    
    const totalCount = results.length;
    const avgChangePct = results.reduce((sum, stock) => sum + (stock.change_pct || 0), 0) / totalCount;
    const avgVolume = results.reduce((sum, stock) => sum + (stock.volume || 0), 0) / totalCount;
    const totalMarketCap = results.reduce((sum, stock) => sum + (stock.market_cap || 0), 0);
    
    return {
        total_count: totalCount,
        avg_change_pct: avgChangePct,
        avg_volume: avgVolume,
        total_market_cap: totalMarketCap,
        processed_stocks: totalStocks,
        total_stocks: totalStocks
    };
}

// 开始筛选
async function startScreening() {
    if (screeningInProgress) {
        return;
    }
    
    const screeningDate = document.getElementById('screening-date').value;
    
    if (!screeningDate) {
        showError('请选择筛选日期');
        return;
    }
    
    // 重置分批变量
    allResultsData = [];
    currentBatch = 0;
    totalStocks = 0;
    
    // 更新UI状态
    screeningInProgress = true;
    startBtn.textContent = '筛选中...';
    startBtn.disabled = true;
    
    // 隐藏其他区域，显示进度条
    hideAllSections();
    progressSection.style.display = 'block';
    updateProgress(0, '正在初始化...');
    
    try {
        // 发送筛选请求
        const response = await fetch('/screen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: screeningDate,
                batch_start: currentBatch * 20,
                batch_size: 20
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (result.status === 'batch_completed') {
                // 处理分批结果
                handleBatchResult(result);
            } else if (result.status === 'completed') {
                // 兼容旧版本完整结果
                updateProgress(100, result.message);
                displayResults(result.results, result.summary);
                hideAllSections();
                resultsSection.style.display = 'block';
                resetUI();
            } else {
                showError(result.message || '筛选处理失败');
            }
        } else {
            showError(result.message || '筛选启动失败');
        }
        
    } catch (error) {
        console.error('筛选请求失败:', error);
        showError('网络请求失败，请检查服务器状态');
    }
}

// 轮询筛选进度
function pollProgress() {
    screeningInterval = setInterval(async () => {
        try {
            const response = await fetch('/progress');
            const data = await response.json();
            
            if (data.status === 'running') {
                updateProgress(data.progress, data.message);
            } else if (data.status === 'completed') {
                // 筛选完成，获取结果
                clearInterval(screeningInterval);
                screeningInterval = null;
                await loadResults();
            } else if (data.status === 'error') {
                clearInterval(screeningInterval);
                screeningInterval = null;
                showError(data.message || '筛选过程中发生错误');
            }
            
        } catch (error) {
            console.error('获取进度失败:', error);
        }
    }, 1000); // 每秒检查一次
}

// 更新进度条
function updateProgress(percentage, message) {
    progressFill.style.width = percentage + '%';
    progressText.textContent = message;
}

// 加载筛选结果
async function loadResults() {
    try {
        const response = await fetch('/results');
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.results, data.summary);
            hideAllSections();
            resultsSection.style.display = 'block';
        } else {
            showError(data.message || '获取结果失败');
        }
        
    } catch (error) {
        console.error('加载结果失败:', error);
        showError('获取结果失败');
    } finally {
        resetUI();
    }
}

// 存储当前结果数据
let currentResultsData = [];
let allResultsData = [];  // 存储所有批次的结果
let currentBatch = 0;
let totalStocks = 0;

// 显示筛选结果
function displayResults(results, summary) {
    // 存储当前结果数据供导出使用
    currentResultsData = results || [];
    
    // 显示摘要信息
    displaySummary(summary);
    
    // 清空表格
    resultsTableBody.innerHTML = '';
    
    if (results && results.length > 0) {
        // 填充表格数据
        results.forEach(stock => {
            const row = createResultRow(stock);
            resultsTableBody.appendChild(row);
        });
    } else {
        // 无结果时显示提示
        const noDataRow = document.createElement('tr');
        noDataRow.innerHTML = `
            <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                未找到符合条件的股票
            </td>
        `;
        resultsTableBody.appendChild(noDataRow);
    }
}

// 获取当前结果数据
function getCurrentResults() {
    return currentResultsData;
}

// 显示摘要信息
function displaySummary(summary) {
    summaryInfo.innerHTML = `
        <div class="summary-item">
            <span class="value">${summary.total_count || 0}</span>
            <span class="label">符合条件股票</span>
        </div>
        <div class="summary-item">
            <span class="value">${(summary.avg_change_pct || 0).toFixed(2)}%</span>
            <span class="label">平均涨跌幅</span>
        </div>
        <div class="summary-item">
            <span class="value">${formatNumber(summary.avg_volume || 0)}</span>
            <span class="label">平均成交量</span>
        </div>
        <div class="summary-item">
            <span class="value">${formatNumber(summary.total_market_cap || 0)}</span>
            <span class="label">总市值(亿)</span>
        </div>
    `;
}

// 创建结果行
function createResultRow(stock) {
    const row = document.createElement('tr');
    
    // 格式化涨跌幅颜色
    const changePctClass = stock.change_pct > 0 ? 'positive' : (stock.change_pct < 0 ? 'negative' : '');
    
    row.innerHTML = `
        <td>${stock.code}</td>
        <td>${stock.name}</td>
        <td>¥${stock.current_price.toFixed(2)}</td>
        <td class="${changePctClass}">${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%</td>
        <td>${formatNumber(stock.volume)}</td>
        <td>${formatNumber(stock.turnover)}</td>
        <td>${formatNumber(stock.market_cap)}</td>
    `;
    
    return row;
}

// 导出结果
async function exportResults(format) {
    try {
        // 获取当前显示的结果数据
        const currentResults = getCurrentResults();
        
        const response = await fetch(`/export/${format}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                results: currentResults
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // 设置文件名
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_');
            const extension = format === 'excel' ? 'xlsx' : 'csv';
            a.download = `rescue_stocks_${timestamp}.${extension}`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // 显示成功提示
            showNotification(`${format.toUpperCase()}文件导出成功！`);
        } else {
            throw new Error('导出失败');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showNotification('导出失败，请重试', 'error');
    }
}

// 格式化数字显示
function formatNumber(num) {
    if (num == null || num === undefined) return '0';
    
    const numValue = parseFloat(num);
    if (isNaN(numValue)) return '0';
    
    if (numValue >= 1e8) {
        return (numValue / 1e8).toFixed(1) + '亿';
    } else if (numValue >= 1e4) {
        return (numValue / 1e4).toFixed(1) + '万';
    } else {
        return numValue.toLocaleString();
    }
}

// 显示通知
function showNotification(message, type = 'success') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加样式
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        backgroundColor: type === 'success' ? '#28a745' : '#dc3545',
        color: 'white',
        borderRadius: '5px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        zIndex: '9999',
        fontSize: '14px',
        maxWidth: '300px',
        opacity: '0',
        transform: 'translateY(-20px)',
        transition: 'all 0.3s ease'
    });
    
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // 自动隐藏
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 防止页面刷新时正在进行的筛选丢失
window.addEventListener('beforeunload', function(e) {
    if (screeningInProgress) {
        e.preventDefault();
        e.returnValue = '筛选正在进行中，确定要离开页面吗？';
    }
});