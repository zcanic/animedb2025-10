// 全局状态
let currentState = {
    page: 1,
    pageSize: 20,
    search: '',
    yearFrom: null,
    yearTo: null,
    ratingFrom: null,
    ratingTo: null,
    sortBy: 'collections',
    sortOrder: 'desc'
};

// DOM元素
const elements = {
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    yearFrom: document.getElementById('year-from'),
    yearTo: document.getElementById('year-to'),
    ratingFrom: document.getElementById('rating-from'),
    ratingTo: document.getElementById('rating-to'),
    sortBy: document.getElementById('sort-by'),
    sortOrder: document.getElementById('sort-order'),
    resetBtn: document.getElementById('reset-filters'),
    animeGrid: document.getElementById('anime-grid'),
    loading: document.getElementById('loading'),
    errorMessage: document.getElementById('error-message'),
    errorText: document.getElementById('error-text'),
    resultsCount: document.getElementById('results-count'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageInfo: document.getElementById('page-info'),
    totalAnime: document.getElementById('total-anime'),
    avgRating: document.getElementById('avg-rating'),
    totalCollections: document.getElementById('total-collections')
};

// API基础URL
const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    // 绑定事件监听器
    bindEventListeners();

    // 加载统计数据
    await loadStats();

    // 加载初始数据
    await loadAnimeData();
}

function bindEventListeners() {
    // 搜索功能
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // 筛选器变化
    [elements.yearFrom, elements.yearTo, elements.ratingFrom, elements.ratingTo,
     elements.sortBy, elements.sortOrder].forEach(element => {
        element.addEventListener('change', handleFilterChange);
    });

    // 重置按钮
    elements.resetBtn.addEventListener('click', resetFilters);

    // 分页按钮
    elements.prevPage.addEventListener('click', () => changePage(-1));
    elements.nextPage.addEventListener('click', () => changePage(1));
}

function handleSearch() {
    currentState.search = elements.searchInput.value.trim();
    currentState.page = 1;
    loadAnimeData();
}

function handleFilterChange() {
    currentState.yearFrom = elements.yearFrom.value ? parseInt(elements.yearFrom.value) : null;
    currentState.yearTo = elements.yearTo.value ? parseInt(elements.yearTo.value) : null;
    currentState.ratingFrom = elements.ratingFrom.value ? parseFloat(elements.ratingFrom.value) : null;
    currentState.ratingTo = elements.ratingTo.value ? parseFloat(elements.ratingTo.value) : null;
    currentState.sortBy = elements.sortBy.value;
    currentState.sortOrder = elements.sortOrder.value;
    currentState.page = 1;

    loadAnimeData();
}

function resetFilters() {
    // 重置输入框
    elements.searchInput.value = '';
    elements.yearFrom.value = '';
    elements.yearTo.value = '';
    elements.ratingFrom.value = '';
    elements.ratingTo.value = '';
    elements.sortBy.value = 'collections';
    elements.sortOrder.value = 'desc';

    // 重置状态
    currentState = {
        page: 1,
        pageSize: 20,
        search: '',
        yearFrom: null,
        yearTo: null,
        ratingFrom: null,
        ratingTo: null,
        sortBy: 'collections',
        sortOrder: 'desc'
    };

    loadAnimeData();
}

