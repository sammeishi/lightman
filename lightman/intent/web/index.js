; (function () {
	/**
	 * 根APP
	 */
	const App = {
		components: {
			"root-intent-chart": RootIntentChart(),
			"sub-intent-chart": SubIntentChart(),
			"timeline-visualizer": TimelineVisualizer,
		},
		created() {
			const that = this
			window.setData = function (data) {
				console.log('got injrected data')
				that.applyNewData(data.asr, data.intent_groups)
			}
		},
		data() {
			return {
				asr: [],
				intentGroups: {},
				colorMap: {},
			}
		},
		mounted() {
			console.log('app mounted')
		},
		methods: {
			/**
			 * 设定新数据
			 */
			applyNewData(asr, ig) {
				if (asr) {
					this.asr = asr
				}
				if (ig) {
					this.intentGroups = ig
				}
				// 重新生成颜色
				this.generateColors()
			},
			/**
			 * 生成颜色
			 * 根据每一个意图
			 */
			generateColors() {
				this.colors = new Map()
				const all = (new Set(this.asr.map((item) => item.intent))).union(new Set(Object.keys(this.intentGroups)))
				let intents = [...all]
				intents = intents.filter((item) => item)
				intents = intents.sort(() => (Math.random() - 0.5))

				// 批量生成颜色
				function generateDistinctColors(n = 12) {
					if (n <= 0) return [];

					const colors = [];
					const step = 360 / n;
					const offset = Math.random() * 360;

					for (let i = 0; i < n; i++) {
						// 等分色相 + 小扰动，保证差异最大同时保持随机性
						let h = (offset + i * step + (Math.random() - 0.5) * 20) % 360;
						if (h < 0) h += 360;

						// 限制饱和度和亮度，避免灰色/过暗/过亮
						const s = 60 + Math.random() * 30; // 60% - 90%
						const l = 45 + Math.random() * 20; // 45% - 65%

						// HSL -> RGB
						const c = (1 - Math.abs(2 * l / 100 - 1)) * (s / 100);
						const x = c * (1 - Math.abs((h / 60) % 2 - 1));
						const m = l / 100 - c / 2;

						let r = 0, g = 0, b = 0;
						if (h < 60) [r, g, b] = [c, x, 0];
						else if (h < 120) [r, g, b] = [x, c, 0];
						else if (h < 180) [r, g, b] = [0, c, x];
						else if (h < 240) [r, g, b] = [0, x, c];
						else if (h < 300) [r, g, b] = [x, 0, c];
						else[r, g, b] = [c, 0, x];

						const toHex = v =>
							Math.round((v + m) * 255).toString(16).padStart(2, "0");

						colors.push(`#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase());
					}

					return colors;
				}
				let colors = generateDistinctColors(intents.length)

				// 使用HSL颜色模型，在色相环上均匀分布颜色
				intents.forEach((intent, index) => {
					this.colorMap[intent] = colors[index]
				})
			},
		},
	}

	const { createApp } = Vue
	const app = createApp(App)
	app.use(ElementPlus)
	app.mount("#app")
})()
