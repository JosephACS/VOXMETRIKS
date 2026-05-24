import { Pipe, PipeTransform } from '@angular/core';

/**
 * Duration Pipe
 * 
 * Convierte milisegundos a formato legible mm:ss o mm:ss.sss
 * 
 * Uso:
 * {{ 180000 | duration }}          // "3:00"
 * {{ 65432 | duration:'short' }}   // "1:05"
 * {{ 65432 | duration:'long' }}    // "1:05.432"
 */
@Pipe({
  name: 'duration',
  standalone: true,
})
export class DurationPipe implements PipeTransform {
  /**
   * Transforma milisegundos a formato tiempo
   * 
   * @param value Milisegundos (number)
   * @param format 'short' (mm:ss) | 'long' (mm:ss.sss) | default 'short'
   * @returns String formateado
   */
  transform(
    value: number | null | undefined,
    format: 'short' | 'long' = 'short'
  ): string {
    if (value === null || value === undefined || value < 0) {
      return '0:00';
    }

    // Convertir a segundos
    const totalSeconds = Math.floor(value / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    // Formato corto: mm:ss
    if (format === 'short') {
      return `${minutes}:${this.pad(seconds)}`;
    }

    // Formato largo: mm:ss.sss (milisegundos)
    const milliseconds = value % 1000;
    return `${minutes}:${this.pad(seconds)}.${this.padMs(milliseconds)}`;
  }

  /**
   * Pad números menores a 10 con un 0 adelante
   * @private
   */
  private pad(num: number): string {
    return num < 10 ? `0${num}` : `${num}`;
  }

  /**
   * Pad milisegundos (3 dígitos)
   * @private
   */
  private padMs(num: number): string {
    if (num < 10) return `00${num}`;
    if (num < 100) return `0${num}`;
    return `${num}`;
  }
}
