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
				const chartData = {
					xAxisData: [],
					areaStyles: [],
					seriesData: [],
				}

				const options = this.getBarBaseOptions()
				for (rootIntent in this.intentGroups) {
					const group = this.intentGroups[rootIntent]
					group.forEach(subIntent => {
						// 序列值
						chartData.seriesData.push({
							name: subIntent,
							value: parseInt(stats[subIntent].duration),
							itemStyle: {
								color: this.colorMap[subIntent]
							}
						})
						// x轴的key，与序列对应
						chartData.xAxisData.push(subIntent)
						// 填充色，取字父亲
						const rootColor = this.hexToEchartsGradient(this.colorMap[rootIntent], 0.3)
						chartData.areaStyles.push(rootColor)
					})
				}

				options.xAxis[0].data = chartData.xAxisData
				options.xAxis[0].splitArea.areaStyle.color = chartData.areaStyles
				options.series[0].data = chartData.seriesData

				// chartObj.setOption(this.getBarBaseOptions())
				chartObj.setOption(options)

			},

			/**
			 * 生成一个echart的颜色渐变
			 * 从上到下，透明度的
			 */
			hexToEchartsGradient(hex, topAlpha) {
				// 移除 # 号
				hex = hex.replace('#', '');

				// 处理 3 位和 6 位的十六进制颜色
				if (hex.length === 3) {
					hex = hex.split('').map(char => char + char).join('');
				}

				// 解析 RGB 值
				const r = parseInt(hex.substring(0, 2), 16);
				const g = parseInt(hex.substring(2, 4), 16);
				const b = parseInt(hex.substring(4, 6), 16);

				// 返回 ECharts 渐变对象
				return {
					type: 'linear',
					x: 0,
					y: 0,
					x2: 0,
					y2: 1,  // 从上到下
					colorStops: [
						{
							offset: 0,
							color: `rgba(${r}, ${g}, ${b}, ${topAlpha})` // 顶部颜色
						},
						{
							offset: 0.6,
							color: `rgba(${r}, ${g}, ${b}, 0)` // 底部透明
						}
					]
				};
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
			getBarBaseOptions() {
				return {
					tooltip: {
						trigger: 'axis',
						axisPointer: {            // 坐标轴指示器，坐标轴触发有效
							type: 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
						},
						formatter: (params) => {
							// params 是一个数组，包含当前悬浮点的所有系列数据
							let result = params[0].axisValueLabel + '<br/>'; // 显示 x 轴标签

							// 从initentGroup中查找父意图
							let findRootIntent = null
							for (rootIntent in this.intentGroups) {
								const group = this.intentGroups[rootIntent]
								if (group.includes(params[0].name)) {
									findRootIntent = rootIntent;
								}
							}

							const rootColor = this.colorMap[findRootIntent]

							// 增加自定义值
							params.push({
								'marker': params[0].marker.replace(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g, rootColor),
								'seriesName': '所属根',
								'value': findRootIntent
							})

							// 遍历所有系列，显示原有的 tooltip 内容
							params.forEach(item => {
								result += `${item.marker} ${item.seriesName}: ${item.value}<br/>`;
							});


							return result;
						}
					},
					grid: {
						top: '8%',
						left: '0%',
						right: '0%',
						bottom: '0%',
						containLabel: true
					},
					xAxis: [
						{
							type: 'category',
							axisLabel: { interval: 0, rotate: 30 },
							data: [
								'淡白', '淡红', '红', '暗', '尖红', '边尖红'],
							splitArea: {
								show: true,
								areaStyle: {
									color: [
										'rgba(255,0,0,0.5)', 'rgba(255,0,0,0.5)', 'rgba(0,232,0,0.5)', 'rgba(0,232,0,0.5)', 'rgba(204,232,207,0.8)', 'rgba(204,232,207,0.8)'
									]
								}
							}
						}
					],
					yAxis: [{
						type: 'value'
					}],
					series: [
						{
							name: '时长',
							type: 'bar',
							data: [10, 52, 20, 34, 30, 30,],
							itemStyle: {
							},
							label: {
								normal: {
									show: true,
								}
							}
						}
					]
				}
			}
		},
	}

}