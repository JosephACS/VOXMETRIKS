import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  effect,
  input,
  viewChild,
} from '@angular/core';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, TreemapChart } from 'echarts/charts';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  MarkPointComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  TreemapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkPointComponent,
  CanvasRenderer,
]);

export type ChartWidgetType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'hbar'
  | 'stacked-bar'
  | 'combo'
  | 'treemap'
  | 'percent-line';

export interface ChartSeries {
  name: string;
  data: (number | { name: string; value: number })[];
  color?: string;
  /** When dualAxis is true, bind series to the secondary Y axis. */
  yAxisIndex?: 0 | 1;
  /** combo: force series type */
  type?: 'line' | 'bar';
}

@Component({
  selector: 'app-chart-widget',
  standalone: true,
  template: `
    <section
      class="chart-widget vm-animate-chart"
      [class.chart-widget--flat]="flat()"
      [attr.data-chart-type]="type()"
    >
      @if (title()) {
        <header class="chart-widget__header">
          <h3>{{ title() }}</h3>
          @if (subtitle()) {
            <span>{{ subtitle() }}</span>
          }
        </header>
      }
      <div class="chart-widget__body" [style.height.px]="height()">
        <div #host class="chart-widget__canvas"></div>
        @if (isEmpty()) {
          <div class="chart-widget__empty-overlay">
            <span>Sin datos para el periodo seleccionado</span>
          </div>
        }
      </div>
    </section>
  `,
  styleUrl: './chart-widget.component.scss',
})
export class ChartWidgetComponent implements AfterViewInit, OnDestroy {
  readonly type = input<ChartWidgetType>('line');
  readonly title = input<string | null>(null);
  readonly subtitle = input<string | null>(null);
  readonly labels = input<string[]>([]);
  readonly series = input<ChartSeries[]>([]);
  readonly height = input(280);
  readonly dualAxis = input(false);
  /** Flatten glass chrome for embedded report surfaces. */
  readonly flat = input(false);
  /** Highlight peak point on temporal line charts. */
  readonly highlightPeak = input(false);
  /** Y-axis as percentage (0–100). */
  readonly percentAxis = input(false);

