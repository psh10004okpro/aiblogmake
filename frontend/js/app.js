/**
 * Main Application Entry Point
 *
 * Initializes Vue 3 application and manages routing and state.
 */
import Dashboard from './components/Dashboard.js';
import Workflows from './components/Workflows.js';
import SEOScores from './components/SEOScores.js';
import Analytics from './components/Analytics.js';
import SocialMedia from './components/SocialMedia.js';
import ContentRepurposing from './components/ContentRepurposing.js';
import Settings from './components/Settings.js';

const { createApp } = Vue;

// Create Vue application
const app = createApp({
    data() {
        return {
            currentPage: 'dashboard',
            showStartModal: false,
            toasts: [],
            toastIdCounter: 0,

            // Start workflow form
            startWorkflowForm: {
                seed_keywords: '',
                num_posts: 2,
                auto_publish: false,
                schedule_time: null
            }
        };
    },

    computed: {
        navItems() {
            return [
                { id: 'dashboard', label: '대시보드', icon: 'fa-home' },
                { id: 'workflows', label: '워크플로우', icon: 'fa-project-diagram' },
                { id: 'seo', label: 'SEO 점수', icon: 'fa-chart-line' },
                { id: 'analytics', label: 'Analytics', icon: 'fa-chart-bar' },
                { id: 'social', label: '소셜 미디어', icon: 'fa-share-alt' },
                { id: 'repurposing', label: '콘텐츠 재활용', icon: 'fa-recycle' },
                { id: 'settings', label: '설정', icon: 'fa-cog' }
            ];
        }
    },

    mounted() {
        // Set initial page from URL hash
        const hash = window.location.hash.slice(1);
        if (hash && this.navItems.find(item => item.id === hash)) {
            this.currentPage = hash;
        }

        // Listen for hash changes
        window.addEventListener('hashchange', () => {
            const newHash = window.location.hash.slice(1);
            if (newHash && this.navItems.find(item => item.id === newHash)) {
                this.currentPage = newHash;
            }
        });
    },

    methods: {
        navigateTo(page) {
            this.currentPage = page;
            window.location.hash = page;
        },

        openStartModal() {
            this.showStartModal = true;
        },

        closeStartModal() {
            this.showStartModal = false;
            this.resetStartWorkflowForm();
        },

        resetStartWorkflowForm() {
            this.startWorkflowForm = {
                seed_keywords: '',
                num_posts: 2,
                auto_publish: false,
                schedule_time: null
            };
        },

        async startWorkflow() {
            // Validate form
            if (!this.startWorkflowForm.seed_keywords.trim()) {
                this.showToast({
                    message: '시드 키워드를 입력하세요.',
                    type: 'warning'
                });
                return;
            }

            if (this.startWorkflowForm.num_posts < 1 || this.startWorkflowForm.num_posts > 10) {
                this.showToast({
                    message: '포스트 수는 1-10개 사이여야 합니다.',
                    type: 'warning'
                });
                return;
            }

            try {
                // Parse seed keywords
                const keywords = this.startWorkflowForm.seed_keywords
                    .split(',')
                    .map(k => k.trim())
                    .filter(k => k.length > 0);

                if (keywords.length === 0) {
                    this.showToast({
                        message: '유효한 키워드를 입력하세요.',
                        type: 'warning'
                    });
                    return;
                }

                // Prepare request data
                const data = {
                    seed_keywords: keywords,
                    num_posts: this.startWorkflowForm.num_posts,
                    auto_publish: this.startWorkflowForm.auto_publish
                };

                if (this.startWorkflowForm.schedule_time) {
                    data.schedule_time = this.startWorkflowForm.schedule_time;
                }

                // Start workflow
                const response = await api.workflows.start(data);

                this.showToast({
                    message: `워크플로우 #${response.data.workflow_id}가 시작되었습니다!`,
                    type: 'success'
                });

                // Close modal
                this.closeStartModal();

                // Navigate to workflows page
                this.navigateTo('workflows');

                // Trigger refresh on workflows component
                this.$refs.workflowsComponent?.loadWorkflows();

            } catch (error) {
                console.error('Failed to start workflow:', error);
                this.showToast({
                    message: error.response?.data?.detail || '워크플로우 시작 실패',
                    type: 'error'
                });
            }
        },

        showToast(toast) {
            const id = this.toastIdCounter++;
            const toastWithId = {
                ...toast,
                id,
                timestamp: Date.now()
            };

            this.toasts.push(toastWithId);

            // Auto remove after 5 seconds
            setTimeout(() => {
                this.removeToast(id);
            }, 5000);
        },

        removeToast(id) {
            const index = this.toasts.findIndex(t => t.id === id);
            if (index !== -1) {
                this.toasts.splice(index, 1);
            }
        },

        getToastIcon(type) {
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-times-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            return icons[type] || 'fa-info-circle';
        },

        getToastClass(type) {
            const classes = {
                success: 'toast-success',
                error: 'toast-error',
                warning: 'toast-warning',
                info: 'toast-info'
            };
            return classes[type] || 'toast-info';
        }
    },

    // Register child components
    components: {
        Dashboard,
        Workflows,
        SEOScores,
        Analytics,
        SocialMedia,
        ContentRepurposing,
        Settings
    },

    template: `
        <div id="app">
            <!-- Navigation Bar -->
            <nav class="navbar">
                <div class="navbar-container">
                    <div class="navbar-brand">
                        <i class="fas fa-blog text-2xl mr-2"></i>
                        <span class="text-xl font-bold">AI 블로그 자동화</span>
                    </div>

                    <div class="navbar-menu">
                        <a
                            v-for="item in navItems"
                            :key="item.id"
                            @click.prevent="navigateTo(item.id)"
                            :class="{ 'navbar-item-active': currentPage === item.id }"
                            class="navbar-item"
                            href="#"
                        >
                            <i :class="'fas ' + item.icon"></i>
                            <span>{{ item.label }}</span>
                        </a>
                    </div>

                    <div class="navbar-actions">
                        <button @click="openStartModal" class="btn btn-primary">
                            <i class="fas fa-play"></i>
                            워크플로우 시작
                        </button>
                    </div>
                </div>
            </nav>

            <!-- Main Content -->
            <main class="main-content">
                <div class="container">
                    <!-- Dashboard Page -->
                    <Dashboard
                        v-if="currentPage === 'dashboard'"
                        @show-toast="showToast"
                        @navigate="navigateTo"
                    />

                    <!-- Workflows Page -->
                    <Workflows
                        v-if="currentPage === 'workflows'"
                        ref="workflowsComponent"
                        @show-toast="showToast"
                    />

                    <!-- SEO Scores Page -->
                    <SEOScores
                        v-if="currentPage === 'seo'"
                        @show-toast="showToast"
                    />

                    <!-- Analytics Page -->
                    <Analytics
                        v-if="currentPage === 'analytics'"
                        @show-toast="showToast"
                    />

                    <!-- Social Media Page -->
                    <SocialMedia
                        v-if="currentPage === 'social'"
                        @show-toast="showToast"
                    />

                    <!-- Content Repurposing Page -->
                    <ContentRepurposing
                        v-if="currentPage === 'repurposing'"
                        @show-toast="showToast"
                    />

                    <!-- Settings Page -->
                    <Settings
                        v-if="currentPage === 'settings'"
                        @show-toast="showToast"
                    />
                </div>
            </main>

            <!-- Start Workflow Modal -->
            <div v-if="showStartModal" class="modal-overlay" @click="closeStartModal">
                <div class="modal-content" @click.stop>
                    <div class="modal-header">
                        <h2 class="text-2xl font-bold">새 워크플로우 시작</h2>
                        <button @click="closeStartModal" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>

                    <div class="modal-body">
                        <form @submit.prevent="startWorkflow" class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    시드 키워드 *
                                </label>
                                <input
                                    v-model="startWorkflowForm.seed_keywords"
                                    type="text"
                                    class="input"
                                    placeholder="예: 블로그 SEO, 콘텐츠 마케팅 (쉼표로 구분)"
                                    required
                                />
                                <p class="text-sm text-gray-500 mt-1">
                                    쉼표(,)로 구분하여 여러 키워드를 입력할 수 있습니다.
                                </p>
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    생성할 포스트 수 *
                                </label>
                                <input
                                    v-model.number="startWorkflowForm.num_posts"
                                    type="number"
                                    min="1"
                                    max="10"
                                    class="input"
                                    required
                                />
                                <p class="text-sm text-gray-500 mt-1">
                                    1-10개의 포스트를 생성할 수 있습니다.
                                </p>
                            </div>

                            <div>
                                <label class="flex items-center gap-2">
                                    <input
                                        v-model="startWorkflowForm.auto_publish"
                                        type="checkbox"
                                        class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                    />
                                    <span class="text-sm font-medium text-gray-700">
                                        자동으로 WordPress에 발행
                                    </span>
                                </label>
                                <p class="text-sm text-gray-500 mt-1 ml-6">
                                    체크하면 생성된 포스트를 자동으로 WordPress에 발행합니다.
                                </p>
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    예약 시간 (선택사항)
                                </label>
                                <input
                                    v-model="startWorkflowForm.schedule_time"
                                    type="datetime-local"
                                    class="input"
                                />
                                <p class="text-sm text-gray-500 mt-1">
                                    지정한 시간에 워크플로우를 시작합니다. 비워두면 즉시 시작됩니다.
                                </p>
                            </div>
                        </form>
                    </div>

                    <div class="modal-footer">
                        <button @click="closeStartModal" type="button" class="btn btn-secondary">
                            취소
                        </button>
                        <button @click="startWorkflow" type="button" class="btn btn-primary">
                            <i class="fas fa-play"></i>
                            시작
                        </button>
                    </div>
                </div>
            </div>

            <!-- Toast Notifications -->
            <div class="toast-container">
                <div
                    v-for="toast in toasts"
                    :key="toast.id"
                    :class="getToastClass(toast.type)"
                    class="toast"
                >
                    <div class="flex items-start gap-3">
                        <i :class="getToastIcon(toast.type)" class="fas text-lg mt-0.5"></i>
                        <div class="flex-1">
                            <p class="font-medium">{{ toast.message }}</p>
                        </div>
                        <button @click="removeToast(toast.id)" class="text-current opacity-70 hover:opacity-100">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
});

// Mount the app
app.mount('#app');
