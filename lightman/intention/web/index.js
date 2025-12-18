;(function () {
  let currData = null
  const getTVMountEle = () =>
    document.querySelector("#timelineVisualizer .renderBody")
  const getPCMountEle = () =>
    document.querySelector("#proportionChart .chartBody")

  /**
   * 设置新的数据
   * 重新渲染
   */
  window.setData = function (data) {
    // currData = mockData(data)
    // 移除无intention的
    currData = []
    data.forEach((element) => {
      if (element.intention) {
        currData.push(element)
      }
    })
    // 颜色映射
    colorMapper.generateIntentionColors(data)
    // 占比图表
    new ProportionChart(getPCMountEle(), currData).render()
    // 时间轴可视化
    TVReGroup(60 * 2)
  }

  /**
   * 时间轴可视化 重新分组
   */
  window.TVReGroup = function (seconds) {
    new TimelineVisualizer(getTVMountEle(), currData).start(seconds) // 按60秒分割
  }

  /**
   * mock数据
   */
  function mockData(data) {
    data.forEach((element) => {
      element.intention = "意图" + Math.ceil(Math.random() * 100)
    })
    return data
    return [
      { id: "001", start: 0, end: 60, intention: "意图1", text: "文本1" },
      {
        id: "002",
        start: 70,
        end: 120,
        intention: "意图2",
        text: "文本23",
      },
      {
        id: "003",
        start: 500,
        end: 1000,
        intention: "意图3",
        text: "文本3",
      },
      {
        id: "004",
        start: 1000,
        end: 2000,
        intention: "意图4",
        text: "文本4",
      },
    ]
  }
})()

/**
 * 颜色映射
 */