  private readonly host = viewChild<ElementRef<HTMLDivElement>>('host');
  private chart: echarts.ECharts | null = null;
  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    afterNextRender(() => {
      this.ensureChart();
      this.render();
    });
    effect(() => {
      this.labels();
      this.series();
      this.type();
      this.dualAxis();
      this.highlightPeak();
      this.percentAxis();
      this.isEmpty();
      this.ensureChart();
      this.render();
    });
  }

  ngAfterViewInit(): void {
    this.ensureChart();
    this.render();
    const el = this.host()?.nativeElement;
    if (el) {
      this.resizeObserver = new ResizeObserver(() => {
        if (!this.chart) {
          this.ensureChart();
          this.render();
          return;
        }
        this.chart.resize();
      });
      this.resizeObserver.observe(el);
    }
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.chart?.dispose();
    this.chart = null;
  }

  isEmpty(): boolean {
    const type = this.type();
    if (type === 'pie' || type === 'treemap') {
      const data = this.series()[0]?.data ?? [];
      return !data.length;
    }
    return !this.labels().length || !this.series().some((s) => (s.data as number[]).length);
  }

  private ensureAttempts = 0;

  private ensureChart(): void {
    const el = this.host()?.nativeElement;
    if (!el || this.chart) return;
    // Avoid zero-size init (white canvas on mobile flex layouts).
    if (el.clientWidth < 8 || el.clientHeight < 8) {
      this.ensureAttempts += 1;
      if (this.ensureAttempts < 60) {
        requestAnimationFrame(() => this.ensureChart());
      }
      return;
    }
    this.ensureAttempts = 0;
    this.chart = echarts.init(el, undefined, { renderer: 'canvas' });
  }

  private render(): void {
    if (!this.chart) {
      this.ensureChart();
      if (!this.chart) return;
    }
    if (this.isEmpty()) {
      this.chart.clear();
      const bg = this.chartSurfaceColor();
      const isLight =
        typeof document !== 'undefined' &&
        document.documentElement.getAttribute('data-theme') === 'light';
      this.chart.setOption({
        backgroundColor: bg,
        title: {
          text: 'Sin datos para el periodo seleccionado',
          left: 'center',
          top: 'middle',
          textStyle: {
            color: isLight ? 'rgba(18,25,22,0.48)' : 'rgba(231,237,234,0.45)',
            fontSize: 13,
            fontWeight: 400,
          },
        },
      });
      return;
    }
    this.chart.setOption(this.buildOption(), { notMerge: true });
    requestAnimationFrame(() => this.chart?.resize());
  }

  private chartSurfaceColor(): string {
    if (typeof document === 'undefined') return '#0C1110';
    const v = getComputedStyle(document.documentElement).getPropertyValue('--vx-surface').trim();
    return v || '#0C1110';
  }

  private buildOption(): EChartsOption {
    const type = this.type();
    const labels = this.labels();
    const seriesInput = this.series();
    const palette = ['#e8a33d', '#f0b555', '#f0b555', '#5F72C9', '#B8B3C2', '#7A849D', '#4B5268', '#9BCBFF'];
    const animDuration = 450;
    const darkBg = this.chartSurfaceColor();
    const isLight =
      typeof document !== 'undefined' &&
      document.documentElement.getAttribute('data-theme') === 'light';
    const axisMuted = isLight ? 'rgba(18,25,22,0.48)' : 'rgba(231,237,234,0.45)';
    const axisLabel = isLight ? 'rgba(18,25,22,0.64)' : 'rgba(231,237,234,0.58)';
    const split = isLight ? 'rgba(18,28,24,0.1)' : 'rgba(214,228,220,0.07)';
    const tipBg = isLight ? 'rgba(242,245,243,0.96)' : 'rgba(28,38,34,0.94)';
    const tipFg = isLight ? '#121916' : '#E7EDEA';
    const tipBorder = isLight ? 'rgba(18,28,24,0.12)' : 'rgba(214,228,220,0.1)';
    const labelFg = isLight ? 'rgba(18,25,22,0.78)' : 'rgba(231,237,234,0.75)';

    if (type === 'pie') {
      const first = seriesInput[0];
      return {
        backgroundColor: darkBg,
        animationDuration: animDuration,
        animationEasing: 'cubicOut',
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { show: false },
        series: [
          {
            type: 'pie',
            radius: ['42%', '68%'],
            center: ['50%', '50%'],
            itemStyle: { borderRadius: 6, borderColor: darkBg, borderWidth: 2 },
            label: { color: labelFg, formatter: '{b}' },
            animationType: 'scale',
            animationEasing: 'elasticOut',
            data: (first?.data ?? []) as { name: string; value: number }[],
          },
        ],
        color: [...palette],
      };
    }

    if (type === 'treemap') {
      const first = seriesInput[0];
      const raw = (first?.data ?? []) as { name: string; value: number }[];
      const data = raw.map((d, i) => ({
        ...d,
        itemStyle: { color: palette[i % palette.length] },
      }));
      return {
        backgroundColor: darkBg,
        animationDuration: animDuration,
        tooltip: { formatter: '{b}: {c}' },
        series: [
          {
            type: 'treemap',
            roam: false,
            nodeClick: false,
            breadcrumb: { show: false },
            label: { show: true, color: '#e8e8e8', fontSize: 12 },
            upperLabel: { show: false },
            itemStyle: { borderColor: darkBg, borderWidth: 2, gapWidth: 2 },
            levels: [{ itemStyle: { borderWidth: 0 } }],
            data,
          },
        ],
        color: [...palette],
      };
    }

    const horizontal =
      type === 'hbar' || (type === 'stacked-bar' && labels.length <= 2 && seriesInput.length >= 2);
    const stacked = type === 'stacked-bar';
    const combo = type === 'combo';
    const percent = type === 'percent-line' || this.percentAxis();
    const seriesTypeDefault: 'line' | 'bar' =
      type === 'line' || type === 'percent-line' ? 'line' : 'bar';
    const useDual = (this.dualAxis() || combo) && seriesInput.length >= 2;
    const stackAsPercent = stacked && horizontal;

    const echartsSeries = seriesInput.map((s, i) => {
      const st: 'line' | 'bar' = combo
        ? (s.type ?? (i === 0 ? 'bar' : 'line'))
        : seriesTypeDefault;
      const isAreaLine = st === 'line' && (type === 'line' || type === 'percent-line') && !combo;
      const values = (s.data as number[]) || [];
      let markPoint: Record<string, unknown> | undefined;
      if (this.highlightPeak() && st === 'line' && i === 0 && values.length) {
        let peakIdx = 0;
        for (let j = 1; j < values.length; j++) {
          if ((values[j] ?? 0) > (values[peakIdx] ?? 0)) peakIdx = j;
        }
        markPoint = {
          symbol: 'circle',
          symbolSize: 10,
          itemStyle: { color: darkBg, borderColor: '#e8a33d', borderWidth: 2 },
          label: { show: false },
          data: [{ coord: [peakIdx, values[peakIdx]], name: 'Pico' }],
        };
      }
      return {
        name: s.name,
        type: st,
        stack: stacked ? 'total' : undefined,
        smooth: st === 'line',
        symbol: st === 'line' ? 'circle' : undefined,
        symbolSize: st === 'line' ? 5 : undefined,
        yAxisIndex: useDual ? (s.yAxisIndex ?? i) : 0,
        barMaxWidth: horizontal ? 22 : 36,
        itemStyle: { color: s.color ?? palette[i % palette.length] },
        areaStyle:
          isAreaLine && (s.yAxisIndex ?? i) === 0
            ? {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(232, 163, 61,0.22)' },
                  { offset: 1, color: 'rgba(232, 163, 61,0)' },
                ]),
              }
            : undefined,
        data: values,
        markPoint,
        animationDuration: animDuration,
        animationEasing: 'cubicOut' as const,
      };
    });

    const valueAxisSingle = {
      type: 'value' as const,
      min: percent || stackAsPercent ? 0 : undefined,
      max: percent || stackAsPercent ? 100 : undefined,
      axisLabel: {
        color: axisMuted,
        formatter: percent || stackAsPercent ? '{value}%' : undefined,
      },
      splitLine: { lineStyle: { color: split } },
    };

    const valueAxis = useDual
      ? [
          {
            type: 'value' as const,
            name: seriesInput[0]?.name,
            nameTextStyle: { color: axisMuted, fontSize: 10 },
            splitLine: { lineStyle: { color: split } },
            axisLabel: { color: axisMuted },
          },
          {
            type: 'value' as const,
            name: seriesInput[1]?.name,
            nameTextStyle: { color: axisMuted, fontSize: 10 },
            splitLine: { show: false },
            axisLabel: { color: axisMuted },
          },
        ]
      : valueAxisSingle;

    const categoryAxis = {
      type: 'category' as const,
      data: labels,
      axisLine: { lineStyle: { color: split } },
      axisLabel: {
        color: axisLabel,
        fontSize: horizontal ? 11 : 10,
        interval: (labels.length > 14 ? 'auto' : 0) as 0 | 'auto',
        width: horizontal ? 88 : undefined,
        overflow: horizontal ? ('truncate' as const) : undefined,
        hideOverlap: true,
      },
    };

    const option: EChartsOption = {
      backgroundColor: darkBg,
      animationDuration: animDuration,
      animationEasing: 'cubicOut',
      grid: {
        left: horizontal ? 108 : 48,
        right: useDual ? 56 : 16,
        top: 36,
        bottom: horizontal ? 28 : 36,
        containLabel: !horizontal,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: tipBg,
        borderColor: tipBorder,
        textStyle: { color: tipFg, fontSize: 12 },
        extraCssText: 'border-radius:8px;padding:8px 10px;',
        valueFormatter: percent
          ? (v) => `${Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 })} %`
          : undefined,
      },
      legend: { top: 0, textStyle: { color: axisLabel } },
      xAxis: (horizontal ? valueAxis : categoryAxis) as EChartsOption['xAxis'],
      yAxis: (horizontal ? categoryAxis : valueAxis) as EChartsOption['yAxis'],
      series: echartsSeries as EChartsOption['series'],
      color: palette,
    };
    return option;
  }
}
