const TimelineVisualizer = {
	name: "TimelineVisualizer",
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
	template: document.querySelector("#timelineVisualizerTemplate").innerHTML,
	watch: {
		// 监听分组变化
		intentGroups() {
			this.update()
		}
	},
	data() {
		return {
			// intent的状态对象
			stateMap: {},
			// 多条时间线
			timelines: [],
			// 显示文字
			isShowText: true,
			// 时间分割
			splitSecond: 60,
			// 时间分割选项
			splitSecondOpts: [
				{ value: 30, label: "30秒" },
				{ value: 60, label: "1分钟" },
				{ value: 60 * 2, label: "2分钟" },
				{ value: 60 * 5, label: "5分钟" },
				{ value: 60 * 10, label: "10分钟" },
			],
		}
	},
	methods: {
		update() {
			// 重置状态
			for (rootIntent in this.intentGroups) {
				// 根类的
				this.stateMap[rootIntent] = {
					isOnlyShowRoot: false,
				}
				// 子类的
				this.intentGroups[rootIntent].forEach(subIntent => {
					this.stateMap[subIntent] = {
						isDisabled: false,
					}
				})
			}
			// 重新渲染
			this.render()
		},
		selOrClearRootOnlyShow(isShow) {
			for (rootIntent in this.intentGroups) {
				// 根类的
				this.stateMap[rootIntent].isOnlyShowRoot = isShow
			}
		},
		selOrClearSub(isSel) {
			for (rootIntent in this.intentGroups) {
				// 根类的
				// this.stateMap[rootIntent].isOnlyShowRoot = true
				// 子类的
				this.intentGroups[rootIntent].forEach(subIntent => {
					this.stateMap[subIntent].isDisabled = isSel ? false : true
				})
			}
		},
		/**
		 *  根据一个子意图查找父
		 */
		findRootIntent(subIntent) {
			for (rootIntent in this.intentGroups) {
				if (this.intentGroups[rootIntent].includes(subIntent)) {
					return rootIntent
				}
			}
			return null
		},
		/**
		 * 获取一个时间轴上block的颜色
		 */
		getBlockColor(block) { 
			// 查找父意图，如果开启独显则使用父
			if (this.stateMap[block.rootIntent].isOnlyShowRoot) { 
				return this.colorMap[block.rootIntent]
			}
			// 自己颜色
			return this.colorMap[block.intent]
		},
		/**
		 * 渲染时间轴
		 */
		render() {
			const asrGroups = this.splitIntoGroups(this.splitSecond)
			this.timelines = []
			// 找到展示时长最大的分组
			let maxGroupDuration = 0
			asrGroups.forEach((group) => {
				const n = group[group.length - 1].end - group[0].start
				if (n > maxGroupDuration) maxGroupDuration = n
			})
			// 循环遍历
			asrGroups.forEach((group, groupIndex) => { 
				const groupStart = group[0].start
				const groupEnd = group[group.length - 1].end
				// 创建时间轴
				const timeline = {
					// 时间范围
					'timeRange': `${parseInt(groupStart)}-${parseInt(groupEnd)}`,
					// 轴上的每个区块
					'blocks': []
				}
				// 遍历每一个asr句子
				group.forEach((asrItem) => {
					// 过滤为空
					if (!asrItem.intent) { 
						return
					}
					// 计算区块在组内的相对位置和宽度
					const relativeStart = asrItem.start - groupStart
					const blockWidth = ((asrItem.end - asrItem.start) / maxGroupDuration) * 100
					const blockLeft = (relativeStart / maxGroupDuration) * 100
					// 获取父意图

					// 加入区块
					const duration = parseInt(asrItem.end - asrItem.start)
					const rootIntent = this.findRootIntent(asrItem.intent)
					timeline.blocks.push({
						"intent": asrItem.intent,
						"rootIntent": rootIntent,
						"title": `${asrItem.intent}(${rootIntent}) \n${duration}s (${parseInt(asrItem.start)}s-${parseInt(asrItem.end)}s) \n${asrItem.text}`,
						"left": blockLeft,
						"width": blockWidth,
						"color": this.colorMap[asrItem.intent],
					})
				})

				this.timelines.push(timeline)
			})
		},
		/**
		 * 切换子类
		 */
		toggleSubIntent(subIntent) {
			this.stateMap[subIntent].isDisabled = !this.stateMap[subIntent].isDisabled
		},
		/**
		 * 切换根类的仅显示
		 */
		toggleRootIntentOnlyShow(rootIntent) {
			this.stateMap[rootIntent].isOnlyShowRoot = !this.stateMap[rootIntent].isOnlyShowRoot
		},
		/**
		 * 查询意图状态
		 */
		getState(intent, stateKey) { 
			console.log(intent, stateKey, this.stateMap[intent])
			if (!this.stateMap[intent]) {
				return null
			}
			return this.stateMap[intent][stateKey]
		},
		/**
		 * 按照指定秒数分割数据
		 */
		splitIntoGroups(splitSeconds) {
			const asrGroups = []
			let currentGroup = []
			let groupEndThreshold = null

			this.asr.forEach((item, index) => {
				if (currentGroup.length === 0) {
					// 开始新的一组
					currentGroup.push(item)
					groupEndThreshold =
						Math.floor(item.end / splitSeconds) * splitSeconds + splitSeconds
				} else if (item.end <= groupEndThreshold) {
					// 当前元素属于当前组
					currentGroup.push(item)
				} else {
					// 当前元素属于下一组，保存当前组并开始新组
					asrGroups.push([...currentGroup])
					currentGroup = [item]
					groupEndThreshold =
						Math.floor(item.end / splitSeconds) * splitSeconds + splitSeconds
				}

				// 处理最后一个元素
				if (index === this.asr.length - 1 && currentGroup.length > 0) {
					asrGroups.push([...currentGroup])
				}
			})
			return asrGroups
		}
	}
}