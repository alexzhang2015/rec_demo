/**
 * 星巴克猜你喜欢 Demo - 前端应用
 */

// 状态管理
const state = {
    currentCategory: 'ALL',
    recommendations: [],
    menuItems: [],
    categories: [],
    customizationOptions: null,
    selectedItem: null,
    customization: {
        cup_size: 'GRANDE',
        temperature: 'ICED',
        sugar_level: 'FULL',
        milk_type: 'WHOLE',
        extra_shot: false,
        whipped_cream: false,
        syrup: null
    },
    userPreferences: {
        tags: []
    }
};

// DOM 元素
const elements = {
    recommendationGrid: document.getElementById('recommendation-grid'),
    menuGrid: document.getElementById('menu-grid'),
    categoryTabs: document.getElementById('category-tabs'),
    modalOverlay: document.getElementById('modal-overlay'),
    modalTitle: document.getElementById('modal-title'),
    totalPrice: document.getElementById('total-price'),
    preferenceTags: document.getElementById('preference-tags'),
    toast: document.getElementById('toast')
};

// API 请求
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// 初始化
async function init() {
    showLoading();

    // 并行加载数据
    const [menuData, recommendations, customOptions] = await Promise.all([
        fetchAPI('/menu'),
        fetchAPI('/recommendations?user_id=guest&limit=6'),
        fetchAPI('/customization/options')
    ]);

    if (menuData) {
        state.menuItems = menuData.items;
        state.categories = menuData.categories;
        renderCategoryTabs();
    }

    if (recommendations) {
        state.recommendations = recommendations.recommendations;
        renderRecommendations();
    }

    if (customOptions) {
        state.customizationOptions = customOptions;
        renderCustomizationOptions();
    }

    renderMenu();
    renderPreferenceTags();
}

// 渲染推荐区域
function renderRecommendations() {
    const html = state.recommendations.map(rec => createProductCard(rec.item, rec.reason)).join('');
    elements.recommendationGrid.innerHTML = html;
}

// 渲染分类标签
function renderCategoryTabs() {
    const allTab = `<button class="category-tab active" data-category="ALL">全部</button>`;
    const categoryTabs = state.categories.map(cat =>
        `<button class="category-tab" data-category="${cat.value}">${cat.label}</button>`
    ).join('');

    elements.categoryTabs.innerHTML = allTab + categoryTabs;

    // 绑定事件
    elements.categoryTabs.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelector('.category-tab.active')?.classList.remove('active');
            tab.classList.add('active');
            state.currentCategory = tab.dataset.category;
            renderMenu();
        });
    });
}

// 渲染菜单
function renderMenu() {
    let items = state.menuItems;

    if (state.currentCategory !== 'ALL') {
        items = items.filter(item => item.category === state.categories.find(c => c.value === state.currentCategory)?.label);
    }

    const html = items.map(item => createProductCard(item)).join('');
    elements.menuGrid.innerHTML = html;
}

// 创建产品卡片
function createProductCard(item, reason = null) {
    const badges = [];
    if (item.is_new) badges.push('<span class="badge badge-new">新品</span>');
    if (item.is_seasonal) badges.push('<span class="badge badge-seasonal">季节限定</span>');
    if (reason) badges.push(`<span class="badge badge-reason">${reason}</span>`);

    const tags = item.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('');

    // 根据分类选择图标
    const icons = {
        '咖啡': '☕',
        '茶饮': '🍵',
        '星冰乐': '🧊',
        '清爽系列': '🍹',
        '食品': '🥐'
    };
    const icon = icons[item.category] || '☕';

    return `
        <div class="product-card" onclick="openCustomization('${item.sku}')">
            <div class="product-image">
                <span class="placeholder">${icon}</span>
                ${badges.length ? `<div class="product-badge">${badges.join('')}</div>` : ''}
            </div>
            <div class="product-info">
                <h3 class="product-name">${item.name}</h3>
                <p class="product-english">${item.english_name}</p>
                <p class="product-desc">${item.description}</p>
                <div class="product-meta">
                    <span class="product-price">${item.base_price}</span>
                    <span class="product-calories">${item.calories} 卡路里</span>
                </div>
                <div class="product-tags">${tags}</div>
            </div>
        </div>
    `;
}

