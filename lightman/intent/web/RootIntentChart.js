/**
 * char对象
 * 不能放进vue.data内，导致鼠标放大图像消失
 */

function RootIntentChart() {
	let chartObj = null
	/**
	 * 所有意图占比统计图
	 * 全部意图都会列出来，不包含父意图
	 */
	return {
		name: "RootIntentChart",
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
		template: document.querySelector("#rootIntentChartTemplate").innerHTML,
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
				const seriesData = []
				for (rootIntent in this.intentGroups) {
					const group = this.intentGroups[rootIntent]
					let val = 0
					group.forEach(subIntent => {
						val += stats[subIntent].duration
					})
					seriesData.push({
						name: rootIntent,
						value: parseInt(val),
						itemStyle: {
							color: this.colorMap[rootIntent]
						}
					})
				}
				options.series[0].data = seriesData
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
					tooltip: {
						trigger: 'item'
					},
					// legend: {
					// 	bottom: '1%',
					// 	left: 'center'
					// },
					grid: {
						top: '20%',
						left: '0%',
						right: '0%',
						bottom: '0%',
					},
					series: [
						{
							type: 'pie',
							avoidLabelOverlap: false,
							radius: ['30%', '50%'],
							label: {
								show: true,
								// position: 'center'
							},
							data: [
								{ value: 1048, name: 'Search Engine' },
								{ value: 735, name: 'Direct' },
								{ value: 580, name: 'Email' },
								{ value: 484, name: 'Union Ads' },
								{ value: 300, name: 'Video Ads' }
							],
							labelLine: {
								show: true
							},
							emphasis: {
								itemStyle: {
									shadowBlur: 10,
									shadowOffsetX: 0,
									shadowColor: 'rgba(0, 0, 0, 0.5)'
								}
							}
						}
					]
				}
			}
		},
	}

}