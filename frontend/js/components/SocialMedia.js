/**
 * Social Media Auto-Posting Component
 *
 * Manages automated social media posting to Facebook, Twitter, and LinkedIn.
 */
export default {
    name: 'SocialMedia',

    data() {
        return {
            status: null,
            loading: false,
            posting: false,
            testingPlatform: null,

            // Post form
            postForm: {
                title: '',
                excerpt: '',
                keywords: '',
                link: '',
                image_url: '',
                platforms: []
            },

            // Available platforms
            availablePlatforms: [
                { id: 'facebook', name: 'Facebook', icon: 'fa-facebook', color: 'blue' },
                { id: 'twitter', name: 'Twitter (X)', icon: 'fa-twitter', color: 'sky' },
                { id: 'linkedin', name: 'LinkedIn', icon: 'fa-linkedin', color: 'blue' }
            ],

            // Last results
            lastResults: null
        };
    },

    computed: {
        configuredPlatforms() {
            if (!this.status || !this.status.configured_platforms) return [];
            return this.availablePlatforms.filter(p =>
                this.status.configured_platforms.includes(p.id)
            );
        },

        unconfiguredPlatforms() {
            if (!this.status || !this.status.configured_platforms) return this.availablePlatforms;
            return this.availablePlatforms.filter(p =>
                !this.status.configured_platforms.includes(p.id)
            );
        },

        hasConfiguredPlatforms() {
            return this.configuredPlatforms.length > 0;
        },

        selectedPlatforms() {
            return this.postForm.platforms;
        }
    },

    async mounted() {
        await this.loadStatus();
    },

    methods: {
        async loadStatus() {
            this.loading = true;
            try {
                const response = await api.socialMedia.getStatus();
                this.status = response.data;
            } catch (error) {
                console.error('Failed to load social media status:', error);
                this.$emit('show-toast', {
                    message: '소셜 미디어 상태 로드 실패',
                    type: 'error'
                });
            } finally {
                this.loading = false;
            }
        },

        togglePlatform(platformId) {
            const index = this.postForm.platforms.indexOf(platformId);
            if (index > -1) {
                this.postForm.platforms.splice(index, 1);
            } else {
                this.postForm.platforms.push(platformId);
            }
        },

        isPlatformSelected(platformId) {
            return this.postForm.platforms.includes(platformId);
        },

        async postToSocialMedia() {
            // Validation
            if (!this.postForm.title || !this.postForm.excerpt || !this.postForm.link) {
                this.$emit('show-toast', {
                    message: '제목, 요약, 링크를 입력하세요.',
                    type: 'warning'
                });
                return;
            }

            if (this.postForm.platforms.length === 0) {
                this.$emit('show-toast', {
                    message: '최소 하나의 플랫폼을 선택하세요.',
                    type: 'warning'
                });
                return;
            }

            this.posting = true;
            this.lastResults = null;

            try {
                const keywords = this.postForm.keywords
                    .split(',')
                    .map(k => k.trim())
                    .filter(k => k.length > 0);

                const response = await api.socialMedia.post({
                    title: this.postForm.title,
                    excerpt: this.postForm.excerpt,
                    keywords,
                    link: this.postForm.link,
                    image_url: this.postForm.image_url || null,
                    platforms: this.postForm.platforms
                });

                this.lastResults = response.data.results;

                const successCount = response.data.summary.succeeded;
                const totalCount = response.data.summary.total_platforms;

                if (successCount > 0) {
                    this.$emit('show-toast', {
                        message: `${successCount}/${totalCount} 플랫폼에 포스팅 성공!`,
                        type: 'success'
                    });
                } else {
                    this.$emit('show-toast', {
                        message: '모든 플랫폼에 포스팅 실패',
                        type: 'error'
                    });
                }

            } catch (error) {
                console.error('Failed to post to social media:', error);
                this.$emit('show-toast', {
                    message: error.response?.data?.detail || '소셜 미디어 포스팅 실패',
                    type: 'error'
                });
            } finally {
                this.posting = false;
            }
        },

        async testPlatform(platformId) {
            this.testingPlatform = platformId;

            try {
                this.$emit('show-toast', {
                    message: `${platformId} 테스트 포스팅 중...`,
                    type: 'info'
                });

                await api.socialMedia.test();

                this.$emit('show-toast', {
                    message: '테스트 포스팅 성공!',
                    type: 'success'
                });

            } catch (error) {
                console.error('Test post failed:', error);
                this.$emit('show-toast', {
                    message: '테스트 포스팅 실패',
                    type: 'error'
                });
            } finally {
                this.testingPlatform = null;
            }
        },

        resetForm() {
            this.postForm = {
                title: '',
                excerpt: '',
                keywords: '',
                link: '',
                image_url: '',
                platforms: []
            };
            this.lastResults = null;
        },

        getPlatformInfo(platformId) {
            return this.availablePlatforms.find(p => p.id === platformId);
        }
    },

    template: `
        <div class="social-media-container">
            <!-- Page Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">소셜 미디어 자동 포스팅</h1>
                <p class="text-gray-600">Facebook, Twitter, LinkedIn에 자동으로 포스팅하세요</p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">로딩 중...</p>
            </div>

            <div v-else class="space-y-6">
                <!-- Platform Status -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold">플랫폼 상태</h2>
                        <button @click="loadStatus" class="btn btn-sm btn-secondary">
                            <i class="fas fa-sync-alt"></i>
                            새로고침
                        </button>
                    </div>
                    <div class="card-content">
                        <!-- Configured Platforms -->
                        <div v-if="hasConfiguredPlatforms" class="mb-6">
                            <h3 class="font-semibold mb-3">설정된 플랫폼</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div
                                    v-for="platform in configuredPlatforms"
                                    :key="platform.id"
                                    class="flex items-center gap-3 p-4 border-2 border-green-200 bg-green-50 rounded-lg"
                                >
                                    <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                                        <i :class="['fab', platform.icon, 'text-' + platform.color + '-600', 'text-2xl']"></i>
                                    </div>
                                    <div class="flex-1">
                                        <div class="font-semibold">{{ platform.name }}</div>
                                        <div class="text-xs text-green-700">준비됨</div>
                                    </div>
                                    <i class="fas fa-check-circle text-green-600 text-xl"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Unconfigured Platforms -->
                        <div v-if="unconfiguredPlatforms.length > 0">
                            <h3 class="font-semibold mb-3">미설정 플랫폼</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div
                                    v-for="platform in unconfiguredPlatforms"
                                    :key="platform.id"
                                    class="flex items-center gap-3 p-4 border border-gray-200 bg-gray-50 rounded-lg opacity-60"
                                >
                                    <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                                        <i :class="['fab', platform.icon, 'text-gray-400', 'text-2xl']"></i>
                                    </div>
                                    <div class="flex-1">
                                        <div class="font-semibold text-gray-600">{{ platform.name }}</div>
                                        <div class="text-xs text-gray-500">미설정</div>
                                    </div>
                                    <i class="fas fa-times-circle text-gray-400 text-xl"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Configuration Guide -->
                        <div v-if="!hasConfiguredPlatforms" class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <h4 class="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
                                <i class="fas fa-exclamation-triangle"></i>
                                소셜 미디어 설정 필요
                            </h4>
                            <p class="text-sm text-yellow-800 mb-3">
                                자동 포스팅 기능을 사용하려면 .env 파일에서 플랫폼별 API 키를 설정하세요.
                            </p>
                            <p class="text-sm text-yellow-800">
                                자세한 설정 방법은 <a href="/docs/SOCIAL_MEDIA.md" target="_blank" class="underline font-medium">소셜 미디어 문서</a>를 참조하세요.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Post Form -->
                <div v-if="hasConfiguredPlatforms" class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold">새 포스트</h2>
                        <button @click="resetForm" class="btn btn-sm btn-secondary">
                            <i class="fas fa-redo"></i>
                            초기화
                        </button>
                    </div>
                    <div class="card-content">
                        <form @submit.prevent="postToSocialMedia" class="space-y-4">
                            <!-- Title -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    제목 *
                                </label>
                                <input
                                    v-model="postForm.title"
                                    type="text"
                                    class="input"
                                    placeholder="블로그 포스트 제목"
                                    required
                                />
                            </div>

                            <!-- Excerpt -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    요약 *
                                </label>
                                <textarea
                                    v-model="postForm.excerpt"
                                    rows="3"
                                    class="input"
                                    placeholder="포스트 요약 (2-3문장)"
                                    required
                                ></textarea>
                            </div>

                            <!-- Keywords -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    키워드
                                </label>
                                <input
                                    v-model="postForm.keywords"
                                    type="text"
                                    class="input"
                                    placeholder="SEO, 마케팅, 블로그 (쉼표로 구분)"
                                />
                                <p class="text-xs text-gray-500 mt-1">
                                    해시태그 생성에 사용됩니다
                                </p>
                            </div>

                            <!-- Link -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    링크 *
                                </label>
                                <input
                                    v-model="postForm.link"
                                    type="url"
                                    class="input"
                                    placeholder="https://yourblog.com/post"
                                    required
                                />
                            </div>

                            <!-- Image URL -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    이미지 URL (선택)
                                </label>
                                <input
                                    v-model="postForm.image_url"
                                    type="url"
                                    class="input"
                                    placeholder="https://yourblog.com/image.jpg"
                                />
                            </div>

                            <!-- Platform Selection -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-3">
                                    포스팅할 플랫폼 선택 *
                                </label>
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div
                                        v-for="platform in configuredPlatforms"
                                        :key="platform.id"
                                        @click="togglePlatform(platform.id)"
                                        :class="isPlatformSelected(platform.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'"
                                        class="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer hover:border-blue-300 transition"
                                    >
                                        <i :class="['fab', platform.icon, 'text-' + platform.color + '-600', 'text-2xl']"></i>
                                        <div class="flex-1">
                                            <div class="font-semibold">{{ platform.name }}</div>
                                        </div>
                                        <i v-if="isPlatformSelected(platform.id)" class="fas fa-check-circle text-blue-600"></i>
                                        <i v-else class="far fa-circle text-gray-400"></i>
                                    </div>
                                </div>
                            </div>

                            <!-- Submit Button -->
                            <div class="flex gap-3">
                                <button
                                    type="submit"
                                    :disabled="posting"
                                    class="btn btn-primary"
                                >
                                    <i class="fas" :class="posting ? 'fa-spinner fa-spin' : 'fa-share-alt'"></i>
                                    {{ posting ? '포스팅 중...' : '소셜 미디어에 포스팅' }}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Last Results -->
                <div v-if="lastResults" class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold">포스팅 결과</h2>
                    </div>
                    <div class="card-content">
                        <div class="space-y-3">
                            <div
                                v-for="(result, platform) in lastResults"
                                :key="platform"
                                :class="result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'"
                                class="flex items-center justify-between p-4 border rounded-lg"
                            >
                                <div class="flex items-center gap-3">
                                    <i :class="['fab', getPlatformInfo(platform).icon, result.success ? 'text-green-600' : 'text-red-600', 'text-2xl']"></i>
                                    <div>
                                        <div class="font-semibold">{{ getPlatformInfo(platform).name }}</div>
                                        <div v-if="result.success && result.url" class="text-xs">
                                            <a :href="result.url" target="_blank" class="text-blue-600 hover:underline">
                                                포스트 보기 →
                                            </a>
                                        </div>
                                        <div v-else-if="result.error" class="text-xs text-red-700">
                                            {{ result.error }}
                                        </div>
                                    </div>
                                </div>
                                <i :class="result.success ? 'fa-check text-green-600' : 'fa-times text-red-600'" class="fas text-xl"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