const colorMapper = {
  intentionColors: new Map(),
  // 为不同的intention生成视觉差异大的颜色
  generateIntentionColors: function (data) {
    const intentions = [...new Set(data.map((item) => item.intention))]
    // 使用HSL颜色模型，在色相环上均匀分布颜色
    const hueStep = 360 / intentions.length

    intentions.forEach((intention, index) => {
      // 生成高饱和度、中亮度的颜色，确保良好的视觉对比
      const hue = (hueStep * index) % 360
      // 使用不同的饱和度和亮度组合增加视觉差异
      const saturation = 70 + Math.floor(Math.random() * 20) // 70-90%
      const lightness = 40 + Math.floor(Math.random() * 20) // 40-60%
      const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`
      this.intentionColors.set(intention, color)
    })
  },
  getColor: function (intention) {
    return colorMapper.intentionColors.get(intention) || "#cccccc"
  },
}

/**
 * 数据时间轴可视化
 */
class TimelineVisualizer {
  constructor(renderEle, data) {
    this.renderEle = renderEle
    this.eles = {}
    this.data = data
    this.intentionColors = new Map()
    this.groups = []
    this.isShowText = true
    // 对外暴露接口
    window.TVSwitchTextShow = this.switchTextShow.bind(this)
  }

  // 转换文字显示状态
  switchTextShow() {
    this.isShowText = !this.isShowText
    const className = "hiddenText"
    if (this.isShowText) {
      this.renderEle.classList.remove(className)
    } else {
      this.renderEle.classList.add(className)
    }
  }

  // 按照指定秒数分割数据
  splitIntoGroups(splitSeconds) {
    this.groups = []
    let currentGroup = []
    let groupEndThreshold = null

    this.data.forEach((item, index) => {
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
        this.groups.push([...currentGroup])
        currentGroup = [item]
        groupEndThreshold =
          Math.floor(item.end / splitSeconds) * splitSeconds + splitSeconds
      }

      // 处理最后一个元素
      if (index === this.data.length - 1 && currentGroup.length > 0) {
        this.groups.push([...currentGroup])
      }
    })

    return this.groups
  }

  // 启动函数
  start(splitSeconds) {
    // 清空容器
    this.renderEle.innerHTML = ""

    // 分割数据
    const groups = this.splitIntoGroups(splitSeconds)

    // 找到展示时长最大的分组
    let maxGroupDuration = 0
    groups.forEach((group) => {
      const n = group[group.length - 1].end - group[0].start
      if (n > maxGroupDuration) maxGroupDuration = n
    })

    // 绘制每个组
    groups.forEach((group, groupIndex) => {
      if (group.length === 0) return

      const groupStart = group[0].start
      const groupEnd = group[group.length - 1].end
      const groupDuration = groupEnd - groupStart

      // 创建组容器
      const groupContainer = (this.eles.groupContainer =
        document.createElement("div"))
      groupContainer.className = "timeline-group"
      groupContainer.style.cssText = `
        display: flex;
        align-items: center;
        margin-bottom: 5px;
      `

      // 左侧时间范围显示
      const timeRange = (this.eles.timeRange = document.createElement("div"))
      timeRange.className = "time-range"
      timeRange.textContent = `${parseInt(groupStart)}-${parseInt(groupEnd)}`
      timeRange.style.cssText = `
        min-width: 80px;
        font-family: monospace;
        font-weight: bold;
        color: #333;
        margin-right: 5px;
      `

      // 右侧区块容器
      const blocksContainer = (this.eles.blocksContainer =
        document.createElement("div"))
      blocksContainer.className = "blocks-container"
      blocksContainer.style.cssText = `
        flex: 1;
        position: relative;
        height: 20px;
      `

      // 绘制区块
      group.forEach((item) => {
        const block = document.createElement("div")
        block.className = "timeline-block"
        block.textContent = item.intention

        // 计算区块在组内的相对位置和宽度
        const relativeStart = item.start - groupStart
        const blockWidth = ((item.end - item.start) / maxGroupDuration) * 100
        const blockLeft = (relativeStart / maxGroupDuration) * 100

        block.style.cssText = `
          position: absolute;
          height: 100%;
          width: ${blockWidth}%;
          left: ${blockLeft}%;
          background-color: ${colorMapper.getColor(item.intention)};
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          overflow: hidden;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        `

        // 添加悬停效果
        block.addEventListener("mouseenter", () => {
          block.style.transform = "scale(1.05)"
          block.style.opacity = "0.9"
          block.title = [
            item.intention,
            item.text,
            parseFloat(item.end - item.start).toFixed(2) +
              "s" +
              ` ${item.start} - ${item.end}`,
          ].join("\r")
        })

        block.addEventListener("mouseleave", () => {
          block.style.transform = "scale(1)"
          block.style.opacity = "1"
        })

        blocksContainer.appendChild(block)
      })

      // 组装容器
      groupContainer.appendChild(timeRange)
      groupContainer.appendChild(blocksContainer)
      this.renderEle.appendChild(groupContainer)
    })

    // 添加图例
    this.addLegend()
  }

  // 添加图例
  addLegend() {
    const legendContainer = document.createElement("div")
    legendContainer.className = "legend"
    legendContainer.style.cssText = `
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
      padding: 15px;
      background: #f0f0f0;
      border-radius: 4px;
    `

    const legendTitle = document.createElement("div")
    legendTitle.textContent = "意图分类图例:"
    legendTitle.style.cssText = `
      width: 100%;
      font-weight: bold;
      margin-bottom: 10px;
      color: #333;
    `
    legendContainer.appendChild(legendTitle)

    this.intentionColors.forEach((color, intention) => {
      const legendItem = document.createElement("div")
      legendItem.style.cssText = `
        display: flex;
        align-items: center;
        margin-right: 15px;
      `

      const colorBox = document.createElement("div")
      colorBox.style.cssText = `
        width: 20px;
        height: 20px;
        background-color: ${color};
        margin-right: 8px;
        border-radius: 3px;
        border: 1px solid #ddd;
      `

      const label = document.createElement("span")
      label.textContent = intention
      label.style.cssText = `
        font-size: 12px;
        color: #333;
      `

      legendItem.appendChild(colorBox)
      legendItem.appendChild(label)
      legendContainer.appendChild(legendItem)
    })

    this.renderEle.appendChild(legendContainer)
  }

  // 获取分组信息（可用于调试）
  getGroupsInfo() {
    return this.groups.map((group, index) => ({
      groupIndex: index,
      timeRange: `${group[0].start}-${group[group.length - 1].end}`,
      elements: group.length,
      intentions: [...new Set(group.map((item) => item.intention))],
    }))
  }
}

/**
 * 占比统计图表
 * 展现每个意图出现的总时长，对于总共的占比
 */
class ProportionChart {
  constructor(renderEle, data) {
    this.data = data
    this.renderEle = renderEle
  }
  getOptions() {
    return {
      series: [
        {
          type: "treemap",
          data: [
            {
              name: "ALL",
              value: 10,
              children: [
                {
                  name: "test1",
                  value: 4,
                  itemStyle: {
                    color: "#aaaaaa",
                  },
                },
                {
                  name: "test2",
                  value: 6,
                  itemStyle: {
                    color: "#dddddd",
                  },
                },
              ],
            },
          ],
        },
      ],
    }
  }
  render() {
    this.renderEle.innerHTML = ""
    const options = this.getOptions()
    const proportion = this.getIntentionProportion()
    const totalDuration = this.data.reduce(
      (acc, item) => acc + item.end - item.start,
      0
    )
    options.series[0].data[0].children = proportion.map((item) => ({
      name: [
        item.intention,
        ((item.duration / totalDuration) * 100).toFixed(0) + "%",
        parseFloat(item.duration).toFixed(0) + "s",
      ].join(" "),
      value: item.duration,
      itemStyle: {
        color: colorMapper.getColor(item.intention),
      },
    }))
    const myChart = echarts.init(this.renderEle)
    myChart.setOption(options)
  }
  /**
   * 计算意图占比
   */
  getIntentionProportion() {
    const intentions = [...new Set(this.data.map((item) => item.intention))]
    const result = intentions.map((intention) => {
      const duration = this.data
        .filter((item) => item.intention === intention)
        .reduce((acc, item) => acc + item.end - item.start, 0)
      return { intention, duration }
    })
    return result
  }
}
