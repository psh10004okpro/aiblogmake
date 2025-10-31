/**
 * Content Repurposing Component
 *
 * 블로그 포스트를 다양한 형식으로 자동 변환
 */
export default {
    name: 'ContentRepurposing',

    data() {
        return {
            loading: false,
            converting: false,
            selectedFormat: null,

            // Input form
            inputForm: {
                title: '',
                content: '',
                keywords: ''
            },

            // Available formats
            availableFormats: [],

            // Conversion results
            results: {
                youtubeScript: null,
                infographic: null,
                socialCards: null,
                podcastScript: null,
                twitterThread: null
            },

            // Active tab
            activeTab: 'input'
        };
    },

    computed: {
        hasContent() {
            return this.inputForm.title && this.inputForm.content;
        },

        keywordsArray() {
            if (!this.inputForm.keywords) return [];
            return this.inputForm.keywords.split(',').map(k => k.trim()).filter(k => k);
        },

        hasResults() {
            return Object.values(this.results).some(r => r !== null);
        }
    },

    async mounted() {
        await this.loadAvailableFormats();
    },

    methods: {
        async loadAvailableFormats() {
            this.loading = true;
            try {
                const response = await api.contentRepurposing.getFormats();
                this.availableFormats = response.data.formats;
            } catch (error) {
                console.error('Failed to load formats:', error);
                this.$emit('show-toast', {
                    message: '형식 목록 로드 실패',
                    type: 'error'
                });
            } finally {
                this.loading = false;
            }
        },

        async convertToFormat(formatName) {
            if (!this.hasContent) {
                this.$emit('show-toast', {
                    message: '제목과 콘텐츠를 입력하세요.',
                    type: 'warning'
                });
                return;
            }

            this.converting = true;
            this.selectedFormat = formatName;

            try {
                const payload = {
                    title: this.inputForm.title,
                    content: this.inputForm.content,
                    keywords: this.keywordsArray
                };

                let response;

                switch (formatName) {
                    case 'youtube-script':
                        response = await api.contentRepurposing.createYouTubeScript(payload);
                        this.results.youtubeScript = response.data;
                        this.activeTab = 'youtube';
                        break;

                    case 'infographic':
                        response = await api.contentRepurposing.createInfographic(payload);
                        this.results.infographic = response.data;
                        this.activeTab = 'infographic';
                        break;

                    case 'social-media-cards':
                        response = await api.contentRepurposing.createSocialMediaCards({
                            ...payload,
                            platforms: ['instagram', 'facebook', 'linkedin']
                        });
                        this.results.socialCards = response.data;
                        this.activeTab = 'social';
                        break;

                    case 'podcast-script':
                        response = await api.contentRepurposing.createPodcastScript(payload);
                        this.results.podcastScript = response.data;
                        this.activeTab = 'podcast';
                        break;

                    case 'twitter-thread':
                        response = await api.contentRepurposing.createTwitterThread(payload);
                        this.results.twitterThread = response.data;
                        this.activeTab = 'twitter';
                        break;
                }

                this.$emit('show-toast', {
                    message: `${this.getFormatDisplayName(formatName)} 변환 완료!`,
                    type: 'success'
                });

            } catch (error) {
                console.error(`Failed to convert to ${formatName}:`, error);
                this.$emit('show-toast', {
                    message: `${this.getFormatDisplayName(formatName)} 변환 실패: ${error.response?.data?.detail || error.message}`,
                    type: 'error'
                });
            } finally {
                this.converting = false;
                this.selectedFormat = null;
            }
        },

        async convertToAll() {
            if (!this.hasContent) {
                this.$emit('show-toast', {
                    message: '제목과 콘텐츠를 입력하세요.',
                    type: 'warning'
                });
                return;
            }

            this.converting = true;

            try {
                const payload = {
                    title: this.inputForm.title,
                    content: this.inputForm.content,
                    keywords: this.keywordsArray
                };

                const response = await api.contentRepurposing.batchConvert(payload);
                const data = response.data;

                this.results.youtubeScript = data.youtube_script;
                this.results.infographic = data.infographic;
                this.results.socialCards = data.social_media_cards;
                this.results.podcastScript = data.podcast_script;
                this.results.twitterThread = data.twitter_thread;

                this.activeTab = 'youtube';

                this.$emit('show-toast', {
                    message: '모든 형식으로 변환 완료! (약 3-5분 소요)',
                    type: 'success'
                });

            } catch (error) {
                console.error('Failed to batch convert:', error);
                this.$emit('show-toast', {
                    message: `일괄 변환 실패: ${error.response?.data?.detail || error.message}`,
                    type: 'error'
                });
            } finally {
                this.converting = false;
            }
        },

        getFormatDisplayName(formatName) {
            const format = this.availableFormats.find(f => f.name === formatName);
            return format ? format.display_name : formatName;
        },

        getFormatIcon(formatName) {
            const icons = {
                'youtube-script': 'fa-youtube',
                'infographic': 'fa-chart-bar',
                'social-media-cards': 'fa-images',
                'podcast-script': 'fa-podcast',
                'twitter-thread': 'fa-twitter'
            };
            return icons[formatName] || 'fa-file';
        },

        getFormatColor(formatName) {
            const colors = {
                'youtube-script': 'red',
                'infographic': 'purple',
                'social-media-cards': 'pink',
                'podcast-script': 'indigo',
                'twitter-thread': 'blue'
            };
            return colors[formatName] || 'gray';
        },

        copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                this.$emit('show-toast', {
                    message: '클립보드에 복사되었습니다!',
                    type: 'success'
                });
            }).catch(() => {
                this.$emit('show-toast', {
                    message: '복사 실패',
                    type: 'error'
                });
            });
        },

        downloadAsJSON(data, filename) {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        },

        clearResults() {
            this.results = {
                youtubeScript: null,
                infographic: null,
                socialCards: null,
                podcastScript: null,
                twitterThread: null
            };
            this.activeTab = 'input';
        }
    },

    template: `
    <div class="content-repurposing">
        <div class="mb-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-2">
                <i class="fas fa-recycle mr-2"></i>콘텐츠 재활용 엔진
            </h2>
            <p class="text-gray-600">
                하나의 블로그 포스트를 5가지 형식으로 자동 변환하여 콘텐츠 생산성을 3-5배 증가시킵니다.
            </p>
        </div>

        <!-- Input Form -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-edit mr-2"></i>블로그 포스트 입력
            </h3>

            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        제목
                    </label>
                    <input
                        v-model="inputForm.title"
                        type="text"
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="블로그 포스트 제목을 입력하세요"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        콘텐츠 (HTML)
                    </label>
                    <textarea
                        v-model="inputForm.content"
                        rows="10"
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                        placeholder="블로그 포스트 HTML 콘텐츠를 입력하세요"
                    ></textarea>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        키워드 (쉼표로 구분)
                    </label>
                    <input
                        v-model="inputForm.keywords"
                        type="text"
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="예: AI, 블로그, 자동화"
                    />
                </div>
            </div>
        </div>

        <!-- Conversion Buttons -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-magic mr-2"></i>변환 형식 선택
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                <button
                    v-for="format in availableFormats"
                    :key="format.name"
                    @click="convertToFormat(format.name)"
                    :disabled="!hasContent || converting"
                    :class="[
                        'flex items-center justify-between p-4 rounded-lg border-2 transition-all',
                        converting && selectedFormat === format.name
                            ? 'border-gray-400 bg-gray-50 cursor-wait'
                            : 'border-gray-200 hover:border-' + getFormatColor(format.name) + '-500 hover:bg-' + getFormatColor(format.name) + '-50',
                        !hasContent ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                    ]"
                >
                    <div class="flex items-center">
                        <i :class="['fas', getFormatIcon(format.name), 'text-2xl mr-3 text-' + getFormatColor(format.name) + '-500']"></i>
                        <div class="text-left">
                            <div class="font-semibold text-gray-900">{{ format.display_name }}</div>
                            <div class="text-xs text-gray-500">{{ format.estimated_time }}</div>
                        </div>
                    </div>
                    <div v-if="converting && selectedFormat === format.name">
                        <i class="fas fa-spinner fa-spin text-gray-400"></i>
                    </div>
                </button>
            </div>

            <div class="border-t pt-4">
                <button
                    @click="convertToAll"
                    :disabled="!hasContent || converting"
                    class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                    <i class="fas fa-bolt mr-2"></i>
                    {{ converting ? '변환 중...' : '모든 형식으로 일괄 변환 (3-5분)' }}
                </button>
            </div>
        </div>

        <!-- Results Tabs -->
        <div v-if="hasResults" class="bg-white rounded-lg shadow-md">
            <div class="border-b">
                <div class="flex overflow-x-auto">
                    <button
                        @click="activeTab = 'youtube'"
                        :class="[
                            'px-6 py-3 font-medium border-b-2 transition-colors whitespace-nowrap',
                            activeTab === 'youtube'
                                ? 'border-red-500 text-red-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        ]"
                        v-if="results.youtubeScript"
                    >
                        <i class="fab fa-youtube mr-2"></i>YouTube 스크립트
                    </button>
                    <button
                        @click="activeTab = 'infographic'"
                        :class="[
                            'px-6 py-3 font-medium border-b-2 transition-colors whitespace-nowrap',
                            activeTab === 'infographic'
                                ? 'border-purple-500 text-purple-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        ]"
                        v-if="results.infographic"
                    >
                        <i class="fas fa-chart-bar mr-2"></i>인포그래픽
                    </button>
                    <button
                        @click="activeTab = 'social'"
                        :class="[
                            'px-6 py-3 font-medium border-b-2 transition-colors whitespace-nowrap',
                            activeTab === 'social'
                                ? 'border-pink-500 text-pink-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        ]"
                        v-if="results.socialCards"
                    >
                        <i class="fas fa-images mr-2"></i>소셜 미디어 카드
                    </button>
                    <button
                        @click="activeTab = 'podcast'"
                        :class="[
                            'px-6 py-3 font-medium border-b-2 transition-colors whitespace-nowrap',
                            activeTab === 'podcast'
                                ? 'border-indigo-500 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        ]"
                        v-if="results.podcastScript"
                    >
                        <i class="fas fa-podcast mr-2"></i>팟캐스트 스크립트
                    </button>
                    <button
                        @click="activeTab = 'twitter'"
                        :class="[
                            'px-6 py-3 font-medium border-b-2 transition-colors whitespace-nowrap',
                            activeTab === 'twitter'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                        ]"
                        v-if="results.twitterThread"
                    >
                        <i class="fab fa-twitter mr-2"></i>Twitter 스레드
                    </button>
                </div>
            </div>

            <div class="p-6">
                <!-- YouTube Script -->
                <div v-if="activeTab === 'youtube' && results.youtubeScript" class="space-y-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">YouTube 스크립트</h3>
                        <button
                            @click="downloadAsJSON(results.youtubeScript, 'youtube-script.json')"
                            class="text-sm text-blue-600 hover:text-blue-700"
                        >
                            <i class="fas fa-download mr-1"></i>다운로드
                        </button>
                    </div>

                    <div class="space-y-3">
                        <div class="bg-red-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-red-800 mb-2">훅 (첫 15초)</h4>
                            <p class="text-gray-700">{{ results.youtubeScript.hook }}</p>
                        </div>

                        <div class="bg-blue-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-blue-800 mb-2">인트로</h4>
                            <p class="text-gray-700">{{ results.youtubeScript.intro }}</p>
                        </div>

                        <div class="bg-green-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-green-800 mb-2">메인 콘텐츠</h4>
                            <div v-for="(point, idx) in results.youtubeScript.main_points" :key="idx" class="mb-2">
                                <div class="font-mono text-sm text-gray-600">{{ point.timestamp }}</div>
                                <p class="text-gray-700">{{ point.content }}</p>
                            </div>
                        </div>

                        <div class="bg-yellow-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-yellow-800 mb-2">아웃트로 & CTA</h4>
                            <p class="text-gray-700 mb-2">{{ results.youtubeScript.outro }}</p>
                            <p class="text-gray-700 font-medium">{{ results.youtubeScript.cta }}</p>
                        </div>

                        <div class="bg-purple-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-purple-800 mb-2">썸네일 아이디어</h4>
                            <ul class="list-disc list-inside space-y-1">
                                <li v-for="(idea, idx) in results.youtubeScript.thumbnail_ideas" :key="idx" class="text-gray-700">
                                    {{ idea }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Infographic -->
                <div v-if="activeTab === 'infographic' && results.infographic" class="space-y-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">인포그래픽 데이터</h3>
                        <button
                            @click="downloadAsJSON(results.infographic, 'infographic-data.json')"
                            class="text-sm text-blue-600 hover:text-blue-700"
                        >
                            <i class="fas fa-download mr-1"></i>다운로드
                        </button>
                    </div>

                    <div class="bg-gradient-to-r from-purple-100 to-pink-100 p-6 rounded-lg mb-4">
                        <h4 class="text-2xl font-bold text-gray-900 mb-2">{{ results.infographic.title }}</h4>
                        <p class="text-lg text-gray-700">{{ results.infographic.subtitle }}</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div
                            v-for="(stat, idx) in results.infographic.main_stats"
                            :key="idx"
                            class="bg-white border-2 border-purple-200 p-4 rounded-lg text-center"
                        >
                            <div class="text-3xl mb-2">{{ stat.icon }}</div>
                            <div class="text-2xl font-bold text-purple-600">{{ stat.value }}</div>
                            <div class="text-sm text-gray-600">{{ stat.label }}</div>
                        </div>
                    </div>

                    <div v-for="(section, idx) in results.infographic.sections" :key="idx" class="bg-gray-50 p-4 rounded-lg mb-3">
                        <h4 class="font-semibold text-gray-900 mb-2">{{ section.title }}</h4>
                        <ul class="list-disc list-inside space-y-1">
                            <li v-for="(point, pidx) in section.points" :key="pidx" class="text-gray-700">
                                {{ point }}
                            </li>
                        </ul>
                    </div>

                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-blue-800 mb-2">핵심 정리</h4>
                        <ul class="list-disc list-inside space-y-1">
                            <li v-for="(takeaway, idx) in results.infographic.key_takeaways" :key="idx" class="text-gray-700 font-medium">
                                {{ takeaway }}
                            </li>
                        </ul>
                    </div>

                    <div class="text-sm text-gray-600">
                        <strong>추천 컬러:</strong> {{ results.infographic.color_scheme }} |
                        <strong>레이아웃:</strong> {{ results.infographic.layout_type }}
                    </div>
                </div>

                <!-- Social Media Cards -->
                <div v-if="activeTab === 'social' && results.socialCards" class="space-y-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">소셜 미디어 카드</h3>
                    </div>

                    <div
                        v-for="card in results.socialCards"
                        :key="card.platform"
                        class="border-2 border-gray-200 rounded-lg p-6 mb-4"
                    >
                        <div class="flex justify-between items-center mb-4">
                            <h4 class="text-lg font-semibold text-gray-900 capitalize">
                                <i :class="['fab fa-' + card.platform, 'mr-2']"></i>{{ card.platform }}
                            </h4>
                            <span class="text-sm text-gray-500">{{ card.character_count }} 자</span>
                        </div>

                        <div class="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg mb-3">
                            <h5 class="text-xl font-bold text-gray-900 mb-2">{{ card.headline }}</h5>
                            <p class="text-gray-700">{{ card.subheadline }}</p>
                        </div>

                        <div class="mb-3">
                            <h5 class="font-semibold text-gray-800 mb-2">핵심 포인트:</h5>
                            <ul class="space-y-1">
                                <li v-for="(point, idx) in card.key_points" :key="idx" class="flex items-start">
                                    <span class="text-green-500 mr-2">✓</span>
                                    <span class="text-gray-700">{{ point }}</span>
                                </li>
                            </ul>
                        </div>

                        <div class="mb-3">
                            <h5 class="font-semibold text-gray-800 mb-2">CTA:</h5>
                            <p class="text-blue-600 font-medium">{{ card.call_to_action }}</p>
                        </div>

                        <div class="mb-3">
                            <h5 class="font-semibold text-gray-800 mb-2">해시태그:</h5>
                            <p class="text-blue-500">{{ card.hashtags.join(' ') }}</p>
                        </div>

                        <div>
                            <h5 class="font-semibold text-gray-800 mb-2">시각 요소 제안:</h5>
                            <ul class="text-sm text-gray-600 space-y-1">
                                <li v-for="(element, idx) in card.visual_elements" :key="idx">
                                    • {{ element }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Podcast Script -->
                <div v-if="activeTab === 'podcast' && results.podcastScript" class="space-y-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">팟캐스트 스크립트</h3>
                        <button
                            @click="downloadAsJSON(results.podcastScript, 'podcast-script.json')"
                            class="text-sm text-blue-600 hover:text-blue-700"
                        >
                            <i class="fas fa-download mr-1"></i>다운로드
                        </button>
                    </div>

                    <div class="bg-indigo-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-indigo-800 mb-2">호스트 인트로</h4>
                        <p class="text-gray-700">{{ results.podcastScript.host_intro }}</p>
                    </div>

                    <div v-for="(segment, idx) in results.podcastScript.segments" :key="idx" class="bg-gray-50 p-4 rounded-lg">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="font-semibold text-gray-900">{{ segment.title }}</h4>
                            <span class="text-sm text-gray-500">{{ segment.duration }}</span>
                        </div>
                        <ul class="list-disc list-inside space-y-1">
                            <li v-for="(point, pidx) in segment.talking_points" :key="pidx" class="text-gray-700">
                                {{ point }}
                            </li>
                        </ul>
                    </div>

                    <div v-if="results.podcastScript.guest_questions.length > 0" class="bg-green-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-green-800 mb-2">게스트 인터뷰 질문</h4>
                        <ol class="list-decimal list-inside space-y-1">
                            <li v-for="(question, idx) in results.podcastScript.guest_questions" :key="idx" class="text-gray-700">
                                {{ question }}
                            </li>
                        </ol>
                    </div>

                    <div class="bg-yellow-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-yellow-800 mb-2">쇼노트 (Show Notes)</h4>
                        <ul class="font-mono text-sm space-y-1">
                            <li v-for="(note, idx) in results.podcastScript.show_notes" :key="idx" class="text-gray-700">
                                {{ note }}
                            </li>
                        </ul>
                    </div>
                </div>

                <!-- Twitter Thread -->
                <div v-if="activeTab === 'twitter' && results.twitterThread" class="space-y-3">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-gray-900">Twitter 스레드 ({{ results.twitterThread.total_tweets }}개 트윗)</h3>
                        <span class="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                            예상 인게이지먼트: {{ results.twitterThread.estimated_engagement }}
                        </span>
                    </div>

                    <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                        <div class="flex items-start">
                            <span class="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">1</span>
                            <p class="text-gray-800 flex-1">{{ results.twitterThread.hook_tweet }}</p>
                        </div>
                    </div>

                    <div
                        v-for="(tweet, idx) in results.twitterThread.thread_tweets"
                        :key="idx"
                        class="bg-gray-50 border-l-4 border-gray-300 p-4 rounded"
                    >
                        <div class="flex items-start">
                            <span class="bg-gray-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">{{ idx + 2 }}</span>
                            <p class="text-gray-800 flex-1">{{ tweet }}</p>
                        </div>
                    </div>

                    <div class="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                        <div class="flex items-start">
                            <span class="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">{{ results.twitterThread.thread_tweets.length + 2 }}</span>
                            <p class="text-gray-800 flex-1">{{ results.twitterThread.conclusion_tweet }}</p>
                        </div>
                    </div>

                    <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                        <div class="flex items-start">
                            <span class="bg-yellow-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">{{ results.twitterThread.total_tweets }}</span>
                            <p class="text-gray-800 flex-1">{{ results.twitterThread.cta_tweet }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="border-t p-4 bg-gray-50 rounded-b-lg">
                <button
                    @click="clearResults"
                    class="text-red-600 hover:text-red-700 font-medium"
                >
                    <i class="fas fa-times mr-2"></i>결과 지우기
                </button>
            </div>
        </div>

        <!-- Empty State -->
        <div v-if="!hasResults && !converting" class="bg-gray-50 rounded-lg p-12 text-center">
            <i class="fas fa-recycle text-6xl text-gray-300 mb-4"></i>
            <p class="text-gray-500 text-lg">
                위에서 블로그 콘텐츠를 입력하고 변환 형식을 선택하세요
            </p>
        </div>
    </div>
    `
};