// 打开客制化弹窗
function openCustomization(sku) {
    const item = state.menuItems.find(i => i.sku === sku);
    if (!item) return;

    state.selectedItem = item;

    // 重置客制化选项
    state.customization = {
        cup_size: item.available_sizes[1]?.toUpperCase() || item.available_sizes[0]?.toUpperCase() || 'GRANDE',
        temperature: item.available_temperatures[0]?.toUpperCase() || 'ICED',
        sugar_level: 'FULL',
        milk_type: 'WHOLE',
        extra_shot: false,
        whipped_cream: false,
        syrup: null
    };

    elements.modalTitle.textContent = item.name;
    updateCustomizationUI();
    updatePrice();
    elements.modalOverlay.classList.add('active');
}

// 关闭弹窗
function closeModal() {
    elements.modalOverlay.classList.remove('active');
    state.selectedItem = null;
}

// 渲染客制化选项
function renderCustomizationOptions() {
    if (!state.customizationOptions) return;

    // 客制化选项将在打开弹窗时动态更新
}

// 更新客制化UI
function updateCustomizationUI() {
    const item = state.selectedItem;
    if (!item || !state.customizationOptions) return;

    const opts = state.customizationOptions;

    // 杯型
    const sizesContainer = document.getElementById('size-options');
    if (sizesContainer && item.available_sizes.length > 0) {
        sizesContainer.innerHTML = opts.cup_sizes
            .filter(s => item.available_sizes.some(as => as.toUpperCase() === s.value))
            .map(s => {
                const priceAdd = s.value === 'VENTI' ? '+¥4' : (s.value === 'TALL' ? '-¥3' : '');
                return `<button class="option-btn ${state.customization.cup_size === s.value ? 'selected' : ''}"
                    onclick="selectOption('cup_size', '${s.value}')">${s.label}${priceAdd ? `<span class="price-add">${priceAdd}</span>` : ''}</button>`;
            }).join('');
        sizesContainer.parentElement.style.display = 'block';
    } else if (sizesContainer) {
        sizesContainer.parentElement.style.display = 'none';
    }

    // 温度
    const tempContainer = document.getElementById('temp-options');
    if (tempContainer && item.available_temperatures.length > 0) {
        tempContainer.innerHTML = opts.temperatures
            .filter(t => item.available_temperatures.some(at => at.toUpperCase() === t.value))
            .map(t => `<button class="option-btn ${state.customization.temperature === t.value ? 'selected' : ''}"
                onclick="selectOption('temperature', '${t.value}')">${t.label}</button>`).join('');
        tempContainer.parentElement.style.display = 'block';
    } else if (tempContainer) {
        tempContainer.parentElement.style.display = 'none';
    }

    // 糖度
    const sugarContainer = document.getElementById('sugar-options');
    if (sugarContainer) {
        sugarContainer.innerHTML = opts.sugar_levels
            .map(s => `<button class="option-btn ${state.customization.sugar_level === s.value ? 'selected' : ''}"
                onclick="selectOption('sugar_level', '${s.value}')">${s.label}</button>`).join('');
    }

    // 奶类
    const milkContainer = document.getElementById('milk-options');
    if (milkContainer) {
        milkContainer.innerHTML = opts.milk_types
            .map(m => {
                const priceAdd = ['OAT', 'COCONUT'].includes(m.value) ? '+¥3' : '';
                return `<button class="option-btn ${state.customization.milk_type === m.value ? 'selected' : ''}"
                    onclick="selectOption('milk_type', '${m.value}')">${m.label}${priceAdd ? `<span class="price-add">${priceAdd}</span>` : ''}</button>`;
            }).join('');
    }

    // 额外选项
    const extrasContainer = document.getElementById('extras-options');
    if (extrasContainer) {
        extrasContainer.innerHTML = `
            <div class="extra-item">
                <label>
                    <input type="checkbox" ${state.customization.extra_shot ? 'checked' : ''}
                        onchange="toggleExtra('extra_shot')">
                    加浓缩
                </label>
                <span class="extra-price">+¥4</span>
            </div>
            <div class="extra-item">
                <label>
                    <input type="checkbox" ${state.customization.whipped_cream ? 'checked' : ''}
                        onchange="toggleExtra('whipped_cream')">
                    奶油顶
                </label>
                <span class="extra-price">免费</span>
            </div>
        `;
    }

    // 糖浆
    const syrupContainer = document.getElementById('syrup-options');
    if (syrupContainer) {
        syrupContainer.innerHTML = `<button class="option-btn ${!state.customization.syrup ? 'selected' : ''}"
            onclick="selectOption('syrup', null)">不加</button>` +
            opts.syrups.map(s => `<button class="option-btn ${state.customization.syrup === s.id ? 'selected' : ''}"
                onclick="selectOption('syrup', '${s.id}')">${s.name}<span class="price-add">+¥${s.price}</span></button>`).join('');
    }
}

