function SubIntentChart() {
	/**
 * char对象
 * 不能放进vue.data内，导致鼠标放大图像消失
 */
	let chartObj = null

	/**
	 * 所有意图占比统计图
	 * 全部意图都会列出来，不包含父意图
	 */
	return {
		name: "SubIntentChart",
		props: {
			colorMap: {
				type: Object,
				required: true,
			},
			intentGroups: {
				type: Object,
				required: true,
			},
			asr: {
				type: Array,
				required: true,
			},
		},
		template: document.querySelector("#subIntentChartTemplate").innerHTML,
		watch: {
			// 监听分组变化
			intentGroups() {
				this.update()
			},
		},
		mounted() {
			if (!chartObj) {
				chartObj = echarts.init(this.$refs.renderEle)
			}
		},
		data() {
			return {
				chart: null,
			}
		},

		methods: {
			/**
				* 重新更新
				*/
			update() {
				const stats = this.calcStats()
				const options = this.getBarBaseOptions()
				const xAxisData = []
				const allSeries = []
				for (rootIntent in this.intentGroups) {
					const group = this.intentGroups[rootIntent]
					const seriesData = []
					group.forEach(subIntent => {
						seriesData.push({
							name: subIntent,
							value: parseInt(stats[subIntent].duration),
							itemStyle: {
								color: this.colorMap[subIntent]
							}
						})
					})
					xAxisData.push(rootIntent)
					allSeries.push({
						name: rootIntent,
						data: seriesData,
						type: 'bar'
					})
				}
				options.xAxis.data = xAxisData
				options.series = allSeries
				chartObj.setOption(options)
			},

			/**
			 * 统计意图数据
			 */
			calcStats() {
				const stats = {}
				// 计算出现次数
				this.asr.forEach(element => {
					if (!element.intent) {
						return
					}
					// 没有则创建
					if (typeof stats[element.intent] === 'undefined') {
						stats[element.intent] = {
							'count': 0,
							'duration': 0
						}
					}
					// 统计
					stats[element.intent].count++
					stats[element.intent].duration += (element.end - element.start)
				})
				return stats
			},
			/**
			 * 获取柱状图类型配置
			 */
			getBarBaseOptions() {
				return {
					xAxis: {
						type: 'category',
						// axisLabel: { interval: 0, rotate: 30 },
						data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
					},
					yAxis: {
						type: 'value'
					},
					tooltip: {
						trigger: 'item'
					},
					grid: {
						left: '0%',
						right: '0%',
						bottom: '0%',
						containLabel: true
					},
					// legend: {
					// 	top: '1%',
					// 	left: 'center'
					// },
					series: [
						{
							name: 'Access From',
							data: [
								120,
								{
									value: 200,
									itemStyle: {
										color: '#505372'
									}
								},
								150,
								80,
								70,
								110,
								130
							],
							type: 'bar'
						},
					]
				}
			}
		},
	}

}