function changePage(delta) {
    currentState.page += delta;
    loadAnimeData();
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();

        elements.totalAnime.textContent = stats.total_anime.toLocaleString();
        elements.avgRating.textContent = stats.avg_rating ? stats.avg_rating.toFixed(2) : 'N/A';
        elements.totalCollections.textContent = stats.total_collections ? Math.round(stats.total_collections / 1000) + 'K' : 'N/A';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadAnimeData() {
    showLoading();
    hideError();

    try {
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentState.page.toString(),
            page_size: currentState.pageSize.toString(),
            sort_by: currentState.sortBy,
            sort_order: currentState.sortOrder
        });

        if (currentState.search) params.append('search', currentState.search);
        if (currentState.yearFrom) params.append('year_from', currentState.yearFrom.toString());
        if (currentState.yearTo) params.append('year_to', currentState.yearTo.toString());
        if (currentState.ratingFrom) params.append('rating_from', currentState.ratingFrom.toString());
        if (currentState.ratingTo) params.append('rating_to', currentState.ratingTo.toString());

        const response = await fetch(`${API_BASE}/api/anime?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        displayAnimeData(data);
        updatePagination(data);

    } catch (error) {
        showError('加载数据失败: ' + error.message);
        console.error('Error loading anime data:', error);
    } finally {
        hideLoading();
    }
}

function displayAnimeData(data) {
    const animeGrid = elements.animeGrid;

    if (data.data.length === 0) {
        animeGrid.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search" style="font-size: 3rem; color: #cbd5e0; margin-bottom: 15px;"></i>
                <h3>没有找到匹配的动漫</h3>
                <p>请尝试调整搜索条件或筛选器</p>
            </div>
        `;
        return;
    }

    animeGrid.innerHTML = data.data.map(anime => createAnimeCard(anime)).join('');

    // 更新结果计数
    elements.resultsCount.textContent = `找到 ${data.total.toLocaleString()} 部动漫`;
}

function createAnimeCard(anime) {
    const coverImage = anime.img_url && anime.img_url !== 'https://bgm.tv/img/no_icon_subject.png'
        ? anime.img_url
        : 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA2MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjYwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0zMCA0MEMyNi42ODYzIDQwIDI0IDM3LjMxMzcgMjQgMzRDMjQgMzAuNjg2MyAyNi42ODYzIDI4IDMwIDI4QzMzLjMxMzcgMjggMzYgMzAuNjg2MyAzNiAzNEMzNiAzNy4zMTM3IDMzLjMxMzcgNDAgMzAgNDBaTTM0IDUySDI2VjQ0SDM0VjUyWiIgZmlsbD0iIzlDQThBNyIvPgo8L3N2Zz4K';

    return `
        <div class="anime-card">
            <div class="anime-header">
                <img src="${coverImage}" alt="${anime.title}" class="anime-cover" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA2MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjYwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0zMCA0MEMyNi42ODYzIDQwIDI0IDM3LjMxMzcgMjQgMzRDMjQgMzAuNjg2MyAyNi42ODYzIDI4IDMwIDI4QzMzLjMxMzcgMjggMzYgMzAuNjg2MyAzNiAzNEMzNiAzNy4zMTM3IDMzLjMxMzcgNDAgMzAgNDBaTTM0IDUySDI2VjQ0SDM0VjUyWiIgZmlsbD0iIzlDQThBNyIvPgo8L3N2Zz4K'">
                <div class="anime-title">
                    <h3 title="${anime.title}">${anime.title}</h3>
                    <div class="anime-year">${anime.year}</div>
                </div>
            </div>

            <div class="anime-stats">
                <div class="stat">
                    <span class="stat-value">${anime.collections ? anime.collections.toLocaleString() : '0'}</span>
                    <span class="stat-label-small">收藏</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${anime.watched ? anime.watched.toLocaleString() : '0'}</span>
                    <span class="stat-label-small">观看</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${anime.rating_count ? anime.rating_count.toLocaleString() : '0'}</span>
                    <span class="stat-label-small">评分</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${anime.completion_rate ? (anime.completion_rate * 100).toFixed(1) + '%' : 'N/A'}</span>
                    <span class="stat-label-small">完成率</span>
                </div>
            </div>

            <div class="rating">
                ${anime.average_rating ? anime.average_rating.toFixed(1) + ' ★' : '未评分'}
            </div>
        </div>
    `;
}

function updatePagination(data) {
    // 更新页面信息
    elements.pageInfo.textContent = `第 ${data.page} 页，共 ${data.total_pages} 页`;

    // 更新分页按钮状态
    elements.prevPage.disabled = data.page <= 1;
    elements.nextPage.disabled = data.page >= data.total_pages;
}

function showLoading() {
    elements.loading.classList.remove('hidden');
    elements.animeGrid.innerHTML = '';
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

function showError(message) {
    elements.errorText.textContent = message;
    elements.errorMessage.classList.remove('hidden');
}

function hideError() {
    elements.errorMessage.classList.add('hidden');
}

// 工具函数：格式化数字
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}