// 选择选项
function selectOption(type, value) {
    state.customization[type] = value;
    updateCustomizationUI();
    updatePrice();
}

// 切换额外选项
function toggleExtra(type) {
    state.customization[type] = !state.customization[type];
    updatePrice();
}

// 更新价格
function updatePrice() {
    if (!state.selectedItem) return;

    let price = state.selectedItem.base_price;

    // 杯型
    if (state.customization.cup_size === 'VENTI') price += 4;
    if (state.customization.cup_size === 'TALL') price -= 3;

    // 奶类
    if (['OAT', 'COCONUT'].includes(state.customization.milk_type)) price += 3;

    // 加浓缩
    if (state.customization.extra_shot) price += 4;

    // 糖浆
    if (state.customization.syrup) price += 3;

    elements.totalPrice.textContent = price;
}

// 添加到购物车
function addToCart() {
    if (!state.selectedItem) return;

    // 记录订单到后端（用于推荐）
    fetchAPI('/user/order', {
        method: 'POST',
        body: JSON.stringify({
            user_id: 'guest',
            sku: state.selectedItem.sku
        })
    });

    showToast(`已添加 ${state.selectedItem.name} 到购物车`);
    closeModal();

    // 刷新推荐
    setTimeout(refreshRecommendations, 500);
}

// 刷新推荐
async function refreshRecommendations() {
    const recommendations = await fetchAPI('/recommendations?user_id=guest&limit=6');
    if (recommendations) {
        state.recommendations = recommendations.recommendations;
        renderRecommendations();
    }
}

// 渲染偏好标签
function renderPreferenceTags() {
    const allTags = ['经典', '人气', '网红', '低卡', '甜蜜', '清爽', '提神', '果香', '抹茶控', '巧克力'];

    elements.preferenceTags.innerHTML = allTags.map(tag =>
        `<span class="pref-tag ${state.userPreferences.tags.includes(tag) ? 'selected' : ''}"
            onclick="togglePreference('${tag}')">${tag}</span>`
    ).join('');
}

// 切换偏好
async function togglePreference(tag) {
    const index = state.userPreferences.tags.indexOf(tag);
    if (index > -1) {
        state.userPreferences.tags.splice(index, 1);
    } else {
        state.userPreferences.tags.push(tag);
    }

    renderPreferenceTags();

    // 更新后端偏好
    await fetchAPI('/user/preference', {
        method: 'POST',
        body: JSON.stringify({
            user_id: 'guest',
            tags_preference: state.userPreferences.tags
        })
    });

    // 刷新推荐
    refreshRecommendations();
}

// 显示加载
function showLoading() {
    elements.recommendationGrid.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
        </div>
    `;
}

// 显示提示
function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add('show');

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 2000);
}

// 点击遮罩关闭弹窗
elements.modalOverlay.addEventListener('click', (e) => {
    if (e.target === elements.modalOverlay) {
        closeModal();
    }
});

// 初始化应用
document.addEventListener('DOMContentLoaded', init);
