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
import { LineChart, BarChart, PieChart } from 'echarts/charts';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

export type ChartWidgetType = 'line' | 'bar' | 'pie';

export interface ChartSeries {
  name: string;
  data: (number | { name: string; value: number })[];
  color?: string;
  /** When dualAxis is true, bind series to the secondary Y axis. */
  yAxisIndex?: 0 | 1;
}

@Component({
  selector: 'app-chart-widget',
  standalone: true,
  template: `
    <section class="chart-widget vm-animate-chart">
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
      this.resizeObserver = new ResizeObserver(() => this.chart?.resize());
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
    if (type === 'pie') {
      const data = this.series()[0]?.data ?? [];
      return !data.length;
    }
    return !this.labels().length || !this.series().some((s) => (s.data as number[]).length);
  }

  private ensureChart(): void {
    const el = this.host()?.nativeElement;
    if (!el || this.chart) return;
    this.chart = echarts.init(el, undefined, { renderer: 'canvas' });
  }

  private render(): void {
    if (!this.chart) return;
    if (this.isEmpty()) {
      this.chart.clear();
      return;
    }
    this.chart.setOption(this.buildOption(), { notMerge: true });
    requestAnimationFrame(() => this.chart?.resize());
  }

  private buildOption(): EChartsOption {
    const type = this.type();
    const labels = this.labels();
    const seriesInput = this.series();
    const palette = ['#1ed896', '#38bdf8', '#a855f7', '#fbbf24', '#f472b6'];
    const animDuration = 450;

    if (type === 'pie') {
      const first = seriesInput[0];
      return {
        backgroundColor: 'transparent',
        animationDuration: animDuration,
        animationEasing: 'cubicOut',
        tooltip: { trigger: 'item' },
        legend: { bottom: 0, textStyle: { color: 'rgba(255,255,255,0.55)' } },
        series: [
          {
            type: 'pie',
            radius: ['42%', '68%'],
            center: ['50%', '46%'],
            itemStyle: { borderRadius: 6, borderColor: '#121212', borderWidth: 2 },
            label: { color: 'rgba(255,255,255,0.75)' },
            animationType: 'scale',
            animationEasing: 'elasticOut',
            data: (first?.data ?? []) as { name: string; value: number }[],
          },
        ],
        color: palette,
      };
    }

    const useDual = this.dualAxis() && type === 'line' && seriesInput.length >= 2;
    const echartsSeries = seriesInput.map((s, i) => {
      const seriesType = type as 'line' | 'bar';
      return {
        name: s.name,
        type: seriesType,
        smooth: type === 'line',
        symbol: type === 'line' ? 'circle' : undefined,
        symbolSize: 6,
        yAxisIndex: useDual ? (s.yAxisIndex ?? i) : 0,
        barMaxWidth: 36,
        itemStyle: { color: s.color ?? palette[i % palette.length] },
        areaStyle:
          type === 'line' && (s.yAxisIndex ?? i) === 0
            ? {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(30,216,150,0.22)' },
                  { offset: 1, color: 'rgba(30,216,150,0)' },
                ]),
              }
            : undefined,
        data: s.data as number[],
        animationDuration: animDuration,
        animationEasing: 'cubicOut' as const,
      };
    });

    const yAxis: EChartsOption['yAxis'] = useDual
      ? [
          {
            type: 'value',
            name: seriesInput[0]?.name,
            nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
            axisLabel: { color: 'rgba(255,255,255,0.45)' },
          },
          {
            type: 'value',
            name: seriesInput[1]?.name,
            nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
            splitLine: { show: false },
            axisLabel: { color: 'rgba(255,255,255,0.45)' },
          },
        ]
      : {
          type: 'value',
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: 'rgba(255,255,255,0.45)' },
        };

    return {
      backgroundColor: 'transparent',
      animationDuration: animDuration,
      animationEasing: 'cubicOut',
      grid: { left: 48, right: useDual ? 48 : 16, top: 36, bottom: 28 },
      tooltip: { trigger: 'axis' },
      legend: { top: 0, textStyle: { color: 'rgba(255,255,255,0.55)' } },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
        axisLabel: { color: 'rgba(255,255,255,0.45)' },
      },
      yAxis,
      series: echartsSeries as EChartsOption['series'],
      color: palette,
    };
  }
}
